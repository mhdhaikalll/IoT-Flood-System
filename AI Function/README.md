# 🤖 AI Function - Flood Detection Backend

The AI-powered backend service for the Flood Detection and Rain Monitoring System. This FastAPI application processes IoT sensor data, performs flood risk predictions using Google Gemini AI, stores data in Google Sheets, and sends real-time alerts via Telegram.

## 🏗️ Architecture

```
AI Function/
├── README.md                 # This file
├── data/                     # Data storage directory
└── src/                      # Python virtual environment
    ├── pyvenv.cfg
    ├── requirements.txt      # Python dependencies
    └── code/                 # Source code
        ├── main.py           # FastAPI application (Hybrid Edition)
        ├── gemini_client.py  # Google Gemini AI integration
        ├── telegram_channel.py # Telegram alert service
        ├── seeder.py         # Test data generator
        ├── .env              # Environment variables
        ├── .env.example      # Environment template
        └── credentials.json  # Google Service Account
```

## 🚀 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | FastAPI | 0.113.0 |
| **AI Model** | Google Gemini | gemini-2.5-flash |
| **Data Validation** | Pydantic | 2.8.0 |
| **ASGI Server** | Uvicorn | 0.30.0 |
| **HTTP Client** | httpx | 0.28.1 |
| **Google Sheets** | gspread | 6.1.0 |
| **Authentication** | google-auth | 2.29.0 |
| **Environment** | python-dotenv | 1.0.0 |
| **Python** | Python | ≥3.8 |

## ⚙️ Setup & Installation

### 1. Navigate to Source Directory

```bash
cd "AI Function/src/code"
```

### 2. Create Virtual Environment (if not exists)

```bash
# Windows
python -m venv ../
../Scripts/activate

# Linux/macOS
python3 -m venv ../
source ../bin/activate
```

### 3. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `code/` directory:

```env
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS=credentials.json
SPREADSHEET_NAME=FloodData

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=-1001234567890
```

### 5. Set Up Google Sheets

1. Create a Google Cloud project
2. Enable Google Sheets API and Google Drive API
3. Create a Service Account and download `credentials.json`
4. Place `credentials.json` in the `code/` directory
5. Share your Google Sheet with the Service Account email

### 6. Run the Server

```bash
# Development
python main.py

# Production with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check and system status |
| `GET` | `/api/system-info` | Detailed system information |

### Sensor Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sensor-data` | Receive sensor data from IoT devices |
| `GET` | `/api/history` | Get historical sensor readings |
| `GET` | `/api/nodes` | List all registered IoT nodes |
| `GET` | `/api/status/{node_id}` | Get status of specific node |

### Predictions & Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/predict` | Get AI flood risk prediction |
| `GET` | `/api/analyze-all` | Analyze all nodes simultaneously |

### Testing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/test-telegram` | Test Telegram connection |
| `POST` | `/api/test-alert` | Trigger a test alert |

## 🎯 Flood Risk Thresholds

### Water Level Thresholds

| Level | Value (cm) | Status |
|-------|------------|--------|
| Normal | < 50 | ✅ Safe |
| Warning | 50 - 79 | ⚠️ Warning |
| Danger | ≥ 80 | 🚨 Danger |

### Rain Intensity Classification

| Intensity | Sensor Value | Description |
|-----------|--------------|-------------|
| None | ≥ 3000 | No rain detected |
| Light | 2000 - 2999 | Light drizzle |
| Moderate | 1000 - 1999 | Steady rain |
| Heavy | < 1000 | Heavy rainfall |

### Flood Risk Levels

| Risk Level | Probability | Alert Triggered |
|------------|-------------|-----------------|
| LOW | 0% - 24% | ❌ No |
| MODERATE | 25% - 49% | ❌ No |
| HIGH | 50% - 74% | ✅ Yes |
| CRITICAL | 75% - 100% | ✅ Yes |

## 🤖 Hybrid AI System

The backend uses a **Hybrid Edition** approach for flood predictions:

### Primary: Google Gemini AI
- Model: `gemini-2.5-flash`
- Provides intelligent analysis with contextual recommendations
- Considers historical patterns and environmental factors

### Fallback: Mathematical Model
- Activates when Gemini is unavailable
- Uses weighted algorithm based on:
  - Water level (40% weight)
  - Vibration/Piezo readings (30% weight)
  - Rain intensity (30% weight)

```python
# Fallback calculation formula
risk = (water_level_risk * 0.4) + (piezo_risk * 0.3) + (rain_risk * 0.3)
```

## 📱 Telegram Alerts

### Alert Configuration

- **Threshold**: Alerts triggered when risk ≥ 50% (HIGH or CRITICAL)
- **Cooldown**: 15 minutes between alerts per node
- **Format**: HTML formatted messages with emoji indicators

### Alert Message Format

```
🚨 FLOOD ALERT - HIGH RISK

📍 Location: Shah Alam, Selangor
🔢 Node: NODE-001

📊 Current Readings:
• Water Level: 75.5 cm ⚠️
• Vibration: 450 units
• Rain: Heavy (850)

🎯 Risk Assessment:
• Level: HIGH
• Probability: 68%

⏰ Time: 2024-01-15 14:30:45
```

## 📊 Google Sheets Schema

The sensor data is stored with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `data_id` | String | Unique record identifier |
| `node_id` | String | IoT node identifier |
| `piezo_value` | Float | Vibration sensor reading |
| `ultrasonic_value` | Float | Water level in cm |
| `rain_sensor_value` | Float | Rain sensor analog value |
| `location` | String | Node location description |
| `timestamp` | ISO8601 | Reading timestamp |

## 🧪 Testing Tools

### Seeder Script (`seeder.py`)

Generate test data for development:

```bash
# Test connection
python seeder.py connect

# Write single test reading
python seeder.py write

# Read last 10 readings
python seeder.py read

# Populate 7 days of data
python seeder.py populate

# Populate 30 days of data
python seeder.py populate30

# View statistics
python seeder.py stats

# Clear all data
python seeder.py clear

# Interactive menu
python seeder.py menu
```

### Telegram Test Script (`telegram_channel.py`)

```bash
python telegram_channel.py
```

## 🔌 Request/Response Examples

### POST `/api/sensor-data`

**Request:**
```json
{
  "node_id": "NODE-001",
  "piezo_value": 350.5,
  "ultrasonic_value": 45.2,
  "rain_sensor_value": 2500,
  "location": "Shah Alam, Selangor",
  "timestamp": "2024-01-15T10:30:00"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sensor data stored successfully",
  "data_id": "NODE-001_20240115103000",
  "timestamp": "2024-01-15T10:30:00",
  "prediction": {
    "flood_risk": "LOW",
    "probability": 15,
    "rain_intensity": "LIGHT",
    "water_level_status": "NORMAL"
  }
}
```

### POST `/api/predict`

**Request:**
```json
{
  "node_id": "NODE-001"
}
```

**Response:**
```json
{
  "success": true,
  "node_id": "NODE-001",
  "flood_risk": "MODERATE",
  "probability": 35,
  "rain_intensity": "MODERATE",
  "water_level_status": "NORMAL",
  "recommendations": [
    "Continue monitoring water levels",
    "Ensure drainage systems are clear"
  ],
  "analysis_source": "gemini",
  "timestamp": "2024-01-15T14:30:00"
}
```

## 📁 File Descriptions

| File | Lines | Description |
|------|-------|-------------|
| `main.py` | ~1600 | Core FastAPI application - Hybrid Edition |
| `gemini_client.py` | ~370 | Google Gemini AI client wrapper |
| `telegram_channel.py` | ~230 | Telegram channel alert handler |
| `seeder.py` | ~490 | Test data generation utility |

## 🐛 Troubleshooting

### Google Sheets Connection Failed

```
❌ Credentials file not found
```
**Solution:** Ensure `credentials.json` is in the `code/` directory

### Gemini API Errors

```
[GEMINI] API Error: 403 Forbidden
```
**Solution:** Verify `GEMINI_API_KEY` in `.env` is valid

### Telegram Not Sending

```
[TELEGRAM] Send failed: Chat not found
```
**Solution:** Verify `TELEGRAM_CHANNEL_ID` is correct (include `-100` prefix for channels)

## 📚 Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Gemini API](https://ai.google.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## 👥 ITT569 - IoT System Development

**Group Assignment** - Flood Detection and Rain Monitoring System

---

*Backend service for real-time flood monitoring and AI-powered predictions.*
