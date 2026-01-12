# Flood Detection and Rain Monitoring System - AI Function

This is the AI backend service for the Flood Detection and Rain Monitoring System. It receives data from IoT sensors, stores it in Google Sheets, and uses AI to predict flood risks.

## Features

- **Receive IoT Sensor Data**: Accepts data from nodes with Piezoelectric, Ultrasonic, and Rain sensors
- **Google Sheets Storage**: Stores all sensor data in Google Sheets as a database
- **AI-Powered Predictions**: Uses LLM to analyze trends and predict flood risks
- **RESTful API**: Provides endpoints for data ingestion and prediction retrieval

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

### 3. Configure LLM (Optional)

The system supports any OpenAI-compatible LLM API. Default is configured for Ollama.

**For Ollama:**
```bash
# Install Ollama and pull a model
ollama pull llama3.2
```

**For other LLMs:**
Update the `.env` file with your LLM API endpoint and model name.

### 4. Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

### 5. Run the Server

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

### Submit Sensor Data
```
POST /api/sensor-data
```
**Body:**
```json
{
    "node_id": "node_001",
    "piezo_value": 45.5,
    "ultrasonic_value": 35.0,
    "rain_sensor_value": 60.0,
    "location": "River Station A"
}
```

### Get Flood Prediction
```
POST /api/predict
```
**Body:**
```json
{
    "node_id": "node_001",
    "hours_ahead": 6
}
```

**Response:**
```json
{
    "node_id": "node_001",
    "current_water_level": 35.0,
    "current_rain_intensity": "moderate",
    "is_raining": true,
    "flood_risk": "moderate",
    "risk_percentage": 42.5,
    "prediction_summary": "Flood risk is MODERATE (42.5%). Water level: 35.0cm. Rain intensity: moderate.",
    "recommended_actions": [...],
    "ai_analysis": "...",
    "timestamp": "2026-01-11T10:30:00"
}
```

### Get Sensor History
```
GET /api/history?node_id=node_001&limit=50
```

### Get Node Status
```
GET /api/status/{node_id}
```

## Sensor Data Interpretation

| Sensor | Value Range | Meaning |
|--------|-------------|---------|
| Piezo | 0-100 | Rain intensity (0=none, 100=extreme) |
| Ultrasonic | 0+ cm | Water level in centimeters |
| Rain Sensor | 0-100 | Rain detection (0=dry, 100=heavy rain) |

## Flood Risk Levels

| Level | Risk % | Action |
|-------|--------|--------|
| LOW | 0-24% | Normal monitoring |
| MODERATE | 25-49% | Increased monitoring |
| HIGH | 50-74% | Prepare evacuation |
| CRITICAL | 75-100% | Immediate evacuation |

## Architecture

```
IoT Node (Sensors) 
    │
    ▼ POST /api/sensor-data
┌──────────────────────┐
│   FastAPI Server     │
│   ┌──────────────┐   │
│   │ Data Process │   │
│   └──────┬───────┘   │
│          │           │
│   ┌──────▼───────┐   │
│   │ Google Sheets│   │
│   │  (Database)  │   │
│   └──────┬───────┘   │
│          │           │
│   ┌──────▼───────┐   │
│   │  AI Analysis │   │
│   │    (LLM)     │   │
│   └──────────────┘   │
└──────────────────────┘
    │
    ▼ POST /api/predict
Web Application / Dashboard
```
