# Flood Detection and Rain Monitoring System - AI Function

This is the AI backend service for the Flood Detection and Rain Monitoring System. It receives data from IoT sensors, stores it in Google Sheets, uses AI to predict flood risks, and sends Telegram alerts for high/critical risk.

## Features

- **Receive IoT Sensor Data**: Accepts data from a single node with Piezoelectric, Ultrasonic, and Rain sensors
- **Google Sheets Storage**: Stores all sensor data in Google Sheets as a database
- **AI-Powered Predictions**: Uses LLM (Gemini or OpenAI-compatible) to analyze trends and predict flood risks
- **Telegram Alerts**: Sends automated alerts to a Telegram channel when flood risk is high or critical
- **RESTful API**: Provides endpoints for data ingestion, prediction, and status

## Setup

### 1. Install Dependencies

```bash
cd src
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
2. Add the bot to your Telegram channel and make it an **admin**
3. Get your channel ID (e.g., `-100xxxxxxxxxx`)
4. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` in your `.env` file

### 4. Configure LLM (Optional)

The system supports any OpenAI-compatible LLM API. Default is configured for Gemini or Ollama.

**For Gemini:**
- Set `AI_PROVIDER=gemini` in `.env` (default)

### 5. Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
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

## API Endpoints

### Health Check

```
GET /
```
Returns system status and service availability.

### Submit Sensor Data (Triggers Telegram alert if risk is high/critical)

```
POST /api/sensor-data
```

**Body:**
```json
{
    "node_id": "NODE-001",
    "piezo_value": 90.0,
    "ultrasonic_value": 90.0,
    "rain_sensor_value": 90.0,
    "location": "Test Location"
}
```

### Get Flood Prediction

```
POST /api/predict
```

**Body:**

```json
{
    "node_id": "NODE-001",
    "hours_ahead": 6
}
```

**Response:**

```json
{
    "node_id": "NODE-001",
    "current_water_level": 90.0,
    "current_rain_intensity": "extreme",
    "is_raining": true,
    "flood_risk": "critical",
    "risk_percentage": 100.0,
    "prediction_summary": "Flood risk is CRITICAL (100.0%). Water level: 90.0cm. Rain intensity: extreme.",
    "recommended_actions": [...],
    "ai_analysis": "...",
    "timestamp": "2026-01-28T10:30:00"
}
```

### Get Sensor History

```
GET /api/history?node_id=NODE-001&limit=50
```

### Get Node Status

```
GET /api/status/NODE-001
```

### Get All Nodes Status

```
GET /api/nodes
```

## Sensor Data Interpretation

| Sensor      | Value Range | Meaning                                 |
|-------------|-------------|-----------------------------------------|
| Piezo       | 0-100       | Rain intensity (0=none, 100=extreme)    |
| Ultrasonic  | 0+ cm       | Water level in centimeters              |
| Rain Sensor | 0-100       | Rain detection (0=dry, 100=heavy rain)  |

## Flood Risk Levels

| Level     | Risk % | Action                  |
|-----------|--------|-------------------------|
| LOW       | 0-24%  | Normal monitoring       |
| MODERATE  | 25-49% | Increased monitoring    |
| HIGH      | 50-74% | Prepare evacuation      |
| CRITICAL  | 75-100%| Immediate evacuation    |

## Telegram Alert Logic

- Alerts are sent to the configured Telegram channel when:
  - Flood risk is HIGH or CRITICAL
  - Risk percentage is 50% or above
  - Cooldown period (15 min) has passed for the node

## Architecture

```
IoT Node (Sensors)
    │
    ▼ POST /api/sensor-data
┌──────────────────────────────┐
│   FastAPI Server (main.py)   │
│   ┌──────────────────────┐   │
│   │ Data Processing      │   │
│   └─────────┬────────────┘   │
│             │                │
│   ┌─────────▼────────────┐   │
│   │ Google Sheets (DB)   │   │
│   └─────────┬────────────┘   │
│             │                │
│   ┌─────────▼────────────┐   │
│   │  AI Analysis (LLM)   │   │
│   └─────────┬────────────┘   │
│             │                │
│   ┌─────────▼────────────┐   │
│   │ Telegram Alert       │   │
│   └──────────────────────┘   │
└──────────────────────────────┘
    │
    ▼ POST /api/predict
Web Application / Dashboard
```
