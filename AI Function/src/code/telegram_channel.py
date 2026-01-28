"""
Telegram Bot for Flood Detection and Rain Monitoring System
CHANNEL-ONLY VERSION
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional
import httpx

# ================= LOGGING =================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= CONFIG =================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7844415200:AAF5FG3YpCx9oqUtKGIonS5X_oIXU_GYCj4")
TELEGRAM_CHANNEL_ID = int(os.getenv("TELEGRAM_CHANNEL_ID", "-1003795098612"))
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

ALERT_RISK_THRESHOLD = 50
ALERT_CHECK_INTERVAL = 60

# ================= TELEGRAM API =================

class TelegramBot:
    def __init__(self, token: str, channel_id: int):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.channel_id = channel_id
        self.last_update_id = 0

    async def send_channel_message(self, text: str, parse_mode: str = "HTML") -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.channel_id,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    async def get_updates(self, offset: int = 0) -> list:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/getUpdates",
                    params={"offset": offset, "timeout": 30}
                )
                if response.status_code == 200:
                    return response.json().get("result", [])
        except Exception as e:
            logger.error(f"Update fetch failed: {e}")
        return []

# ================= BACKEND CLIENT =================

class BackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_health(self) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self.base_url}/")
                if r.status_code == 200:
                    return r.json()
        except Exception as e:
            logger.error(e)
        return None

    async def get_prediction(self, node_id: str = None) -> Optional[dict]:
        try:
            payload = {"node_id": node_id} if node_id else {}
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(f"{self.base_url}/api/predict", json=payload)
                if r.status_code == 200:
                    return r.json()
        except Exception as e:
            logger.error(e)
        return None

    async def get_history(self, node_id: str = None, limit: int = 5) -> Optional[dict]:
        try:
            params = {"limit": limit}
            if node_id:
                params["node_id"] = node_id
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self.base_url}/api/history", params=params)
                if r.status_code == 200:
                    return r.json()
        except Exception as e:
            logger.error(e)
        return None

# ================= COMMAND HANDLER =================

class BotHandler:
    def __init__(self, bot: TelegramBot, backend: BackendClient):
        self.bot = bot
        self.backend = backend

    async def handle_status(self):
        health = await self.backend.get_health()
        if not health:
            await self.bot.send_channel_message("❌ Backend unreachable")
            return

        services = health.get("services", {})
        msg = f"""
✅ <b>System Status</b>

• API: {services.get('api')}
• Database: {services.get('google_sheets')}
• AI: {services.get('llm')}

<i>{health.get('timestamp')}</i>
"""
        await self.bot.send_channel_message(msg)

    async def handle_predict(self, node_id=None):
        await self.bot.send_channel_message("🔄 Generating flood prediction...")
        p = await self.backend.get_prediction(node_id)
        if not p:
            await self.bot.send_channel_message("❌ Prediction failed")
            return

        msg = f"""
🚨 <b>Flood Prediction</b>

📍 Node: {p.get('node_id')}
💧 Water Level: {p.get('current_water_level')} cm
🌧 Rain: {p.get('current_rain_intensity')}
⚠ Risk: {p.get('flood_risk').upper()} ({p.get('risk_percentage')}%)

<b>AI Analysis</b>
{p.get('ai_analysis')}
"""
        await self.bot.send_channel_message(msg)

    async def process_update(self, update: dict):
        msg = update.get("message")
        if not msg or msg.get("chat", {}).get("id") != TELEGRAM_CHANNEL_ID:
            return

        text = msg.get("text", "")
        if text.startswith("/status"):
            await self.handle_status()
        elif text.startswith("/predict"):
            parts = text.split()
            node_id = parts[1] if len(parts) > 1 else None
            await self.handle_predict(node_id)

# ================= ALERT SYSTEM =================

class AlertSystem:
    def __init__(self, bot: TelegramBot, backend: BackendClient):
        self.bot = bot
        self.backend = backend
        self.cooldown = {}

    async def check_and_alert(self):
        p = await self.backend.get_prediction()
        if not p:
            return

        risk = p.get("risk_percentage", 0)
        node = p.get("node_id")

        if risk < ALERT_RISK_THRESHOLD:
            return

        now = datetime.now()
        last = self.cooldown.get(node)
        if last and (now - last).seconds < 900:
            return

        self.cooldown[node] = now

        msg = f"""
🚨 <b>FLOOD ALERT</b>

📍 Node: {node}
💧 Water Level: {p.get('current_water_level')} cm
🌧 Rain: {p.get('current_rain_intensity')}

<b>Risk: {p.get('flood_risk').upper()} ({risk}%)</b>

{p.get('ai_analysis')}
"""
        await self.bot.send_channel_message(msg)

# ================= MAIN LOOP =================

async def run_bot():
    bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)
    backend = BackendClient(BACKEND_API_URL)
    handler = BotHandler(bot, backend)
    alerts = AlertSystem(bot, backend)

    logger.info("🚀 Channel-only Telegram bot started")

    last_alert_check = 0

    while True:
        updates = await bot.get_updates(bot.last_update_id + 1)
        for u in updates:
            bot.last_update_id = u["update_id"]
            await handler.process_update(u)

        now = asyncio.get_event_loop().time()
        if now - last_alert_check > ALERT_CHECK_INTERVAL:
            await alerts.check_and_alert()
            last_alert_check = now

        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_bot())
