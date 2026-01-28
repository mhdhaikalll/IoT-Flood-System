"""
Flood Monitoring System - Hybrid Edition
Combines real-time IoT sensor data with historical Google Sheets analysis
"""

# ============== IMPORTS ==============
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import json
import httpx
import asyncio
from enum import Enum
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Google Sheets API
import gspread
from google.oauth2.service_account import Credentials

# Gemini AI Client (with fallback)
try:
    from gemini_client import analyze_with_gemini
    GEMINI_AVAILABLE = True
except ImportError:
    print("[WARNING] gemini_client module not found. Using mathematical fallback.")
    GEMINI_AVAILABLE = False
    
    async def analyze_with_gemini(**kwargs):
        """Fallback when Gemini is unavailable"""
        water_level = kwargs.get('water_level', 0)
        rain_intensity = kwargs.get('rain_intensity', 'none')
        flood_risk = kwargs.get('flood_risk', 'low')
        risk_percentage = kwargs.get('risk_percentage', 0)
        
        return f"""
⚠️ **FALLBACK ANALYSIS** ⚠️

**Current Status:**
- Water Level: {water_level:.1f} cm
- Rain Intensity: {rain_intensity}
- Flood Risk: {flood_risk.upper()} ({risk_percentage:.1f}%)

**Analysis:**
Using mathematical calculations only. Gemini AI is currently unavailable.

**Recommendation:**
{get_fallback_recommendation(flood_risk, water_level)}
"""

# ============== CONFIGURATION ==============

class Config:
    """System configuration"""
    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")
    SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "FloodMonitoringData")
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")
    
    # Flood thresholds
    WATER_LEVEL_WARNING = 50  # cm
    WATER_LEVEL_DANGER = 80   # cm
    ALERT_RISK_THRESHOLD = 50  # %
    
    # Node status
    NODE_ONLINE_MINUTES = 2
    NODE_IDLE_MINUTES = 10
    NODE_OFFLINE_MINUTES = 30
    
    # Analysis
    HISTORICAL_DAYS_TO_ANALYZE = 3
    MIN_DATA_POINTS_FOR_ANALYSIS = 5
    ANALYSIS_INTERVAL_MINUTES = 30
    
    # Alerts
    ALERT_COOLDOWN_MINUTES = 15
    HISTORICAL_ALERT_COOLDOWN_MINUTES = 30

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

class NodeStatus(str, Enum):
    ONLINE = "online"
    IDLE = "idle"
    OFFLINE = "offline"

class SensorData(BaseModel):
    """Incoming data from ESP32/IoT sensor"""
    node_id: str
    piezo_value: float          # Rain intensity sensor (0-100)
    ultrasonic_value: float     # Water level in cm
    rain_sensor_value: float    # Rain detection (0-100)
    timestamp: Optional[str] = None
    location: Optional[str] = "Unknown"

class SensorDataResponse(BaseModel):
    """Response after storing sensor data"""
    success: bool
    message: str
    data_id: str
    timestamp: str
    risk_level: str
    risk_percentage: float
    alert_triggered: bool

class PredictionRequest(BaseModel):
    """Request for flood prediction"""
    node_id: Optional[str] = None
    hours_ahead: Optional[int] = 6

class PredictionResponse(BaseModel):
    """Flood prediction response"""
    node_id: str
    current_water_level: float
    current_rain_intensity: RainIntensity
    is_raining: bool
    flood_risk: FloodRisk
    risk_percentage: float
    prediction_summary: str
    recommended_actions: List[str]
    ai_analysis: str
    ai_provider: str  # "gemini" or "fallback"
    timestamp: str

class HealthResponse(BaseModel):
    """System health response"""
    status: str
    timestamp: str
    services: dict
    data_statistics: dict
    system_info: dict

# ============== CORE SERVICE CLASSES ==============

class GoogleSheetsService:
    """Handles all Google Sheets operations"""
    
    def __init__(self):
        self.client = None
        self.connect()
    
    def connect(self):
        """Connect to Google Sheets with original scopes"""
        try:
            if os.path.exists(Config.GOOGLE_SHEETS_CREDENTIALS):
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                
                creds = Credentials.from_service_account_file(
                    Config.GOOGLE_SHEETS_CREDENTIALS,
                    scopes=scopes
                )
                self.client = gspread.authorize(creds)
                print("[GOOGLE SHEETS] Connected successfully")
                return True
            else:
                print(f"[GOOGLE SHEETS] Credentials file not found: {Config.GOOGLE_SHEETS_CREDENTIALS}")
                return False
        except Exception as e:
            print(f"[GOOGLE SHEETS] Connection error: {e}")
            return False
    
    def store_sensor_data(self, data: SensorData) -> dict:
        """Store sensor data in Google Sheets"""
        if not self.client:
            return {"success": False, "error": "Google Sheets not connected"}
        
        try:
            spreadsheet = self.client.open(Config.SPREADSHEET_NAME)
            worksheet = spreadsheet.sheet1
            
            # Ensure headers exist
            headers = worksheet.row_values(1)
            if not headers:
                worksheet.append_row([
                    "data_id", "node_id", "piezo_value", "ultrasonic_value",
                    "rain_sensor_value", "location", "timestamp"
                ])
            
            # Generate data ID and timestamp
            timestamp = data.timestamp or datetime.now().isoformat()
            data_id = f"{data.node_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Append data
            worksheet.append_row([
                data_id, data.node_id, data.piezo_value, data.ultrasonic_value,
                data.rain_sensor_value, data.location or "Unknown", timestamp
            ])
            
            return {"success": True, "data_id": data_id, "timestamp": timestamp}
            
        except Exception as e:
            print(f"[GOOGLE SHEETS] Store error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_historical_data(self, node_id: str = None, limit: int = 1000, 
                           days_back: int = None) -> List[Dict[str, Any]]:
        """Retrieve historical sensor data"""
        if not self.client:
            return []
        
        try:
            spreadsheet = self.client.open(Config.SPREADSHEET_NAME)
            worksheet = spreadsheet.sheet1
            records = worksheet.get_all_records()
            
            if not records:
                return []
            
            # Filter by node if specified
            if node_id:
                records = [r for r in records if r.get('node_id') == node_id]
            
            # Filter by date if specified
            if days_back:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                filtered = []
                for record in records:
                    try:
                        ts_str = record.get('timestamp', '')
                        if not ts_str:
                            continue
                        record_time = self._parse_timestamp(ts_str)
                        if record_time >= cutoff_date:
                            filtered.append(record)
                    except:
                        continue
                records = filtered
            
            # Sort by timestamp (newest first)
            records.sort(key=lambda x: self._parse_timestamp(x.get('timestamp', '')), reverse=True)
            
            # Apply limit and clean data
            cleaned = []
            for record in records[:limit]:
                try:
                    cleaned.append({
                        'data_id': record.get('data_id', ''),
                        'node_id': record.get('node_id', 'unknown'),
                        'piezo_value': float(record.get('piezo_value', 0)),
                        'ultrasonic_value': float(record.get('ultrasonic_value', 0)),
                        'rain_sensor_value': float(record.get('rain_sensor_value', 0)),
                        'location': record.get('location', 'Unknown'),
                        'timestamp': record.get('timestamp', '')
                    })
                except (ValueError, KeyError):
                    continue
            
            return cleaned
            
        except Exception as e:
            print(f"[GOOGLE SHEETS] Read error: {e}")
            return []
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        data = self.get_historical_data(days_back=30, limit=1000)
        
        if not data:
            return {
                "total_records": 0,
                "nodes_found": 0,
                "nodes": [],
                "latest_timestamp": None
            }
        
        # Group by node
        nodes_data = {}
        for record in data:
            node_id = record['node_id']
            if node_id not in nodes_data:
                nodes_data[node_id] = []
            nodes_data[node_id].append(record)
        
        # Get date range
        timestamps = [self._parse_timestamp(r['timestamp']) for r in data if r['timestamp']]
        if timestamps:
            earliest = min(timestamps)
            latest = max(timestamps)
        else:
            earliest = latest = None
        
        # Get latest reading for each node
        latest_readings = {}
        for node_id, records in nodes_data.items():
            if records:
                latest_rec = max(records, key=lambda x: self._parse_timestamp(x['timestamp']))
                latest_readings[node_id] = {
                    "timestamp": latest_rec['timestamp'],
                    "water_level": latest_rec['ultrasonic_value'],
                    "location": latest_rec['location'],
                    "data_points": len(records)
                }
        
        return {
            "total_records": len(data),
            "nodes_found": len(nodes_data),
            "nodes": list(nodes_data.keys()),
            "date_range": {
                "earliest": earliest.isoformat() if earliest else None,
                "latest": latest.isoformat() if latest else None,
                "days_covered": (latest - earliest).days if earliest and latest else 0
            },
            "latest_readings": latest_readings
        }
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime"""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except:
                continue
        
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return datetime.now()

class FloodAnalysisService:
    """Handles flood risk analysis and predictions"""
    
    def __init__(self):
        self.water_level_warning = Config.WATER_LEVEL_WARNING
        self.water_level_danger = Config.WATER_LEVEL_DANGER
    
    def classify_rain_intensity(self, piezo_value: float, rain_sensor_value: float) -> RainIntensity:
        """Classify rain intensity from sensor values"""
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
    
    def calculate_immediate_risk(self, water_level: float, 
                               rain_intensity: RainIntensity,
                               historical_data: List[Dict] = None) -> tuple[FloodRisk, float, str]:
        """Calculate immediate flood risk (mathematical only)"""
        
        # Base risk from water level
        if water_level >= self.water_level_danger:
            base_risk = 85
            water_status = "DANGER"
        elif water_level >= self.water_level_warning:
            base_risk = 60
            water_status = "WARNING"
        elif water_level > 30:
            base_risk = 40
            water_status = "ELEVATED"
        else:
            base_risk = 20
            water_status = "NORMAL"
        
        # Adjust for rain intensity
        intensity_multiplier = {
            RainIntensity.NONE: 1.0,
            RainIntensity.LIGHT: 1.1,
            RainIntensity.MODERATE: 1.3,
            RainIntensity.HEAVY: 1.7,
            RainIntensity.EXTREME: 2.0
        }
        base_risk *= intensity_multiplier.get(rain_intensity, 1.0)
        
        # Adjust for trend if historical data available
        if historical_data and len(historical_data) >= 3:
            recent_levels = [d.get('ultrasonic_value', 0) for d in historical_data[-5:]]
            if len(recent_levels) >= 2:
                trend = recent_levels[-1] - recent_levels[0]
                if trend > 15:  # Rapidly rising
                    base_risk *= 1.4
                    water_status += " (RISING RAPIDLY)"
                elif trend > 8:
                    base_risk *= 1.2
                    water_status += " (RISING)"
                elif trend < -5:
                    base_risk *= 0.8
                    water_status += " (RECEDING)"
        
        # Cap risk
        risk_percentage = min(base_risk, 100)
        
        # Determine risk category
        if risk_percentage >= 80:
            flood_risk = FloodRisk.CRITICAL
        elif risk_percentage >= 60:
            flood_risk = FloodRisk.HIGH
        elif risk_percentage >= 40:
            flood_risk = FloodRisk.MODERATE
        else:
            flood_risk = FloodRisk.LOW
        
        return flood_risk, risk_percentage, water_status
    
    def get_recommended_actions(self, flood_risk: FloodRisk, water_level: float) -> List[str]:
        """Get recommended actions based on risk level"""
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
    
    def analyze_historical_trend(self, water_levels: List[float]) -> Dict[str, Any]:
        """Analyze trend from historical water level data"""
        if len(water_levels) < 2:
            return {"direction": "insufficient_data", "strength": 0.0, "description": "Not enough data"}
        
        # Simple linear trend
        recent = water_levels[:min(10, len(water_levels))]
        if len(recent) >= 2:
            change = recent[0] - recent[-1]
            if change > 10:
                return {"direction": "rising_rapidly", "strength": 0.9, 
                       "description": "Water levels rising rapidly"}
            elif change > 3:
                return {"direction": "rising", "strength": 0.6,
                       "description": "Water levels rising gradually"}
            elif change < -10:
                return {"direction": "falling_rapidly", "strength": 0.9,
                       "description": "Water levels falling rapidly"}
            elif change < -3:
                return {"direction": "falling", "strength": 0.6,
                       "description": "Water levels falling gradually"}
        
        return {"direction": "stable", "strength": 0.1, 
               "description": "Water levels stable"}

class AlertService:
    """Handles Telegram alerts and notifications"""
    
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.channel_id = Config.TELEGRAM_CHANNEL_ID
        self.alert_cooldown = {}  # {node_id: last_alert_time}
    
    def is_configured(self) -> bool:
        """Check if Telegram is configured"""
        return bool(self.bot_token and self.channel_id)
    
    def can_send_alert(self, node_id: str, cooldown_minutes: int = 15) -> bool:
        """Check if alert can be sent (cooldown)"""
        if node_id not in self.alert_cooldown:
            return True
        
        last_alert = self.alert_cooldown[node_id]
        time_diff = (datetime.now() - last_alert).total_seconds() / 60
        return time_diff >= cooldown_minutes
    
    def update_cooldown(self, node_id: str):
        """Update alert cooldown"""
        self.alert_cooldown[node_id] = datetime.now()
    
    async def send_alert(self, node_id: str, water_level: float, 
                        rain_intensity: RainIntensity, flood_risk: FloodRisk,
                        risk_percentage: float, location: str = "Unknown",
                        alert_type: str = "real_time") -> bool:
        """Send alert to Telegram channel"""
        
        if not self.is_configured():
            print("[ALERT] Telegram not configured")
            return False
        
        # Check cooldown
        cooldown = Config.ALERT_COOLDOWN_MINUTES if alert_type == "real_time" else Config.HISTORICAL_ALERT_COOLDOWN_MINUTES
        if not self.can_send_alert(node_id, cooldown):
            print(f"[ALERT] Cooldown active for node {node_id}")
            return False
        
        # Build message
        if alert_type == "real_time":
            emoji = "🚨"
            alert_title = "REAL-TIME FLOOD ALERT"
            alert_source = "Live sensor data"
        else:
            emoji = "📊"
            alert_title = "PREDICTIVE FLOOD ALERT"
            alert_source = "Historical data analysis"
        
        # Determine urgency
        if flood_risk == FloodRisk.CRITICAL:
            urgency_emoji = "🚨🚨🚨"
        elif flood_risk == FloodRisk.HIGH:
            urgency_emoji = "🚨🚨"
        else:
            urgency_emoji = "⚠️"
        
        # Get recommended actions
        analysis_service = FloodAnalysisService()
        actions = analysis_service.get_recommended_actions(flood_risk, water_level)
        actions_text = "\n".join([f"• {action}" for action in actions[:3]])
        
        message = f"""
{urgency_emoji} <b>{alert_title}</b> {urgency_emoji}

{emoji} <b>Source:</b> {alert_source}
📍 <b>Node:</b> {node_id}
📌 <b>Location:</b> {location}

💧 <b>Water Level:</b> <b>{water_level:.1f} cm</b>
🌧️ <b>Rain Intensity:</b> {rain_intensity.value}

<b>Risk Level: {flood_risk.value.upper()} ({risk_percentage:.1f}%)</b>

<b>Recommended Actions:</b>
{actions_text}

<i>⏰ Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        
        # Send to Telegram
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                    json={
                        "chat_id": self.channel_id,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                )
                
                if response.status_code == 200:
                    self.update_cooldown(node_id)
                    print(f"[ALERT] {alert_type} alert sent for node {node_id}")
                    return True
                else:
                    print(f"[ALERT] Failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"[ALERT] Error: {e}")
            return False
    
    async def send_test_alert(self) -> bool:
        """Send a test alert"""
        if not self.is_configured():
            return False
        
        test_message = f"""
🤖 <b>TEST ALERT</b> 🤖

System: Flood Monitoring System
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a test message to verify Telegram integration.
If you receive this, the alert system is working correctly.
"""
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                    json={
                        "chat_id": self.channel_id,
                        "text": test_message,
                        "parse_mode": "HTML"
                    }
                )
                return response.status_code == 200
        except:
            return False

class AIAnalysisService:
    """Handles AI analysis with Gemini fallback"""
    
    def __init__(self):
        self.gemini_available = GEMINI_AVAILABLE
    
    async def analyze(self, water_level: float, rain_intensity: RainIntensity,
                     flood_risk: FloodRisk, risk_percentage: float,
                     historical_data: List[Dict] = None) -> tuple[str, str]:
        """Get analysis from Gemini or fallback"""
        
        if self.gemini_available:
            try:
                ai_analysis = await analyze_with_gemini(
                    water_level=water_level,
                    rain_intensity=rain_intensity.value,
                    flood_risk=flood_risk.value,
                    risk_percentage=risk_percentage,
                    historical_data=historical_data
                )
                return ai_analysis, "gemini"
            except Exception as e:
                print(f"[AI] Gemini analysis failed: {e}")
                # Fall through to mathematical analysis
        
        # Fallback mathematical analysis
        return self._generate_fallback_analysis(
            water_level, rain_intensity, flood_risk, risk_percentage, historical_data
        ), "fallback"
    
    def _generate_fallback_analysis(self, water_level: float, rain_intensity: RainIntensity,
                                   flood_risk: FloodRisk, risk_percentage: float,
                                   historical_data: List[Dict] = None) -> str:
        """Generate mathematical analysis fallback"""
        
        # Calculate statistics if historical data available
        stats = ""
        if historical_data and len(historical_data) >= 5:
            water_levels = [d.get('ultrasonic_value', 0) for d in historical_data]
            avg_water = sum(water_levels) / len(water_levels)
            max_water = max(water_levels)
            stats = f"\nHistorical Context:\n- Average: {avg_water:.1f} cm\n- Maximum: {max_water:.1f} cm"
        
        analysis = f"""
📊 **MATHEMATICAL ANALYSIS**

**Current Conditions:**
- Water Level: {water_level:.1f} cm
- Rain Intensity: {rain_intensity.value}
- Flood Risk: {flood_risk.value.upper()} ({risk_percentage:.1f}%)
{stats}

**Risk Assessment:**
Based on mathematical calculations, the current conditions indicate {flood_risk.value} flood risk.

**Note:** Gemini AI analysis is currently unavailable. This analysis uses mathematical models only.
"""
        return analysis

class NodeStatusService:
    """Manages node online/offline status"""
    
    def __init__(self):
        self.online_nodes = {}  # {node_id: last_seen}
    
    def update_node_status(self, node_id: str):
        """Update node as online"""
        self.online_nodes[node_id] = datetime.now()
    
    def get_node_status(self, last_timestamp: str) -> tuple[NodeStatus, str]:
        """Get node status based on last timestamp"""
        if not last_timestamp:
            return NodeStatus.OFFLINE, "Never"
        
        try:
            # Parse timestamp
            last_seen = parse_timestamp(last_timestamp)
            now = datetime.now()
            minutes_ago = (now - last_seen).total_seconds() / 60
            
            # Determine status
            if minutes_ago <= Config.NODE_ONLINE_MINUTES:
                status = NodeStatus.ONLINE
            elif minutes_ago <= Config.NODE_IDLE_MINUTES:
                status = NodeStatus.IDLE
            else:
                status = NodeStatus.OFFLINE
            
            # Format time ago string
            if minutes_ago < 1:
                time_ago = f"{int(minutes_ago * 60)}s ago"
            elif minutes_ago < 60:
                time_ago = f"{int(minutes_ago)}m ago"
            else:
                time_ago = f"{int(minutes_ago / 60)}h ago"
            
            return status, time_ago
            
        except Exception as e:
            print(f"[NODE STATUS] Error: {e}")
            return NodeStatus.OFFLINE, "Unknown"
    
    def get_all_nodes_status(self, sheets_service: GoogleSheetsService) -> Dict[str, Any]:
        """Get status for all nodes"""
        data_stats = sheets_service.get_data_statistics()
        nodes = data_stats.get('nodes', [])
        
        if not nodes:
            return {
                "count": 0,
                "nodes": [],
                "summary": {"online": 0, "idle": 0, "offline": 0, "total": 0}
            }
        
        nodes_list = []
        summary = {"online": 0, "idle": 0, "offline": 0, "total": len(nodes)}
        
        for node_id in nodes:
            # Get latest data for this node
            node_data = sheets_service.get_historical_data(node_id=node_id, limit=1)
            
            if node_data:
                latest = node_data[0]
                last_timestamp = latest['timestamp']
                
                # Get status
                status, time_ago = self.get_node_status(last_timestamp)
                
                # Update summary
                if status == NodeStatus.ONLINE:
                    summary["online"] += 1
                elif status == NodeStatus.IDLE:
                    summary["idle"] += 1
                else:
                    summary["offline"] += 1
                
                # Analyze current risk
                analysis_service = FloodAnalysisService()
                rain_intensity = analysis_service.classify_rain_intensity(
                    latest['piezo_value'], latest['rain_sensor_value']
                )
                flood_risk, risk_percentage, _ = analysis_service.calculate_immediate_risk(
                    latest['ultrasonic_value'], rain_intensity
                )
                
                nodes_list.append({
                    "node_id": node_id,
                    "location": latest['location'],
                    "status": status.value,
                    "last_seen": last_timestamp,
                    "last_seen_ago": time_ago,
                    "water_level": latest['ultrasonic_value'],
                    "rain_intensity": rain_intensity.value,
                    "flood_risk": flood_risk.value,
                    "risk_percentage": risk_percentage,
                    "is_online": status == NodeStatus.ONLINE
                })
        
        # Sort by status (online first)
        nodes_list.sort(key=lambda x: {"online": 0, "idle": 1, "offline": 2}.get(x["status"], 3))
        
        return {
            "count": len(nodes_list),
            "nodes": nodes_list,
            "summary": summary
        }

class HistoricalAnalysisService:
    """Service for analyzing historical data in background"""
    
    def __init__(self, sheets_service: GoogleSheetsService, 
                 analysis_service: FloodAnalysisService,
                 alert_service: AlertService,
                 ai_service: AIAnalysisService):
        self.sheets_service = sheets_service
        self.analysis_service = analysis_service
        self.alert_service = alert_service
        self.ai_service = ai_service
        self.running = False
    
    async def start(self):
        """Start the background analysis service"""
        self.running = True
        print("[HISTORICAL ANALYSIS] Service started")
        
        try:
            while self.running:
                await self._analyze_historical_data()
                await asyncio.sleep(Config.ANALYSIS_INTERVAL_MINUTES * 60)  # Convert to seconds
        except asyncio.CancelledError:
            print("[HISTORICAL ANALYSIS] Service stopped")
        except Exception as e:
            print(f"[HISTORICAL ANALYSIS] Error: {e}")
    
    async def _analyze_historical_data(self):
        """Analyze historical data and send alerts if needed"""
        print(f"[HISTORICAL ANALYSIS] Analyzing at {datetime.now().strftime('%H:%M:%S')}")
        
        # Get all nodes from historical data
        data_stats = self.sheets_service.get_data_statistics()
        nodes = data_stats.get('nodes', [])
        
        if not nodes:
            print("[HISTORICAL ANALYSIS] No nodes found in data")
            return
        
        print(f"[HISTORICAL ANALYSIS] Found {len(nodes)} nodes")
        
        for node_id in nodes:
            try:
                await self._analyze_node(node_id)
            except Exception as e:
                print(f"[HISTORICAL ANALYSIS] Error analyzing {node_id}: {e}")
    
    async def _analyze_node(self, node_id: str):
        """Analyze a single node's historical data"""
        # Get historical data
        historical_data = self.sheets_service.get_historical_data(
            node_id=node_id, 
            days_back=Config.HISTORICAL_DAYS_TO_ANALYZE,
            limit=50
        )
        
        if not historical_data or len(historical_data) < Config.MIN_DATA_POINTS_FOR_ANALYSIS:
            return
        
        # Get latest reading
        latest = historical_data[0]  # Already sorted newest first
        water_level = latest['ultrasonic_value']
        piezo_value = latest['piezo_value']
        rain_sensor_value = latest['rain_sensor_value']
        location = latest['location']
        
        # Analyze
        rain_intensity = self.analysis_service.classify_rain_intensity(piezo_value, rain_sensor_value)
        flood_risk, risk_percentage, water_status = self.analysis_service.calculate_immediate_risk(
            water_level, rain_intensity, historical_data
        )
        
        # Check if alert should be sent
        should_alert = (
            risk_percentage >= Config.ALERT_RISK_THRESHOLD or
            flood_risk in [FloodRisk.HIGH, FloodRisk.CRITICAL] or
            water_level >= Config.WATER_LEVEL_WARNING
        )
        
        if should_alert:
            print(f"[HISTORICAL ANALYSIS] Sending alert for node {node_id}")
            await self.alert_service.send_alert(
                node_id=node_id,
                water_level=water_level,
                rain_intensity=rain_intensity,
                flood_risk=flood_risk,
                risk_percentage=risk_percentage,
                location=location,
                alert_type="historical"
            )
    
    def stop(self):
        """Stop the background service"""
        self.running = False

# ============== HELPER FUNCTIONS ==============

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp string"""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m%dT%H:%M:%S.%f"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except:
            continue
    
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except:
        return datetime.now()

def get_fallback_recommendation(flood_risk: FloodRisk, water_level: float) -> str:
    """Get fallback recommendation"""
    if flood_risk == FloodRisk.CRITICAL:
        return "IMMEDIATE EVACUATION REQUIRED. Contact emergency services immediately."
    elif flood_risk == FloodRisk.HIGH:
        return "Prepare for evacuation. Move to higher ground and avoid flood zones."
    elif flood_risk == FloodRisk.MODERATE:
        return "Monitor situation closely. Prepare emergency supplies."
    else:
        return "Continue normal monitoring. Stay alert for changes."

# ============== APPLICATION SETUP ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("\n" + "="*60)
    print("🚀 Flood Monitoring System - Starting Up")
    print("="*60)
    
    # Initialize services
    app.state.sheets_service = GoogleSheetsService()
    app.state.analysis_service = FloodAnalysisService()
    app.state.alert_service = AlertService()
    app.state.ai_service = AIAnalysisService()
    app.state.node_service = NodeStatusService()
    
    # Start historical analysis service
    app.state.historical_service = HistoricalAnalysisService(
        sheets_service=app.state.sheets_service,
        analysis_service=app.state.analysis_service,
        alert_service=app.state.alert_service,
        ai_service=app.state.ai_service
    )
    
    historical_task = asyncio.create_task(app.state.historical_service.start())
    app.state.background_tasks = [historical_task]
    
    print(f"[SYSTEM] Services initialized")
    print(f"[SYSTEM] Google Sheets: {'Connected' if app.state.sheets_service.client else 'Disconnected'}")
    print(f"[SYSTEM] Telegram: {'Configured' if app.state.alert_service.is_configured() else 'Not configured'}")
    print(f"[SYSTEM] Gemini AI: {'Available' if GEMINI_AVAILABLE else 'Using fallback'}")
    print("="*60 + "\n")
    
    yield
    
    # Shutdown
    print("\n" + "="*60)
    print("🛑 Flood Monitoring System - Shutting Down")
    print("="*60)
    
    # Stop background services
    app.state.historical_service.stop()
    for task in app.state.background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    print("[SYSTEM] All services stopped")
    print("="*60)

# Create FastAPI app
app = FastAPI(
    title="Flood Monitoring System",
    description="Hybrid system combining real-time IoT data with historical analysis",
    version="4.0.0",
    lifespan=lifespan
)

# CORS middleware
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

# ============== API ENDPOINTS ==============

@app.get("/", response_model=HealthResponse)
async def root():
    """System health check"""
    sheets_service = app.state.sheets_service
    alert_service = app.state.alert_service
    node_service = app.state.node_service
    
    # Get data statistics
    data_stats = sheets_service.get_data_statistics()
    
    # Get node status summary
    nodes_status = node_service.get_all_nodes_status(sheets_service)
    
    return HealthResponse(
        status="operational",
        timestamp=datetime.now().isoformat(),
        services={
            "api": "online",
            "google_sheets": "connected" if sheets_service.client else "disconnected",
            "telegram_alerts": "configured" if alert_service.is_configured() else "not_configured",
            "gemini_ai": "available" if GEMINI_AVAILABLE else "fallback_mode",
            "historical_analysis": "running",
            "active_nodes": nodes_status["summary"]["online"],
            "total_nodes": nodes_status["count"]
        },
        data_statistics=data_stats,
        system_info={
            "version": "4.0.0",
            "mode": "hybrid",
            "last_updated": datetime.now().isoformat(),
            "thresholds": {
                "water_warning": Config.WATER_LEVEL_WARNING,
                "water_danger": Config.WATER_LEVEL_DANGER,
                "alert_threshold": Config.ALERT_RISK_THRESHOLD
            }
        }
    )

@app.post("/api/sensor-data", response_model=SensorDataResponse)
async def receive_sensor_data(data: SensorData, background_tasks: BackgroundTasks):
    """
    Receive real-time data from ESP32/IoT sensor
    
    - Stores data immediately in Google Sheets
    - Analyzes for flood risk
    - Sends Telegram alert if conditions are met
    - Updates node status to online
    """
    print(f"\n[REAL-TIME] Data received from {data.node_id}")
    print(f"  Water: {data.ultrasonic_value:.1f}cm, Rain: {data.rain_sensor_value:.1f}")
    
    # Store data in Google Sheets
    sheets_service = app.state.sheets_service
    result = sheets_service.store_sensor_data(data)
    
    if not result["success"]:
        return SensorDataResponse(
            success=False,
            message="Failed to store data",
            data_id="",
            timestamp=datetime.now().isoformat(),
            risk_level="unknown",
            risk_percentage=0,
            alert_triggered=False
        )
    
    # Update node status
    app.state.node_service.update_node_status(data.node_id)
    
    # Analyze for immediate risk
    analysis_service = app.state.analysis_service
    rain_intensity = analysis_service.classify_rain_intensity(data.piezo_value, data.rain_sensor_value)
    
    # Get historical data for trend analysis
    historical_data = sheets_service.get_historical_data(
        node_id=data.node_id, 
        limit=10
    )
    
    flood_risk, risk_percentage, water_status = analysis_service.calculate_immediate_risk(
        data.ultrasonic_value, rain_intensity, historical_data
    )
    
    # Check if alert should be sent
    should_alert = (
        risk_percentage >= Config.ALERT_RISK_THRESHOLD or
        flood_risk in [FloodRisk.HIGH, FloodRisk.CRITICAL] or
        data.ultrasonic_value >= Config.WATER_LEVEL_WARNING
    )
    
    # Send alert if needed
    if should_alert:
        print(f"[ALERT] Triggering real-time alert for {data.node_id}")
        background_tasks.add_task(
            app.state.alert_service.send_alert,
            node_id=data.node_id,
            water_level=data.ultrasonic_value,
            rain_intensity=rain_intensity,
            flood_risk=flood_risk,
            risk_percentage=risk_percentage,
            location=data.location or "Unknown",
            alert_type="real_time"
        )
    
    # Prepare response
    message = f"Data stored. Risk: {flood_risk.value} ({risk_percentage:.1f}%)"
    if should_alert:
        message += " - Alert triggered!"
    
    return SensorDataResponse(
        success=True,
        message=message,
        data_id=result["data_id"],
        timestamp=result["timestamp"],
        risk_level=flood_risk.value,
        risk_percentage=risk_percentage,
        alert_triggered=should_alert
    )

@app.post("/api/predict", response_model=PredictionResponse)
async def predict_flood(request: PredictionRequest):
    """
    Generate flood prediction using both real-time and historical data
    
    - Uses latest available data (real-time if available, otherwise historical)
    - Analyzes with Gemini AI if available, otherwise uses mathematical fallback
    - Provides risk assessment and recommendations
    """
    
    sheets_service = app.state.sheets_service
    analysis_service = app.state.analysis_service
    ai_service = app.state.ai_service
    
    # Determine which node to analyze
    node_id = request.node_id
    if not node_id:
        # Try to auto-detect node
        data_stats = sheets_service.get_data_statistics()
        nodes = data_stats.get('nodes', [])
        if nodes:
            node_id = nodes[0]
        else:
            raise HTTPException(400, "No node_id provided and no data available")
    
    print(f"[PREDICTION] Analyzing node: {node_id}")
    
    # Get latest data (try real-time cache first, then historical)
    latest_data = None
    if hasattr(app.state, 'latest_readings') and node_id in app.state.latest_readings:
        latest_data = app.state.latest_readings[node_id]
        data_source = "real_time"
    else:
        historical = sheets_service.get_historical_data(node_id=node_id, limit=1)
        if historical:
            latest_data = historical[0]
            data_source = "historical"
        else:
            raise HTTPException(404, f"No data available for node: {node_id}")
    
    # Get historical data for trend analysis
    historical_data = sheets_service.get_historical_data(
        node_id=node_id, 
        limit=50,
        days_back=Config.HISTORICAL_DAYS_TO_ANALYZE
    )
    
    # Analyze current conditions
    water_level = latest_data['ultrasonic_value']
    piezo_value = latest_data['piezo_value']
    rain_sensor_value = latest_data['rain_sensor_value']
    
    rain_intensity = analysis_service.classify_rain_intensity(piezo_value, rain_sensor_value)
    is_raining = rain_sensor_value > 10
    
    flood_risk, risk_percentage, water_status = analysis_service.calculate_immediate_risk(
        water_level, rain_intensity, historical_data
    )
    
    # Get AI analysis
    ai_analysis, ai_provider = await ai_service.analyze(
        water_level, rain_intensity, flood_risk, risk_percentage, historical_data
    )
    
    # Get recommendations
    recommended_actions = analysis_service.get_recommended_actions(flood_risk, water_level)
    
    # Generate summary
    prediction_summary = (
        f"Flood risk is {flood_risk.value.upper()} ({risk_percentage:.1f}%). "
        f"Water level: {water_level:.1f}cm ({water_status}). "
        f"Rain intensity: {rain_intensity.value}. "
        f"Data source: {data_source}. "
        f"AI provider: {ai_provider}."
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
        ai_provider=ai_provider,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/history")
async def get_sensor_history(node_id: Optional[str] = None, limit: int = 1000):
    """
    Get historical sensor data for charts and analysis
    
    - Returns data in format suitable for frontend charts
    - Auto-detects node if not specified
    - Includes chart-ready arrays
    """
    sheets_service = app.state.sheets_service
    
    # Auto-detect node if not specified
    if not node_id:
        data_stats = sheets_service.get_data_statistics()
        nodes = data_stats.get('nodes', [])
        if nodes:
            node_id = nodes[0]
            print(f"[HISTORY] Auto-detected node: {node_id}")
    
    # Get historical data
    data = sheets_service.get_historical_data(node_id=node_id, limit=limit)
    
    # Prepare chart data
    timestamps = []
    water_levels = []
    rain_intensities = []
    piezo_values = []
    
    for record in data:
        timestamps.append(record.get('timestamp', ''))
        water_levels.append(record.get('ultrasonic_value', 0))
        rain_intensities.append(record.get('rain_sensor_value', 0))
        piezo_values.append(record.get('piezo_value', 0))
    
    # Calculate statistics
    stats = {}
    if water_levels:
        stats = {
            "avg_water_level": sum(water_levels) / len(water_levels),
            "max_water_level": max(water_levels),
            "min_water_level": min(water_levels),
            "total_readings": len(data)
        }
    
    return {
        "node_id": node_id or "all",
        "count": len(data),
        "data": data,
        "chart_data": {
            "timestamps": timestamps,
            "water_levels": water_levels,
            "rain_intensities": rain_intensities,
            "piezo_values": piezo_values
        },
        "statistics": stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/nodes")
async def get_all_nodes():
    """
    Get status of all nodes for dashboard
    
    - Returns node list with current status
    - Includes risk levels and last seen times
    - Suitable for frontend node cards
    """
    node_service = app.state.node_service
    sheets_service = app.state.sheets_service
    
    result = node_service.get_all_nodes_status(sheets_service)
    
    # Add system info
    result.update({
        "system_status": "operational",
        "last_updated": datetime.now().isoformat(),
        "telegram_configured": app.state.alert_service.is_configured(),
        "gemini_available": GEMINI_AVAILABLE
    })
    
    return result

@app.get("/api/status/{node_id}")
async def get_node_status(node_id: str):
    """Get detailed status for a specific node"""
    sheets_service = app.state.sheets_service
    analysis_service = app.state.analysis_service
    node_service = app.state.node_service
    
    # Get latest data
    historical_data = sheets_service.get_historical_data(node_id=node_id, limit=10)
    
    if not historical_data:
        raise HTTPException(404, f"No data found for node: {node_id}")
    
    latest = historical_data[0]
    
    # Analyze
    rain_intensity = analysis_service.classify_rain_intensity(
        latest['piezo_value'], latest['rain_sensor_value']
    )
    
    flood_risk, risk_percentage, water_status = analysis_service.calculate_immediate_risk(
        latest['ultrasonic_value'], rain_intensity, historical_data
    )
    
    # Get node status
    status, time_ago = node_service.get_node_status(latest['timestamp'])
    
    return {
        "node_id": node_id,
        "location": latest['location'],
        "status": status.value,
        "is_online": status == NodeStatus.ONLINE,
        "last_seen": latest['timestamp'],
        "last_seen_ago": time_ago,
        "current_reading": {
            "water_level": latest['ultrasonic_value'],
            "rain_intensity": rain_intensity.value,
            "piezo_value": latest['piezo_value'],
            "rain_sensor_value": latest['rain_sensor_value']
        },
        "risk_assessment": {
            "level": flood_risk.value,
            "percentage": risk_percentage,
            "water_status": water_status,
            "recommended_actions": analysis_service.get_recommended_actions(flood_risk, latest['ultrasonic_value'])[:3]
        },
        "data_points": len(historical_data),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/analyze-all")
async def analyze_all_nodes(background_tasks: BackgroundTasks = None):
    """
    Analyze all nodes at once
    
    - Uses historical data for offline nodes
    - Can trigger alerts if conditions are met
    - Returns analysis results
    """
    sheets_service = app.state.sheets_service
    analysis_service = app.state.analysis_service
    alert_service = app.state.alert_service
    
    # Get all nodes
    data_stats = sheets_service.get_data_statistics()
    nodes = data_stats.get('nodes', [])
    
    if not nodes:
        return {
            "success": False,
            "message": "No nodes found in data",
            "timestamp": datetime.now().isoformat()
        }
    
    print(f"[ANALYZE ALL] Analyzing {len(nodes)} nodes")
    
    results = []
    alerts_sent = 0
    
    for node_id in nodes:
        try:
            # Get historical data
            historical_data = sheets_service.get_historical_data(
                node_id=node_id, 
                limit=20,
                days_back=Config.HISTORICAL_DAYS_TO_ANALYZE
            )
            
            if not historical_data or len(historical_data) < Config.MIN_DATA_POINTS_FOR_ANALYSIS:
                continue
            
            latest = historical_data[0]
            water_level = latest['ultrasonic_value']
            piezo_value = latest['piezo_value']
            rain_sensor_value = latest['rain_sensor_value']
            location = latest['location']
            
            # Analyze
            rain_intensity = analysis_service.classify_rain_intensity(piezo_value, rain_sensor_value)
            flood_risk, risk_percentage, water_status = analysis_service.calculate_immediate_risk(
                water_level, rain_intensity, historical_data
            )
            
            # Check if alert should be sent
            should_alert = (
                risk_percentage >= Config.ALERT_RISK_THRESHOLD or
                flood_risk in [FloodRisk.HIGH, FloodRisk.CRITICAL] or
                water_level >= Config.WATER_LEVEL_WARNING
            )
            
            # Send alert if needed
            if should_alert and background_tasks:
                background_tasks.add_task(
                    alert_service.send_alert,
                    node_id=node_id,
                    water_level=water_level,
                    rain_intensity=rain_intensity,
                    flood_risk=flood_risk,
                    risk_percentage=risk_percentage,
                    location=location,
                    alert_type="historical"
                )
                alerts_sent += 1
            
            results.append({
                "node_id": node_id,
                "location": location,
                "water_level": water_level,
                "rain_intensity": rain_intensity.value,
                "flood_risk": flood_risk.value,
                "risk_percentage": risk_percentage,
                "water_status": water_status,
                "should_alert": should_alert,
                "data_points": len(historical_data)
            })
            
        except Exception as e:
            print(f"[ANALYZE ALL] Error analyzing {node_id}: {e}")
            results.append({
                "node_id": node_id,
                "error": str(e)
            })
    
    return {
        "success": True,
        "total_nodes": len(nodes),
        "analyzed": len([r for r in results if 'error' not in r]),
        "alerts_sent": alerts_sent,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/test-telegram")
async def test_telegram_connection():
    """Test Telegram integration"""
    alert_service = app.state.alert_service
    
    if not alert_service.is_configured():
        return {
            "success": False,
            "configured": False,
            "message": "Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID."
        }
    
    success = await alert_service.send_test_alert()
    
    return {
        "success": success,
        "configured": True,
        "message": "Test message sent successfully" if success else "Failed to send test message",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/test-alert")
async def test_alert(background_tasks: BackgroundTasks):
    """Trigger a test flood alert"""
    alert_service = app.state.alert_service
    
    if not alert_service.is_configured():
        return {
            "success": False,
            "message": "Telegram not configured"
        }
    
    # Simulate high-risk conditions
    test_data = {
        "node_id": "test_node_001",
        "water_level": 65.5,
        "rain_intensity": RainIntensity.HEAVY,
        "flood_risk": FloodRisk.HIGH,
        "risk_percentage": 75.0,
        "location": "Test Location"
    }
    
    if background_tasks:
        background_tasks.add_task(
            alert_service.send_alert,
            node_id=test_data["node_id"],
            water_level=test_data["water_level"],
            rain_intensity=test_data["rain_intensity"],
            flood_risk=test_data["flood_risk"],
            risk_percentage=test_data["risk_percentage"],
            location=test_data["location"],
            alert_type="real_time"
        )
        
        return {
            "success": True,
            "message": "Test alert triggered in background",
            "test_data": test_data,
            "timestamp": datetime.now().isoformat()
        }
    
    # Send immediately if no background tasks
    sent = await alert_service.send_alert(
        node_id=test_data["node_id"],
        water_level=test_data["water_level"],
        rain_intensity=test_data["rain_intensity"],
        flood_risk=test_data["flood_risk"],
        risk_percentage=test_data["risk_percentage"],
        location=test_data["location"],
        alert_type="real_time"
    )
    
    return {
        "success": sent,
        "message": "Test alert sent" if sent else "Test alert failed",
        "test_data": test_data,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/system-info")
async def get_system_info():
    """Get detailed system information"""
    sheets_service = app.state.sheets_service
    alert_service = app.state.alert_service
    
    data_stats = sheets_service.get_data_statistics()
    
    return {
        "system": {
            "name": "Flood Monitoring System",
            "version": "4.0.0",
            "mode": "Hybrid (Real-time + Historical)",
            "status": "operational",
            "uptime": datetime.now().isoformat()
        },
        "configuration": {
            "water_level_warning": Config.WATER_LEVEL_WARNING,
            "water_level_danger": Config.WATER_LEVEL_DANGER,
            "alert_risk_threshold": Config.ALERT_RISK_THRESHOLD,
            "historical_days_analyzed": Config.HISTORICAL_DAYS_TO_ANALYZE,
            "analysis_interval_minutes": Config.ANALYSIS_INTERVAL_MINUTES
        },
        "services": {
            "google_sheets": {
                "connected": bool(sheets_service.client),
                "spreadsheet": Config.SPREADSHEET_NAME
            },
            "telegram_alerts": {
                "configured": alert_service.is_configured(),
                "cooldown_minutes": Config.ALERT_COOLDOWN_MINUTES
            },
            "ai_analysis": {
                "provider": "Gemini AI" if GEMINI_AVAILABLE else "Mathematical Fallback",
                "available": GEMINI_AVAILABLE
            },
            "historical_analysis": {
                "enabled": True,
                "interval_minutes": Config.ANALYSIS_INTERVAL_MINUTES
            }
        },
        "data": data_stats,
        "timestamp": datetime.now().isoformat()
    }

# ============== RUN SERVER ==============

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🌊 Flood Monitoring System v4.0.0")
    print("="*60)
    print("Mode: Hybrid (Real-time IoT + Historical Analysis)")
    print("AI: Gemini AI with Mathematical Fallback")
    print("Data Storage: Google Sheets")
    print("="*60)
    
    # Test Google Sheets connection on startup
    try:
        test_service = GoogleSheetsService()
        if test_service.client:
            print("[STARTUP] Google Sheets connection: ✓ SUCCESS")
            # Test reading data
            stats = test_service.get_data_statistics()
            print(f"[STARTUP] Found {stats['total_records']} records for {stats['nodes_found']} nodes")
        else:
            print("[STARTUP] Google Sheets connection: ✗ FAILED")
    except Exception as e:
        print(f"[STARTUP] Google Sheets test error: {e}")
    
    print("="*60 + "\n")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        # reload=True,
        log_level="info"
    )