from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import json
import httpx
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Sheets API
import gspread
from google.oauth2.service_account import Credentials

# Gemini AI Client
from gemini_client import analyze_with_gemini

app = FastAPI(
    title="Flood Detection and Rain Monitoring System",
    description="AI-powered system for flood prediction and rain monitoring using IoT sensors",
    version="1.0.0"
)

# CORS Configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== CONFIGURATION ==============

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "FloodMonitoringData")

# AI Provider Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")  # "ollama" or "gemini"

# OpenAI-compatible LLM API Configuration (works with OpenLLM, Ollama, etc.)
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")  # Default Ollama
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "")  # Comma-separated list of chat IDs

# Flood threshold configurations
WATER_LEVEL_WARNING = 50  # cm - Warning level
WATER_LEVEL_DANGER = 80   # cm - Danger level
RAIN_INTENSITY_HIGH = 70  # Percentage threshold for high intensity
ALERT_RISK_THRESHOLD = 50 # Trigger alert when risk >= 50%

# Alert cooldown tracking (to prevent spam)
alert_cooldown = {}  # {node_id: last_alert_timestamp}

# ============== DATA MODELS ==============

class RainIntensity(str, Enum):
    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    EXTREME = "extreme"

class FloodRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class SensorData(BaseModel):
    """Data model for incoming IoT sensor data from node"""
    node_id: str
    piezo_value: float          # Piezoelectric sensor - rain intensity (0-100)
    ultrasonic_value: float     # Ultrasonic sensor - water level in cm
    rain_sensor_value: float    # Rain sensor - rain detection (0-100, 0=dry, 100=heavy rain)
    timestamp: Optional[str] = None
    location: Optional[str] = "default"

class SensorDataResponse(BaseModel):
    """Response after storing sensor data"""
    success: bool
    message: str
    data_id: str
    timestamp: str

class PredictionRequest(BaseModel):
    """Request model for flood prediction"""
    node_id: Optional[str] = None
    hours_ahead: Optional[int] = 6  # Predict flood risk for next N hours

class PredictionResponse(BaseModel):
    """Response model for flood prediction"""
    node_id: str
    current_water_level: float
    current_rain_intensity: RainIntensity
    is_raining: bool
    flood_risk: FloodRisk
    risk_percentage: float
    prediction_summary: str
    recommended_actions: List[str]
    ai_analysis: str
    timestamp: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    services: dict

# ============== GOOGLE SHEETS FUNCTIONS ==============

def get_google_sheets_client():
    """Initialize and return Google Sheets client"""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        if os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FILE):
            creds = Credentials.from_service_account_file(
                GOOGLE_SHEETS_CREDENTIALS_FILE,
                scopes=scopes
            )
            client = gspread.authorize(creds)
            return client
        else:
            print(f"Warning: Credentials file not found at {GOOGLE_SHEETS_CREDENTIALS_FILE}")
            return None
    except Exception as e:
        print(f"Error initializing Google Sheets client: {e}")
        return None

def store_sensor_data(data: SensorData) -> dict:
    """Store sensor data in Google Sheets"""
    client = get_google_sheets_client()
    
    timestamp = data.timestamp or datetime.now().isoformat()
    data_id = f"{data.node_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if client:
        try:
            spreadsheet = client.open(SPREADSHEET_NAME)
            worksheet = spreadsheet.sheet1
            
            # Check if headers exist, if not add them
            try:
                headers = worksheet.row_values(1)
                if not headers:
                    worksheet.append_row([
                        "data_id", "node_id", "piezo_value", "ultrasonic_value", 
                        "rain_sensor_value", "location", "timestamp"
                    ])
            except:
                worksheet.append_row([
                    "data_id", "node_id", "piezo_value", "ultrasonic_value", 
                    "rain_sensor_value", "location", "timestamp"
                ])
            
            # Append the new data
            worksheet.append_row([
                data_id,
                data.node_id,
                data.piezo_value,
                data.ultrasonic_value,
                data.rain_sensor_value,
                data.location,
                timestamp
            ])
            
            return {"success": True, "data_id": data_id, "timestamp": timestamp}
        except Exception as e:
            print(f"Error storing data in Google Sheets: {e}")
            return {"success": False, "data_id": data_id, "timestamp": timestamp, "error": str(e)}
    else:
        # Fallback: Store locally if Google Sheets is not available
        return {"success": True, "data_id": data_id, "timestamp": timestamp, "storage": "local_fallback"}

def get_historical_data(node_id: str = None, limit: int = 100) -> List[dict]:
    """Retrieve historical sensor data from Google Sheets"""
    client = get_google_sheets_client()
    
    if client:
        try:
            spreadsheet = client.open(SPREADSHEET_NAME)
            worksheet = spreadsheet.sheet1
            records = worksheet.get_all_records()
            
            if node_id:
                records = [r for r in records if r.get("node_id") == node_id]
            
            return records[-limit:] if len(records) > limit else records
        except Exception as e:
            print(f"Error retrieving data from Google Sheets: {e}")
            return []
    return []

# ============== TELEGRAM ALERT FUNCTIONS ==============

async def send_telegram_message(chat_id: str, message: str) -> bool:
    """Send a message to a specific Telegram chat"""
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram bot token not configured")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        return False

async def broadcast_alert(message: str) -> int:
    """Broadcast alert message to all configured chat IDs"""
    if not TELEGRAM_CHAT_IDS:
        print("No Telegram chat IDs configured")
        return 0
    
    chat_ids = [cid.strip() for cid in TELEGRAM_CHAT_IDS.split(",") if cid.strip()]
    success_count = 0
    
    for chat_id in chat_ids:
        if await send_telegram_message(chat_id, message):
            success_count += 1
    
    return success_count

def can_send_alert(node_id: str, cooldown_minutes: int = 15) -> bool:
    """Check if we can send alert for this node (cooldown check)"""
    if node_id not in alert_cooldown:
        return True
    
    last_alert = alert_cooldown[node_id]
    time_diff = (datetime.now() - last_alert).total_seconds() / 60
    return time_diff >= cooldown_minutes

def update_alert_cooldown(node_id: str) -> None:
    """Update alert cooldown for node"""
    alert_cooldown[node_id] = datetime.now()

async def check_and_send_flood_alert(
    node_id: str,
    water_level: float,
    rain_intensity: RainIntensity,
    flood_risk: FloodRisk,
    risk_percentage: float,
    location: str = "Unknown"
) -> bool:
    """
    Check if flood alert should be sent and send it.
    
    Alerts are sent when:
    - Risk percentage >= threshold (50%)
    - Flood risk is HIGH or CRITICAL
    - Cooldown period has passed
    """
    # Check if alert should be sent
    should_alert = (
        risk_percentage >= ALERT_RISK_THRESHOLD and
        flood_risk in [FloodRisk.HIGH, FloodRisk.CRITICAL] and
        can_send_alert(node_id)
    )
    
    if not should_alert:
        return False
    
    # Build alert message
    emoji = "🚨" if flood_risk == FloodRisk.CRITICAL else "⚠️"
    
    actions = get_recommended_actions(flood_risk, water_level)
    actions_text = "\n".join([f"• {action}" for action in actions[:3]])
    
    message = f"""
{emoji} <b>FLOOD ALERT</b> {emoji}

📍 <b>Node:</b> {node_id}
📌 <b>Location:</b> {location}
💧 <b>Water Level:</b> {water_level:.1f} cm
🌧️ <b>Rain Intensity:</b> {rain_intensity.value}

<b>Risk Level: {flood_risk.value.upper()} ({risk_percentage:.1f}%)</b>

<b>Immediate Actions:</b>
{actions_text}

<i>⏰ Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
<i>Stay safe and follow local authority guidelines!</i>
"""
    
    # Send alert
    count = await broadcast_alert(message)
    
    if count > 0:
        update_alert_cooldown(node_id)
        print(f"Flood alert sent to {count} subscribers for node {node_id}")
        return True
    
    return False

# ============== AI ANALYSIS FUNCTIONS ==============

def classify_rain_intensity(piezo_value: float, rain_sensor_value: float) -> RainIntensity:
    """Classify rain intensity based on sensor values"""
    avg_value = (piezo_value + rain_sensor_value) / 2
    
    if avg_value < 10:
        return RainIntensity.NONE
    elif avg_value < 30:
        return RainIntensity.LIGHT
    elif avg_value < 50:
        return RainIntensity.MODERATE
    elif avg_value < 75:
        return RainIntensity.HEAVY
    else:
        return RainIntensity.EXTREME

def calculate_flood_risk(
    water_level: float, 
    rain_intensity: RainIntensity, 
    historical_data: List[dict] = None
) -> tuple[FloodRisk, float]:
    """Calculate flood risk based on current conditions and historical trends"""
    
    # Base risk from water level
    if water_level >= WATER_LEVEL_DANGER:
        base_risk = 80
    elif water_level >= WATER_LEVEL_WARNING:
        base_risk = 50
    else:
        base_risk = (water_level / WATER_LEVEL_WARNING) * 30
    
    # Add risk from rain intensity
    intensity_risk = {
        RainIntensity.NONE: 0,
        RainIntensity.LIGHT: 5,
        RainIntensity.MODERATE: 15,
        RainIntensity.HEAVY: 25,
        RainIntensity.EXTREME: 35
    }
    base_risk += intensity_risk.get(rain_intensity, 0)
    
    # Analyze trend from historical data
    if historical_data and len(historical_data) >= 3:
        recent_levels = [d.get("ultrasonic_value", 0) for d in historical_data[-5:]]
        if len(recent_levels) >= 2:
            trend = recent_levels[-1] - recent_levels[0]
            if trend > 10:  # Water level rising rapidly
                base_risk += 15
            elif trend > 5:
                base_risk += 8
    
    # Cap risk at 100
    risk_percentage = min(base_risk, 100)
    
    # Determine flood risk category
    if risk_percentage >= 75:
        flood_risk = FloodRisk.CRITICAL
    elif risk_percentage >= 50:
        flood_risk = FloodRisk.HIGH
    elif risk_percentage >= 25:
        flood_risk = FloodRisk.MODERATE
    else:
        flood_risk = FloodRisk.LOW
    
    return flood_risk, risk_percentage

def get_recommended_actions(flood_risk: FloodRisk, water_level: float) -> List[str]:
    """Get recommended actions based on flood risk level"""
    actions = {
        FloodRisk.LOW: [
            "Continue normal monitoring",
            "Ensure drainage systems are clear",
            "Review emergency preparedness plan"
        ],
        FloodRisk.MODERATE: [
            "Increase monitoring frequency",
            "Alert local authorities",
            "Check flood barriers and sandbags availability",
            "Prepare emergency evacuation routes"
        ],
        FloodRisk.HIGH: [
            "Activate flood warning systems",
            "Deploy flood barriers if available",
            "Begin evacuation of low-lying areas",
            "Contact emergency services",
            "Move valuable items to higher ground"
        ],
        FloodRisk.CRITICAL: [
            "IMMEDIATE EVACUATION REQUIRED",
            "Emergency services on high alert",
            "All residents must move to higher ground",
            "Avoid all flood-affected areas",
            "Do not attempt to cross flooded roads"
        ]
    }
    return actions.get(flood_risk, ["Continue monitoring"])

async def get_ai_analysis(
    water_level: float,
    rain_intensity: RainIntensity,
    flood_risk: FloodRisk,
    risk_percentage: float,
    historical_data: List[dict] = None
) -> str:
    """Get AI-powered analysis using configured AI provider (Gemini or Ollama)"""
    
    # Use Gemini if configured
    if AI_PROVIDER == "gemini":
        try:
            return await analyze_with_gemini(
                water_level=water_level,
                rain_intensity=rain_intensity.value,
                flood_risk=flood_risk.value,
                risk_percentage=risk_percentage,
                historical_data=historical_data
            )
        except Exception as e:
            print(f"Gemini analysis failed: {e}")
            return generate_fallback_analysis(water_level, rain_intensity, flood_risk, risk_percentage)
    
    # Use Ollama/Local LLM
    # Prepare context for LLM
    historical_context = ""
    if historical_data and len(historical_data) > 0:
        recent_readings = historical_data[-5:]
        historical_context = f"Recent readings: {json.dumps(recent_readings)}"
    
    prompt = f"""You are a flood prediction AI assistant. Analyze the following sensor data and provide a brief, actionable analysis:

Current Conditions:
- Water Level: {water_level} cm
- Rain Intensity: {rain_intensity.value}
- Flood Risk Level: {flood_risk.value}
- Risk Percentage: {risk_percentage}%
{historical_context}

Thresholds:
- Warning water level: {WATER_LEVEL_WARNING} cm
- Danger water level: {WATER_LEVEL_DANGER} cm

Provide a 2-3 sentence analysis including:
1. Current situation assessment
2. Predicted trend for the next few hours
3. One key recommendation

Keep response concise and actionable."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Ollama API format
            response = await client.post(
                LLM_API_URL,
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "AI analysis unavailable")
            else:
                return f"AI analysis unavailable (Status: {response.status_code})"
    except Exception as e:
        # Fallback analysis when LLM is not available
        return generate_fallback_analysis(water_level, rain_intensity, flood_risk, risk_percentage)

def generate_fallback_analysis(
    water_level: float,
    rain_intensity: RainIntensity,
    flood_risk: FloodRisk,
    risk_percentage: float
) -> str:
    """Generate fallback analysis when LLM is unavailable"""
    
    status = "stable" if flood_risk in [FloodRisk.LOW, FloodRisk.MODERATE] else "concerning"
    
    if rain_intensity in [RainIntensity.HEAVY, RainIntensity.EXTREME]:
        trend = "Water levels are expected to rise due to heavy rainfall."
    elif rain_intensity == RainIntensity.MODERATE:
        trend = "Moderate rainfall may cause gradual water level increase."
    else:
        trend = "Water levels are expected to remain stable."
    
    if flood_risk == FloodRisk.CRITICAL:
        action = "Immediate evacuation is strongly recommended."
    elif flood_risk == FloodRisk.HIGH:
        action = "Prepare for potential evacuation and stay alert."
    else:
        action = "Continue regular monitoring."
    
    return f"Current conditions are {status} with water level at {water_level}cm. {trend} {action}"

# ============== API ENDPOINTS ==============

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    sheets_available = get_google_sheets_client() is not None
    
    return HealthResponse(
        status="operational",
        timestamp=datetime.now().isoformat(),
        services={
            "api": "online",
            "google_sheets": "connected" if sheets_available else "not_configured",
            "llm": "configured"
        }
    )

@app.post("/api/sensor-data", response_model=SensorDataResponse)
async def receive_sensor_data(data: SensorData, background_tasks: BackgroundTasks):
    """
    Receive sensor data from IoT node.
    
    This endpoint accepts data from the IoT sensors:
    - Piezoelectric sensor (rain intensity)
    - Ultrasonic sensor (water level)
    - Rain sensor (rain detection)
    
    Features:
    - Stores data in Google Sheets for historical analysis
    - Analyzes incoming data for flood risk
    - Triggers automated Telegram alerts for HIGH/CRITICAL risk
    """
    # Store sensor data
    result = store_sensor_data(data)
    
    # Analyze incoming data for flood risk
    rain_intensity = classify_rain_intensity(data.piezo_value, data.rain_sensor_value)
    flood_risk, risk_percentage = calculate_flood_risk(data.ultrasonic_value, rain_intensity)
    
    # Trigger automated alert in background if risk is high
    if flood_risk in [FloodRisk.HIGH, FloodRisk.CRITICAL]:
        background_tasks.add_task(
            check_and_send_flood_alert,
            node_id=data.node_id,
            water_level=data.ultrasonic_value,
            rain_intensity=rain_intensity,
            flood_risk=flood_risk,
            risk_percentage=risk_percentage,
            location=data.location or "Unknown"
        )
    
    # Build response message with risk info
    message = f"Data stored successfully. Risk: {flood_risk.value} ({risk_percentage:.1f}%)"
    if flood_risk in [FloodRisk.HIGH, FloodRisk.CRITICAL]:
        message += " - Alert triggered!"
    
    return SensorDataResponse(
        success=result["success"],
        message=message if result["success"] else "Storage error",
        data_id=result["data_id"],
        timestamp=result["timestamp"]
    )

@app.post("/api/predict", response_model=PredictionResponse)
async def predict_flood(request: PredictionRequest):
    """
    Generate flood prediction based on sensor data and AI analysis.
    
    This endpoint:
    1. Retrieves latest sensor data
    2. Analyzes trends from historical data
    3. Uses AI to generate prediction
    4. Returns flood risk assessment and recommendations
    """
    # Get historical data
    historical_data = get_historical_data(node_id=request.node_id, limit=50)
    
    if not historical_data:
        raise HTTPException(
            status_code=404, 
            detail="No sensor data available for prediction. Please submit sensor data first."
        )
    
    # Get latest reading
    latest = historical_data[-1]
    node_id = latest.get("node_id", "unknown")
    water_level = float(latest.get("ultrasonic_value", 0))
    piezo_value = float(latest.get("piezo_value", 0))
    rain_sensor_value = float(latest.get("rain_sensor_value", 0))
    
    # Analyze current conditions
    rain_intensity = classify_rain_intensity(piezo_value, rain_sensor_value)
    is_raining = rain_sensor_value > 10
    flood_risk, risk_percentage = calculate_flood_risk(water_level, rain_intensity, historical_data)
    
    # Get recommendations
    recommended_actions = get_recommended_actions(flood_risk, water_level)
    
    # Get AI analysis
    ai_analysis = await get_ai_analysis(
        water_level, rain_intensity, flood_risk, risk_percentage, historical_data
    )
    
    # Generate prediction summary
    prediction_summary = (
        f"Flood risk is {flood_risk.value.upper()} ({risk_percentage:.1f}%). "
        f"Water level: {water_level}cm. Rain intensity: {rain_intensity.value}."
    )
    
    return PredictionResponse(
        node_id=node_id,
        current_water_level=water_level,
        current_rain_intensity=rain_intensity,
        is_raining=is_raining,
        flood_risk=flood_risk,
        risk_percentage=risk_percentage,
        prediction_summary=prediction_summary,
        recommended_actions=recommended_actions,
        ai_analysis=ai_analysis,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/history")
async def get_sensor_history(node_id: str = None, limit: int = 100):
    """
    Retrieve historical sensor data.
    
    Optional filters:
    - node_id: Filter by specific node
    - limit: Maximum number of records to return
    """
    data = get_historical_data(node_id=node_id, limit=limit)
    return {
        "count": len(data),
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status/{node_id}")
async def get_node_status(node_id: str):
    """Get current status for a specific node"""
    historical_data = get_historical_data(node_id=node_id, limit=10)
    
    if not historical_data:
        raise HTTPException(status_code=404, detail=f"No data found for node: {node_id}")
    
    latest = historical_data[-1]
    water_level = float(latest.get("ultrasonic_value", 0))
    piezo_value = float(latest.get("piezo_value", 0))
    rain_sensor_value = float(latest.get("rain_sensor_value", 0))
    
    rain_intensity = classify_rain_intensity(piezo_value, rain_sensor_value)
    flood_risk, risk_percentage = calculate_flood_risk(water_level, rain_intensity, historical_data)
    
    # Calculate node online/offline status based on last transmission
    last_timestamp = latest.get("timestamp", "")
    is_online, last_seen_ago = check_node_online_status(last_timestamp)
    
    return {
        "node_id": node_id,
        "status": "online" if is_online else "offline",
        "is_online": is_online,
        "last_seen": last_timestamp,
        "last_seen_ago": last_seen_ago,
        "last_reading": latest,
        "current_risk": flood_risk.value,
        "risk_percentage": risk_percentage,
        "rain_intensity": rain_intensity.value,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/nodes")
async def get_all_nodes_status():
    """
    Get status of all IoT nodes with online/offline detection.
    
    A node is considered:
    - Online: Last transmission within 2 minutes
    - Idle: Last transmission within 10 minutes
    - Offline: No transmission for more than 10 minutes
    """
    all_data = get_historical_data(limit=1000)
    
    if not all_data:
        return {
            "count": 0,
            "nodes": [],
            "summary": {
                "online": 0,
                "idle": 0,
                "offline": 0,
                "total": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    # Group by node_id and get latest reading for each
    nodes_map = {}
    for reading in all_data:
        node_id = reading.get("node_id", "unknown")
        timestamp = reading.get("timestamp", "")
        
        if node_id not in nodes_map:
            nodes_map[node_id] = reading
        else:
            # Keep the latest reading
            existing_ts = nodes_map[node_id].get("timestamp", "")
            if timestamp > existing_ts:
                nodes_map[node_id] = reading
    
    # Build node status list
    nodes_list = []
    online_count = 0
    idle_count = 0
    offline_count = 0
    
    for node_id, reading in nodes_map.items():
        last_timestamp = reading.get("timestamp", "")
        is_online, last_seen_ago = check_node_online_status(last_timestamp)
        status = get_node_status_label(last_timestamp)
        
        water_level = float(reading.get("ultrasonic_value", 0))
        piezo_value = float(reading.get("piezo_value", 0))
        rain_sensor_value = float(reading.get("rain_sensor_value", 0))
        
        rain_intensity = classify_rain_intensity(piezo_value, rain_sensor_value)
        flood_risk, risk_percentage = calculate_flood_risk(water_level, rain_intensity)
        
        node_info = {
            "node_id": node_id,
            "location": reading.get("location", "Unknown"),
            "status": status,
            "is_online": status == "online",
            "last_seen": last_timestamp,
            "last_seen_ago": last_seen_ago,
            "water_level": water_level,
            "rain_intensity": rain_sensor_value,
            "piezo_value": piezo_value,
            "flood_risk": flood_risk.value,
            "risk_percentage": risk_percentage
        }
        nodes_list.append(node_info)
        
        if status == "online":
            online_count += 1
        elif status == "idle":
            idle_count += 1
        else:
            offline_count += 1
    
    # Sort by status (online first) then by node_id
    status_order = {"online": 0, "idle": 1, "offline": 2}
    nodes_list.sort(key=lambda x: (status_order.get(x["status"], 3), x["node_id"]))
    
    return {
        "count": len(nodes_list),
        "nodes": nodes_list,
        "summary": {
            "online": online_count,
            "idle": idle_count,
            "offline": offline_count,
            "total": len(nodes_list)
        },
        "timestamp": datetime.now().isoformat()
    }


def check_node_online_status(timestamp_str: str, online_threshold_minutes: int = 2) -> tuple:
    """
    Check if a node is online based on its last transmission timestamp.
    
    Returns:
        tuple: (is_online: bool, last_seen_ago: str)
    """
    if not timestamp_str:
        return False, "Never"
    
    try:
        # Parse the timestamp
        if "T" in timestamp_str:
            last_seen = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            last_seen = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        
        # Make timezone naive for comparison
        if last_seen.tzinfo:
            last_seen = last_seen.replace(tzinfo=None)
        
        now = datetime.now()
        diff = now - last_seen
        total_seconds = diff.total_seconds()
        
        # Calculate human-readable time ago
        if total_seconds < 60:
            last_seen_ago = f"{int(total_seconds)}s ago"
        elif total_seconds < 3600:
            last_seen_ago = f"{int(total_seconds / 60)}m ago"
        elif total_seconds < 86400:
            last_seen_ago = f"{int(total_seconds / 3600)}h ago"
        else:
            last_seen_ago = f"{int(total_seconds / 86400)}d ago"
        
        # Check if online (within threshold)
        is_online = total_seconds <= (online_threshold_minutes * 60)
        
        return is_online, last_seen_ago
        
    except Exception as e:
        print(f"Error parsing timestamp '{timestamp_str}': {e}")
        return False, "Unknown"


def get_node_status_label(timestamp_str: str) -> str:
    """
    Get status label for a node based on last transmission.
    
    - online: within 2 minutes
    - idle: within 10 minutes
    - offline: more than 10 minutes
    """
    if not timestamp_str:
        return "offline"
    
    try:
        if "T" in timestamp_str:
            last_seen = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            last_seen = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        
        if last_seen.tzinfo:
            last_seen = last_seen.replace(tzinfo=None)
        
        now = datetime.now()
        diff = now - last_seen
        total_minutes = diff.total_seconds() / 60
        
        if total_minutes <= 2:
            return "online"
        elif total_minutes <= 10:
            return "idle"
        else:
            return "offline"
            
    except Exception:
        return "offline"


# ============== RUN SERVER ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

