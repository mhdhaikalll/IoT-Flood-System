# ITT569 Group Assignment

# Flood Detection and Rain Monitoring System

A comprehensive IoT-integrated system for real-time flood detection and rain monitoring, combining hardware sensors, AI-powered predictions, and a modern web dashboard.

## 📋 Project Overview

This project integrates multiple components to provide end-to-end flood monitoring:

```
┌─────────────┐     ┌─────────────────────────────────────────────────┐
│  IoT Nodes  │────▶│               FastAPI Backend                   │
│   (ESP32)   │     │  ┌─────────────┐  ┌──────────────────────────┐  │
└─────────────┘     │  │ Sensor Data │  │     AI Analysis          │  │
                    │  │  Endpoint   │  │  (Gemini / Ollama)       │  │
┌─────────────┐     │  └─────────────┘  └──────────────────────────┘  │
│   Next.js   │◀───▶│  ┌─────────────┐  ┌──────────────────────────┐  │
│  Dashboard  │     │  │ Prediction  │  │    Google Sheets         │  │
└─────────────┘     │  │   API       │  │    (Database)            │  │
                    │  └─────────────┘  └──────────────────────────┘  │
┌─────────────┐     └──────────────────────────┬──────────────────────┘
│  Telegram   │◀───────────────────────────────┘
│    Bot      │     (Real-time Alerts)
└─────────────┘
```

## 🗂️ Project Structure

```
.
├── AI Function/              # Backend API service
│   ├── ai-documentation/     # Business model and documentation
│   ├── data/                 # Data storage
│   └── src/                  # Python source code
│       ├── code/             # Main application code
│       │   ├── main.py       # FastAPI application entry point
│       │   ├── gemini_client.py  # Gemini AI integration
│       │   ├── telegram_bot.py   # Telegram notification bot
│       │   └── .env.example  # Environment template
│       └── requirements.txt  # Python dependencies
│
├── IoT Source Code/          # Arduino/IoT implementation
│   └── main.ino              # ESP32/ESP8266 sketch
│
└── Web Application/          # Next.js frontend
    ├── src/
    │   ├── app/              # Next.js App Router
    │   │   ├── (root)/       # Protected pages (admin, bots, settings)
    │   │   ├── api/          # API routes
    │   │   └── auth/         # Authentication pages
    │   ├── components/       # React components
    │   │   ├── ui/           # shadcn/ui components
    │   │   ├── app-sidebar.jsx
    │   │   └── theme-toggle.jsx
    │   ├── lib/
    │   │   ├── api.js        # Backend API client
    │   │   └── utils.js      # Utility functions
    │   └── utils/
    │       └── supabase/     # Supabase client
    ├── .env.example          # Environment template
    └── package.json          # Node.js dependencies
```

## 🚀 Components

### 1. AI Function (Backend)

**Technology Stack:**
- Python 3.x
- FastAPI - Modern async web framework
- Google Sheets API - Data storage
- Gemini AI - Flood prediction analysis
- Ollama - Optional local LLM support

**Key Features:**
- RESTful API endpoints for sensor data
- AI-powered flood risk prediction
- Google Sheets as database
- Real-time data processing
- Telegram bot integration

**Setup:**
```bash
cd "AI Function/src"
pip install -r requirements.txt

# Copy and configure environment
cp code/.env.example code/.env

# Run the server
python code/main.py
```

### 2. IoT Source Code

**Technology Stack:**
- ESP32 / ESP8266
- Arduino Framework
- WiFi HTTP Client

**Hardware Components:**
- Piezoelectric Sensor - Rain intensity detection
- Ultrasonic Sensor (HC-SR04) - Water level measurement
- Rain Sensor Module - Rain detection

**Key Features:**
- WiFi connectivity
- Automatic data transmission
- Retry logic for reliability
- Serial debugging

**Setup:**
1. Open `main.ino` in Arduino IDE
2. Install ESP32/ESP8266 board support
3. Configure WiFi credentials and server IP
4. Upload sketch to your device

### 3. Web Application

**Technology Stack:**
- Next.js 14+ (App Router)
- React
- Tailwind CSS
- Supabase - Authentication
- shadcn/ui - UI components
- Recharts - Data visualization

**Key Features:**
- Real-time flood monitoring dashboard
- Historical data charts
- User authentication
- Dark/Light theme toggle
- Responsive design
- Telegram bot management

**Setup:**
```bash
cd "Web Application"
npm install
cp .env.example .env.local
npm run dev
```

### 4. Telegram Bot

**Key Features:**
- Real-time flood alerts
- Query current sensor status
- Get flood predictions on demand
- Subscribe/unsubscribe to notifications

**Commands:**
- `/start` - Subscribe to alerts
- `/status` - Check system status
- `/predict` - Get flood prediction
- `/history` - View recent readings
- `/unsubscribe` - Stop notifications

**Setup:**
```bash
# Configure bot token in .env
TELEGRAM_BOT_TOKEN=your_token

# Run the bot
python code/telegram_bot.py
```

## 📦 Prerequisites

### AI Function
- Python 3.8 or higher
- pip package manager
- Google Cloud Platform account (for Sheets API)

### IoT Source Code
- Arduino IDE
- Compatible Arduino board
- Required sensors/hardware components

### Web Application
- Node.js 18+ 
- npm or yarn package manager
- Supabase account

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Group Assignment"
   ```

2. **Set up AI Function**
   ```bash
   cd "AI Function/src"
   pip install -r requirements.txt
   ```

3. **Set up Web Application**
   ```bash
   cd "Web Application"
   npm install
   ```

4. **Configure Arduino**
   - Open Arduino IDE
   - Load `IoT Source Code/main.ino`
   - Configure board settings

## ⚙️ Configuration

### AI Function
- Configure Google Sheets API credentials
- Set up OAuth authentication
- Update API endpoints in environment variables

### Web Application
- Create `.env.local` file
- Configure Supabase credentials:
  ```
  NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
  NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
  ```

### IoT Device
- Configure WiFi credentials (if applicable)
- Set API endpoint URLs
- Configure sensor pins

## 🏃 Running the Project

1. **Start the AI Backend**
   ```bash
   cd "AI Function/src"
   python code/main.py
   ```

2. **Start the Web Application**
   ```bash
   cd "Web Application"
   npm run dev
   ```

3. **Deploy IoT Code**
   - Upload Arduino sketch to your device
   - Monitor serial output for debugging

## 📚 Documentation

- **AI Function**: See `AI Function/src/code/README.md`
- **Business Model**: See `AI Function/ai-documentation/business-model.md`
- **Web Application**: See `Web Application/README.md`

## 🛠️ Development

### AI Function Development
- Virtual environment is configured in `src/`
- Main application code in `src/code/main.py`
- Dependencies managed via `requirements.txt`

### Web Application Development
- Use `npm run dev` for development server
- Components located in `src/components/`
- API routes in `src/app/api/`
- UI components use shadcn/ui library

### IoT Development
- Use Arduino IDE or PlatformIO
- Serial monitor for debugging
- Test sensors individually before integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

Please refer to the LICENSE file for details.

## 👥 Team

ITT569 - Group Assignment

## 📞 Support

For questions or issues, please contact the development team or create an issue in the repository.
