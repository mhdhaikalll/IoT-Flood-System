# Flood Detection and Rain Monitoring System - API Documentation

The FastAPI backend service for the Flood Detection and Rain Monitoring System. This is the **Hybrid Edition** that combines real-time IoT sensor data with historical Google Sheets analysis and Gemini AI-powered predictions.

## 🚀 Features

- **Receive IoT Sensor Data**: Accepts data from ESP32 nodes with Piezoelectric, Ultrasonic, and Rain sensors
- **Google Sheets Storage**: Stores all sensor data in Google Sheets as a persistent database
- **Hybrid AI Predictions**: Uses Gemini AI (`gemini-2.5-flash`) with mathematical fallback
- **Telegram Channel Alerts**: Sends automated alerts when flood risk is HIGH or CRITICAL (≥50%)
- **Node Status Monitoring**: Tracks online/idle/offline status based on last data transmission
- **Historical Analysis**: Analyzes trends from the last 3 days of data
- **RESTful API**: Provides endpoints for data ingestion, prediction, history, and status

## ⚙️ Setup

### 1. Install Dependencies

```bash
cd "AI Function/src"
pip install -r requirements.txt
```

### 2. Configure Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google Sheets API** and **Google Drive API**
4. Create a Service Account and download the JSON credentials
5. Save the credentials as `credentials.json` in the `code/` directory
6. Create a Google Sheet named "FloodMonitoringData" and share it with the service account email

### 3. Configure Telegram Alerts

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather)
2. Create a Telegram channel
3. Add the bot to your channel and make it an **admin**
4. Get your channel ID (format: `-100xxxxxxxxxx`)
5. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` in your `.env` file

### 4. Configure Gemini AI

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
2. Set `GEMINI_API_KEY` in your `.env` file
3. The system uses `gemini-2.5-flash` model by default

### 5. Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

```env
# Google Sheets
GOOGLE_SHEETS_CREDENTIALS=credentials.json
SPREADSHEET_NAME=FloodMonitoringData

# AI Provider
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHANNEL_ID=-100xxxxxxxxxx

# Frontend CORS
FRONTEND_URL=http://localhost:3000
```

### 6. Run the Server

```bash
cd code
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### Health Check

```
GET /
```
Returns system status, service availability, and data statistics.

### Submit Sensor Data

```
POST /api/sensor-data
```
Receives IoT sensor data and triggers Telegram alert if risk is HIGH or CRITICAL.

**Request Body:**
```json
{
    "node_id": "NODE-001",
    "piezo_value": 350.5,
    "ultrasonic_value": 45.2,
    "rain_sensor_value": 2500,
    "location": "Shah Alam, Selangor",
    "timestamp": "2026-02-03T10:30:00"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Sensor data stored successfully",
    "data_id": "NODE-001_20260203103000",
    "timestamp": "2026-02-03T10:30:00",
    "prediction": {
        "flood_risk": "LOW",
        "probability": 15,
        "rain_intensity": "LIGHT",
        "water_level_status": "NORMAL"
    }
}
```

### Get Flood Prediction

```
POST /api/predict
```
Get AI-powered flood risk prediction for a specific node.

**Request Body:**
```json
{
    "node_id": "NODE-001"
}
```

**Response:**
```json
{
    "node_id": "NODE-001",
    "current_water_level": 45.2,
    "current_rain_intensity": "light",
    "is_raining": true,
    "flood_risk": "moderate",
    "risk_percentage": 35.0,
    "prediction_summary": "Flood risk is MODERATE (35.0%). Water level: 45.2cm.",
    "recommended_actions": ["Continue monitoring water levels"],
    "ai_analysis": "...",
    "analysis_source": "gemini",
    "timestamp": "2026-02-03T10:30:00"
}
```

### Get Sensor History

```
GET /api/history?node_id=NODE-001&limit=50&days_back=7
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node_id` | string | - | Filter by node ID (optional) |
| `limit` | int | 100 | Maximum records to return |
| `days_back` | int | - | Filter by days (optional) |

### Get Node Status

```
GET /api/status/{node_id}
```
Get detailed status and latest readings for a specific node.

### Get All Nodes

```
GET /api/nodes
```
Get status of all registered nodes.

### Analyze All Nodes

```
GET /api/analyze-all
```
Perform AI analysis on all active nodes simultaneously.

### Test Telegram

```
GET /api/test-telegram
```
Test Telegram bot connection.

### Test Alert

```
POST /api/test-alert
```
Trigger a test flood alert to Telegram channel.

### System Info

```
GET /api/system-info
```
Get detailed system configuration and statistics.

## 📊 Sensor Data Interpretation

### Piezo Sensor (Vibration/Rain Detection)
| Value Range | Meaning |
|-------------|---------|
| 0 - 200 | No rain / Calm |
| 200 - 500 | Light activity |
| 500 - 800 | Moderate activity |
| > 800 | Heavy rain / Strong vibration |

### Ultrasonic Sensor (Water Level)
| Value (cm) | Status |
|------------|--------|
| < 50 | ✅ Normal |
| 50 - 79 | ⚠️ Warning |
| ≥ 80 | 🚨 Danger |

### Rain Sensor (Analog)
| Value Range | Rain Intensity |
|-------------|----------------|
| ≥ 3000 | None |
| 2000 - 2999 | Light |
| 1000 - 1999 | Moderate |
| < 1000 | Heavy |

## 🎯 Flood Risk Levels

| Level     | Risk % | Water Level | Action                  |
|-----------|--------|-------------|-------------------------|
| 🟢 LOW       | 0-24%  | < 30 cm | Normal monitoring       |
| 🟡 MODERATE  | 25-49% | 30-50 cm | Increased monitoring    |
| 🟠 HIGH      | 50-74% | 50-80 cm | Prepare evacuation      |
| 🔴 CRITICAL  | 75-100%| > 80 cm | Immediate evacuation    |

## 📱 Telegram Alert Logic

Alerts are automatically sent to the configured Telegram channel when:

- ✅ Flood risk is **HIGH** or **CRITICAL**
- ✅ Risk percentage is **≥50%**
- ✅ Cooldown period (**15 minutes**) has passed for the node

### Alert Message Format

```
🚨 FLOOD ALERT 🚨

📍 Node: NODE-001
📌 Location: Shah Alam, Selangor
💧 Water Level: 85.0 cm
🌧️ Rain Intensity: heavy

Risk Level: CRITICAL (92.5%)

Immediate Actions:
• IMMEDIATE EVACUATION REQUIRED
• Emergency services on high alert
• All residents must move to higher ground

⏰ Alert Time: 2026-02-03 14:30:00
```

## 🤖 Hybrid AI System

The backend uses a **Hybrid Edition** approach:

### Primary: Google Gemini AI
- Model: `gemini-2.5-flash`
- Provides intelligent analysis with contextual recommendations
- Considers historical patterns and environmental factors

### Fallback: Mathematical Model
When Gemini is unavailable, the system uses weighted calculations:

```python
risk = (water_level_risk * 0.4) + (piezo_risk * 0.3) + (rain_risk * 0.3)
```

## 🏗️ Architecture

```
IoT Node (ESP32 Sensors)
    │
    ▼ POST /api/sensor-data
┌──────────────────────────────────────────┐
│      FastAPI Server (main.py)            │
│   ┌──────────────────────────────────┐   │
│   │  Data Validation (Pydantic)      │   │
│   └──────────────┬───────────────────┘   │
│                  │                       │
│   ┌──────────────▼───────────────────┐   │
│   │   Google Sheets Storage          │   │
│   │   (gspread + Service Account)    │   │
│   └──────────────┬───────────────────┘   │
│                  │                       │
│   ┌──────────────▼───────────────────┐   │
│   │   AI Analysis (Hybrid)           │   │
│   │   ├─ Primary: Gemini AI          │   │
│   │   └─ Fallback: Math Model        │   │
│   └──────────────┬───────────────────┘   │
│                  │                       │
│   ┌──────────────▼───────────────────┐   │
│   │   Telegram Alert (if risk ≥50%)  │   │
│   │   (15-min cooldown per node)     │   │
│   └──────────────────────────────────┘   │
└──────────────────────────────────────────┘
    │
    ▼ GET /api/predict, /api/history
Next.js Web Dashboard
```

## 📁 Files

| File | Description |
|------|-------------|
| `main.py` | FastAPI application (Hybrid Edition) |
| `gemini_client.py` | Google Gemini AI client wrapper |
| `telegram_channel.py` | Telegram channel alert handler |
| `seeder.py` | Test data generation utility |
| `.env` | Environment variables (not in repo) |
| `.env.example` | Environment template |
| `credentials.json` | Google Service Account (not in repo) |

## 🔗 Related Documentation

- [AI Function Overview](../../README.md)
- [Main Project README](../../../README.md)
- [Web Application](../../../Web%20Application/README.md)
- [IoT Source Code](../../../IoT%20Source%20Code/README.md)
