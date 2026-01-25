"""
Telegram Bot for Flood Detection and Rain Monitoring System

This bot provides real-time flood alerts and allows users to query
the current flood status through Telegram.

Features:
- Real-time flood alerts
- Query current sensor status
- Subscribe to notifications
- View prediction reports
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional
import httpx

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============== CONFIGURATION ==============

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# Alert thresholds
ALERT_RISK_THRESHOLD = 50  # Send alert when risk >= 50%

# Polling interval for checking alerts (in seconds)
ALERT_CHECK_INTERVAL = 60

# ============== TELEGRAM API WRAPPER ==============

class TelegramBot:
    """Simple Telegram Bot API wrapper"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.subscribers = set()  # Store chat IDs of subscribers
        self.last_update_id = 0
        
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to a specific chat"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def get_updates(self, offset: int = 0) -> list:
        """Get updates from Telegram"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/getUpdates",
                    params={"offset": offset, "timeout": 30}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("result", [])
        except Exception as e:
            logger.error(f"Failed to get updates: {e}")
        return []
    
    async def broadcast(self, text: str) -> int:
        """Send message to all subscribers"""
        success_count = 0
        for chat_id in self.subscribers.copy():
            if await self.send_message(chat_id, text):
                success_count += 1
        return success_count

# ============== BACKEND API CLIENT ==============

class BackendClient:
    """Client for interacting with the FastAPI backend"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def get_health(self) -> Optional[dict]:
        """Check backend health status"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Backend health check failed: {e}")
        return None
    
    async def get_prediction(self, node_id: str = None) -> Optional[dict]:
        """Get flood prediction from backend"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {}
                if node_id:
                    payload["node_id"] = node_id
                
                response = await client.post(
                    f"{self.base_url}/api/predict",
                    json=payload
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get prediction: {e}")
        return None
    
    async def get_node_status(self, node_id: str) -> Optional[dict]:
        """Get status for a specific node"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/status/{node_id}")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get node status: {e}")
        return None
    
    async def get_history(self, node_id: str = None, limit: int = 10) -> Optional[dict]:
        """Get historical sensor data"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"limit": limit}
                if node_id:
                    params["node_id"] = node_id
                
                response = await client.get(
                    f"{self.base_url}/api/history",
                    params=params
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
        return None

# ============== MESSAGE HANDLERS ==============

class BotHandler:
    """Handle incoming messages and commands"""
    
    def __init__(self, bot: TelegramBot, backend: BackendClient):
        self.bot = bot
        self.backend = backend
    
    async def handle_start(self, chat_id: int, user_name: str) -> None:
        """Handle /start command"""
        self.bot.subscribers.add(chat_id)
        
        message = f"""
🌊 <b>Flood Detection & Rain Monitoring System</b>

Welcome, {user_name}! 👋

You are now subscribed to flood alerts. I will notify you when:
⚠️ Flood risk exceeds {ALERT_RISK_THRESHOLD}%
🌧️ Heavy rain is detected
🚨 Critical water levels are reached

<b>Available Commands:</b>
/status - Get current flood status
/predict - Get flood prediction
/history - View recent sensor data
/help - Show this help message
/unsubscribe - Stop receiving alerts

Stay safe! 🏠
"""
        await self.bot.send_message(chat_id, message)
    
    async def handle_status(self, chat_id: int) -> None:
        """Handle /status command"""
        health = await self.backend.get_health()
        
        if health:
            services = health.get("services", {})
            status_emoji = "✅" if health.get("status") == "operational" else "⚠️"
            
            message = f"""
{status_emoji} <b>System Status</b>

<b>Services:</b>
• API: {services.get('api', 'unknown')}
• Database: {services.get('google_sheets', 'unknown')}
• AI/LLM: {services.get('llm', 'unknown')}

<i>Last updated: {health.get('timestamp', 'N/A')}</i>
"""
        else:
            message = "❌ Unable to connect to the backend system. Please try again later."
        
        await self.bot.send_message(chat_id, message)
    
    async def handle_predict(self, chat_id: int, node_id: str = None) -> None:
        """Handle /predict command"""
        await self.bot.send_message(chat_id, "🔄 Analyzing flood risk...")
        
        prediction = await self.backend.get_prediction(node_id)
        
        if prediction:
            risk = prediction.get("flood_risk", "unknown")
            risk_pct = prediction.get("risk_percentage", 0)
            
            # Choose emoji based on risk level
            risk_emoji = {
                "low": "🟢",
                "moderate": "🟡",
                "high": "🟠",
                "critical": "🔴"
            }.get(risk, "⚪")
            
            actions = prediction.get("recommended_actions", [])
            actions_text = "\n".join([f"• {action}" for action in actions[:5]])
            
            message = f"""
{risk_emoji} <b>Flood Prediction Report</b>

📍 <b>Node:</b> {prediction.get('node_id', 'N/A')}
💧 <b>Water Level:</b> {prediction.get('current_water_level', 0):.1f} cm
🌧️ <b>Rain Intensity:</b> {prediction.get('current_rain_intensity', 'N/A')}
☔ <b>Is Raining:</b> {'Yes' if prediction.get('is_raining') else 'No'}

<b>Risk Assessment:</b>
{risk_emoji} {risk.upper()} ({risk_pct:.1f}%)

<b>Summary:</b>
{prediction.get('prediction_summary', 'N/A')}

<b>AI Analysis:</b>
{prediction.get('ai_analysis', 'N/A')}

<b>Recommended Actions:</b>
{actions_text}

<i>Generated: {prediction.get('timestamp', 'N/A')}</i>
"""
        else:
            message = """
❌ <b>Unable to Generate Prediction</b>

No sensor data available. Please ensure:
• IoT nodes are sending data
• Backend system is operational

Try /status to check system health.
"""
        
        await self.bot.send_message(chat_id, message)
    
    async def handle_history(self, chat_id: int, node_id: str = None) -> None:
        """Handle /history command"""
        history = await self.backend.get_history(node_id, limit=5)
        
        if history and history.get("data"):
            data = history.get("data", [])
            
            readings = []
            for reading in data[-5:]:
                readings.append(
                    f"• Water: {reading.get('ultrasonic_value', 0):.1f}cm | "
                    f"Rain: {reading.get('rain_sensor_value', 0):.0f}%"
                )
            
            readings_text = "\n".join(readings)
            
            message = f"""
📊 <b>Recent Sensor Readings</b>

{readings_text}

<i>Showing last {len(data)} readings</i>
"""
        else:
            message = "📭 No historical data available."
        
        await self.bot.send_message(chat_id, message)
    
    async def handle_unsubscribe(self, chat_id: int) -> None:
        """Handle /unsubscribe command"""
        self.bot.subscribers.discard(chat_id)
        
        message = """
👋 <b>Unsubscribed</b>

You will no longer receive flood alerts.
Use /start to subscribe again anytime.

Stay safe! 🏠
"""
        await self.bot.send_message(chat_id, message)
    
    async def handle_help(self, chat_id: int) -> None:
        """Handle /help command"""
        message = """
📖 <b>Help - Available Commands</b>

/start - Subscribe to flood alerts
/status - Check system status
/predict - Get flood prediction
/predict [node_id] - Predict for specific node
/history - View recent sensor readings
/unsubscribe - Stop receiving alerts
/help - Show this message

<b>Alert Notifications:</b>
You'll receive automatic alerts when:
• Flood risk exceeds {threshold}%
• Water levels reach warning thresholds
• Heavy rainfall is detected

<b>Need Support?</b>
Contact your system administrator.
""".format(threshold=ALERT_RISK_THRESHOLD)
        
        await self.bot.send_message(chat_id, message)
    
    async def process_message(self, update: dict) -> None:
        """Process incoming message"""
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()
        user = message.get("from", {})
        user_name = user.get("first_name", "User")
        
        if not chat_id or not text:
            return
        
        # Parse command
        parts = text.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Handle commands
        if command == "/start":
            await self.handle_start(chat_id, user_name)
        elif command == "/status":
            await self.handle_status(chat_id)
        elif command == "/predict":
            node_id = args[0] if args else None
            await self.handle_predict(chat_id, node_id)
        elif command == "/history":
            node_id = args[0] if args else None
            await self.handle_history(chat_id, node_id)
        elif command == "/unsubscribe":
            await self.handle_unsubscribe(chat_id)
        elif command == "/help":
            await self.handle_help(chat_id)
        else:
            # Unknown command
            await self.bot.send_message(
                chat_id,
                "❓ Unknown command. Use /help to see available commands."
            )

# ============== ALERT SYSTEM ==============

class AlertSystem:
    """Automated alert system for flood notifications"""
    
    def __init__(self, bot: TelegramBot, backend: BackendClient):
        self.bot = bot
        self.backend = backend
        self.last_alert_risk = 0
        self.alert_cooldown = {}  # Track alert cooldowns per node
    
    async def check_and_alert(self) -> None:
        """Check current conditions and send alerts if needed"""
        try:
            prediction = await self.backend.get_prediction()
            
            if not prediction:
                return
            
            risk_pct = prediction.get("risk_percentage", 0)
            flood_risk = prediction.get("flood_risk", "low")
            node_id = prediction.get("node_id", "unknown")
            
            # Check if alert should be sent
            should_alert = (
                risk_pct >= ALERT_RISK_THRESHOLD and
                flood_risk in ["high", "critical"] and
                self._can_alert(node_id)
            )
            
            if should_alert:
                await self._send_alert(prediction)
                self._update_cooldown(node_id)
                
        except Exception as e:
            logger.error(f"Alert check failed: {e}")
    
    def _can_alert(self, node_id: str) -> bool:
        """Check if we can send alert (cooldown check)"""
        if node_id not in self.alert_cooldown:
            return True
        
        last_alert = self.alert_cooldown[node_id]
        cooldown_minutes = 15  # 15 minute cooldown between alerts
        
        time_diff = (datetime.now() - last_alert).total_seconds() / 60
        return time_diff >= cooldown_minutes
    
    def _update_cooldown(self, node_id: str) -> None:
        """Update alert cooldown for node"""
        self.alert_cooldown[node_id] = datetime.now()
    
    async def _send_alert(self, prediction: dict) -> None:
        """Send flood alert to all subscribers"""
        risk = prediction.get("flood_risk", "unknown")
        risk_pct = prediction.get("risk_percentage", 0)
        
        emoji = "🚨" if risk == "critical" else "⚠️"
        
        actions = prediction.get("recommended_actions", [])
        actions_text = "\n".join([f"• {action}" for action in actions[:3]])
        
        message = f"""
{emoji} <b>FLOOD ALERT</b> {emoji}

📍 <b>Node:</b> {prediction.get('node_id', 'N/A')}
💧 <b>Water Level:</b> {prediction.get('current_water_level', 0):.1f} cm
🌧️ <b>Rain:</b> {prediction.get('current_rain_intensity', 'N/A')}

<b>Risk Level: {risk.upper()} ({risk_pct:.1f}%)</b>

<b>Immediate Actions:</b>
{actions_text}

<b>AI Analysis:</b>
{prediction.get('ai_analysis', 'Stay alert and monitor conditions.')}

<i>Stay safe and follow local authority guidelines!</i>
"""
        
        count = await self.bot.broadcast(message)
        logger.info(f"Flood alert sent to {count} subscribers")

# ============== MAIN BOT RUNNER ==============

async def run_bot():
    """Main bot runner"""
    bot = TelegramBot(TELEGRAM_BOT_TOKEN)
    backend = BackendClient(BACKEND_API_URL)
    handler = BotHandler(bot, backend)
    alert_system = AlertSystem(bot, backend)
    
    logger.info("Starting Flood Detection Telegram Bot...")
    
    # Check backend health
    health = await backend.get_health()
    if health:
        logger.info("Backend connection successful")
    else:
        logger.warning("Backend connection failed - bot will retry")
    
    last_alert_check = 0
    
    while True:
        try:
            # Get and process updates
            updates = await bot.get_updates(offset=bot.last_update_id + 1)
            
            for update in updates:
                bot.last_update_id = update.get("update_id", 0)
                await handler.process_message(update)
            
            # Check for alerts periodically
            current_time = asyncio.get_event_loop().time()
            if current_time - last_alert_check >= ALERT_CHECK_INTERVAL:
                await alert_system.check_and_alert()
                last_alert_check = current_time
            
            # Small delay to prevent excessive API calls
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Bot error: {e}")
            await asyncio.sleep(5)

# ============== ENTRY POINT ==============

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
