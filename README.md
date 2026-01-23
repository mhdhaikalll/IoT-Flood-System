# ITT569 Group Assignment

A comprehensive IoT-integrated system combining hardware sensors, AI-powered backend services, and a modern web application.

## 📋 Project Overview

This project integrates three main components:
- **IoT Device**: Arduino-based hardware for sensor data collection
- **AI Function**: FastAPI backend with AI capabilities and Google Sheets integration
- **Web Application**: Next.js frontend with authentication and real-time features

## 🗂️ Project Structure

```
.
├── AI Function/              # Backend API service
│   ├── ai-documentation/     # Business model and documentation
│   ├── data/                 # Data storage
│   └── src/                  # Python source code
│       ├── code/             # Main application code
│       │   ├── main.py       # FastAPI application entry point
│       │   └── README.md     # AI Function documentation
│       └── requirements.txt  # Python dependencies
│
├── IoT Source Code/          # Arduino/IoT implementation
│   └── main.ino              # Arduino sketch
│
└── Web Application/          # Next.js frontend
    ├── src/
    │   ├── app/              # Next.js App Router
    │   │   ├── (root)/       # Root pages
    │   │   ├── api/          # API routes
    │   │   └── auth/         # Authentication pages
    │   ├── components/       # React components
    │   │   ├── ui/           # UI components
    │   │   ├── app-sidebar.jsx
    │   │   └── theme-toggle.jsx
    │   ├── hooks/            # Custom React hooks
    │   ├── lib/              # Utility libraries
    │   └── utils/
    │       └── supabase/     # Supabase integration
    ├── public/               # Static assets
    ├── package.json          # Node.js dependencies
    └── next.config.mjs       # Next.js configuration
```

## 🚀 Components

### 1. AI Function (Backend)

**Technology Stack:**
- Python 3.x
- FastAPI - Modern web framework
- Google Sheets API - Data integration
- Google Auth - Authentication
- Email Validator - Input validation

**Key Features:**
- RESTful API endpoints
- Google Sheets integration for data storage
- OAuth authentication
- Real-time data processing

**Setup:**
```bash
cd "AI Function/src"
pip install -r requirements.txt
python code/main.py
```

### 2. IoT Source Code

**Technology Stack:**
- Arduino
- Embedded C/C++

**Key Features:**
- Sensor data collection
- Hardware interface
- Data transmission to backend

**Setup:**
1. Open `main.ino` in Arduino IDE
2. Configure board and port settings
3. Upload sketch to your Arduino device

### 3. Web Application

**Technology Stack:**
- Next.js 14+ (App Router)
- React
- Tailwind CSS
- Supabase - Backend services
- shadcn/ui - UI components

**Key Features:**
- Modern responsive UI
- Authentication system
- Dark/Light theme toggle
- Sidebar navigation
- API integration
- Real-time updates

**Setup:**
```bash
cd "Web Application"
npm install
npm run dev
```

The application will be available at `http://localhost:3000`

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
