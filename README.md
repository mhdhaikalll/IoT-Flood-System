# ITT569 Group Assignment

# 🌊 Flood Detection and Rain Monitoring System

A comprehensive IoT-integrated system for real-time flood detection and rain monitoring, combining hardware sensors, AI-powered predictions, and a modern web dashboard with Telegram alerts.

## 📋 Project Overview

This project integrates multiple components to provide end-to-end flood monitoring:

```
┌──────────────────┐     ┌───────────────────────────────────────────────────┐
│   IoT Node       │────▶│              FastAPI Backend                      │
│   (ESP32)        │     │  ┌─────────────┐  ┌────────────────────────────┐  │
│ - Piezo Sensor   │     │  │ Sensor Data │  │     AI Analysis            │  │
│ - Ultrasonic     │     │  │  Endpoint   │  │  (Gemini AI / Fallback)    │  │
│ - Rain Sensor    │     │  └─────────────┘  └────────────────────────────┘  │
│ - LCD Display    │     │  ┌─────────────┐  ┌────────────────────────────┐  │
│ - RGB LEDs       │     │  │ Prediction  │  │    Google Sheets           │  │
└──────────────────┘     │  │    API      │  │    (Database)              │  │
                         │  └─────────────┘  └────────────────────────────┘  │
┌──────────────────┐     └──────────────────────────┬────────────────────────┘
│   Next.js 16     │◀──────────────────────────────▶│
│   Dashboard      │                                │
│ - Real-time Data │     ┌──────────────────────────▼────────────────────────┐
│ - Charts         │     │              Telegram Channel                     │
│ - Admin Panel    │     │         (Automated Flood Alerts)                  │
│ - Auth (Supabase)│     └───────────────────────────────────────────────────┘
└──────────────────┘
```

## 🗂️ Project Structure

```
.
├── AI Function/                    # Backend API service
│   ├── ai-documentation/           # Business model documentation
│   ├── data/                       # Data storage
│   └── src/                        # Python source code
│       ├── code/
│       │   ├── main.py             # FastAPI application (Hybrid Edition)
│       │   ├── gemini_client.py    # Gemini AI integration
│       │   ├── telegram_channel.py # Telegram channel alerts
│       │   ├── seeder.py           # Database seeder utility
│       │   ├── credentials.json    # Google Service Account (not in repo)
│       │   └── .env.example        # Environment template
│       └── requirements.txt        # Python dependencies
│
├── IoT Source Code/                # Arduino/ESP32 implementation
│   └── main.ino                    # ESP32 sketch with LCD & LED support
│
└── Web Application/                # Next.js 16 frontend
    ├── src/
    │   ├── app/
    │   │   ├── (root)/             # Protected pages
    │   │   │   ├── admin/          # Admin dashboard
    │   │   │   ├── bots/           # Telegram bot management
    │   │   │   └── settings/       # System settings
    │   │   ├── api/                # API routes
    │   │   └── auth/               # Login/Signup pages
    │   ├── components/
    │   │   ├── ui/                 # shadcn/ui components
    │   │   ├── app-sidebar.jsx     # Navigation sidebar
    │   │   └── theme-toggle.jsx    # Dark/Light mode toggle
    │   └── utils/
    │       └── supabase/           # Supabase auth client
    └── package.json                # Node.js dependencies
```

## 🚀 Components

### 1. AI Function (Backend)

**Technology Stack:**
- Python 3.8+
- FastAPI - Modern async web framework
- Google Sheets API - Data storage (via gspread)
- Gemini AI (gemini-2.5-flash) - Flood prediction analysis
- Telegram Bot API - Automated channel alerts
- httpx - Async HTTP client

**Key Features:**
- RESTful API endpoints for sensor data ingestion
- AI-powered flood risk prediction with Gemini
- Mathematical fallback when AI is unavailable
- Google Sheets as persistent database
- Automated Telegram alerts for HIGH/CRITICAL risk
- Real-time node status monitoring (online/idle/offline)
- 15-minute alert cooldown to prevent spam

**API Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check & service status |
| `/api/sensor-data` | POST | Receive IoT sensor data (triggers alerts) |
| `/api/predict` | POST | Get AI flood prediction |
| `/api/history` | GET | Retrieve historical sensor data |
| `/api/nodes` | GET | Get all nodes status |
| `/api/status/{node_id}` | GET | Get specific node status |

**Setup:**
```bash
cd "AI Function/src"
pip install -r requirements.txt

# Configure environment
cp code/.env.example code/.env
# Edit .env with your credentials

# Run the server
cd code
python main.py
```

---

### 2. IoT Source Code (ESP32)

**Technology Stack:**
- ESP32 / ESP8266 Microcontroller
- Arduino Framework
- WiFi HTTP Client
- LiquidCrystal_I2C Library

**Hardware Components:**
| Component | Pin | Description |
|-----------|-----|-------------|
| Piezoelectric Sensor | GPIO34 (ADC) | Rain intensity detection |
| Ultrasonic HC-SR04 (Trig) | GPIO5 | Water level trigger |
| Ultrasonic HC-SR04 (Echo) | GPIO18 | Water level echo |
| Rain Sensor Module | GPIO35 (ADC) | Rain detection |
| Green LED | GPIO25 | Safe/Low risk indicator |
| Yellow LED | GPIO26 | Warning/Moderate risk indicator |
| Red LED | GPIO27 | Danger/High-Critical risk indicator |
| LCD I2C (SDA) | GPIO21 | Display data |
| LCD I2C (SCL) | GPIO22 | Display clock |

**Key Features:**
- WiFi connectivity with auto-reconnect
- LCD 16x2 display with custom characters
- Traffic light LED alert system (Green/Yellow/Red)
- Multiple display modes (cycle through water level, rain, status)
- Automatic data transmission every 30 seconds
- Retry logic for reliable communication
- Alert levels: LOW, MODERATE, HIGH, CRITICAL

**Alert Thresholds:**
| Level | Water Level | Rain Intensity | LED Color |
|-------|-------------|----------------|-----------|
| LOW | < 30 cm | < 40% | 🟢 Green |
| MODERATE | 30-50 cm | 40-70% | 🟡 Yellow |
| HIGH | 50-80 cm | 70-90% | 🔴 Red |
| CRITICAL | > 80 cm | > 90% | 🔴 Red (Blinking) |

**Setup:**
1. Open `main.ino` in Arduino IDE
2. Install required libraries:
   - `LiquidCrystal_I2C`
   - `WiFi` (ESP32) or `ESP8266WiFi`
3. Configure WiFi credentials and API URL:
   ```cpp
   const char* WIFI_SSID = "YOUR_WIFI_SSID";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
   const char* API_URL = "http://YOUR_SERVER_IP:8000/api/sensor-data";
   ```
4. Upload sketch to ESP32

---

### 3. Web Application (Dashboard)

**Technology Stack:**
- Next.js 16 (App Router)
- React 19
- Tailwind CSS 4
- Supabase - Authentication
- shadcn/ui - UI components
- Recharts - Data visualization
- Lucide React - Icons

**Key Features:**
- Real-time flood monitoring dashboard
- Historical data visualization with charts
- User authentication (Login/Signup)
- Protected admin routes
- Dark/Light theme toggle
- Responsive sidebar navigation
- Telegram bot management page
- System settings configuration

**Pages:**
| Route | Description |
|-------|-------------|
| `/auth/login` | User login |
| `/auth/signup` | User registration |
| `/admin` | Main dashboard |
| `/bots` | Telegram bot management |
| `/settings` | System settings |

**Setup:**
```bash
cd "Web Application"
npm install

# Configure environment
cp .env.example .env.local
# Add Supabase credentials

npm run dev
```

---

### 4. Telegram Alerts

**Key Features:**
- Automated flood alerts to Telegram channel
- Triggered when flood risk is HIGH or CRITICAL (≥50%)
- 15-minute cooldown per node to prevent spam
- Rich HTML formatted messages with:
  - Node ID and location
  - Water level and rain intensity
  - Risk level percentage
  - Recommended actions
  - Timestamp

**Alert Message Format:**
```
🚨 FLOOD ALERT 🚨

📍 Node: NODE-001
📌 Location: Test Location
💧 Water Level: 85.0 cm
🌧️ Rain Intensity: extreme

Risk Level: CRITICAL (92.5%)

Immediate Actions:
• IMMEDIATE EVACUATION REQUIRED
• Emergency services on high alert
• All residents must move to higher ground

⏰ Alert Time: 2026-02-03 14:30:00
Stay safe and follow local authority guidelines!
```

**Setup:**
1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Create a Telegram channel
3. Add the bot as admin to the channel
4. Get channel ID (format: `-100xxxxxxxxxx`)
5. Configure in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHANNEL_ID=-100xxxxxxxxxx
   ```

---

## 📦 Prerequisites

| Component | Requirement |
|-----------|-------------|
| AI Function | Python 3.8+, pip, Google Cloud account |
| IoT Source Code | Arduino IDE, ESP32 board, Required sensors |
| Web Application | Node.js 18+, npm, Supabase account |

## 🔧 Quick Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mhdhaikalll/IoT-Flood-System.git
   cd "Group Assignment"
   ```

2. **Set up AI Function**
   ```bash
   cd "AI Function/src"
   pip install -r requirements.txt
   cp code/.env.example code/.env
   # Configure .env with your credentials
   ```

3. **Set up Web Application**
   ```bash
   cd "Web Application"
   npm install
   cp .env.example .env.local
   # Configure Supabase credentials
   ```

4. **Configure IoT Device**
   - Open `IoT Source Code/main.ino` in Arduino IDE
   - Update WiFi and API configuration
   - Upload to ESP32

## ⚙️ Environment Variables

### AI Function (.env)
```env
# Google Sheets
GOOGLE_SHEETS_CREDENTIALS=credentials.json
SPREADSHEET_NAME=FloodMonitoringData

# AI Provider
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=-100xxxxxxxxxx

# Frontend CORS
FRONTEND_URL=http://localhost:3000
```

### Web Application (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🏃 Running the Project

1. **Start the AI Backend**
   ```bash
   cd "AI Function/src/code"
   python main.py
   # Server runs on http://localhost:8000
   ```

2. **Start the Web Application**
   ```bash
   cd "Web Application"
   npm run dev
   # Dashboard runs on http://localhost:3000
   ```

3. **Deploy IoT Device**
   - Power on ESP32 with uploaded sketch
   - Monitor serial output for debugging
   - Verify data transmission in backend logs

## 📊 Flood Risk Levels

| Level | Risk % | Water Level | Action |
|-------|--------|-------------|--------|
| 🟢 LOW | 0-24% | < 30 cm | Normal monitoring |
| 🟡 MODERATE | 25-49% | 30-50 cm | Increased monitoring |
| 🟠 HIGH | 50-74% | 50-80 cm | Prepare evacuation |
| 🔴 CRITICAL | 75-100% | > 80 cm | **Immediate evacuation** |

## 📚 Documentation

- **AI Function**: See `AI Function/src/code/README.md`
- **Business Model**: See `AI Function/ai-documentation/business-model.md`
- **Web Application**: See `Web Application/README.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Please refer to the LICENSE file for details.

## 👥 Team

**ITT569 - Group Assignment**  
Flood Detection and Rain Monitoring System

## 📞 Support

For questions or issues, please create an issue in the [GitHub repository](https://github.com/mhdhaikalll/IoT-Flood-System/issues).
