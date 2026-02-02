# 🌊 Flood Detection Dashboard - Web Application

A modern Next.js 16 web dashboard for real-time flood and rain monitoring, integrated with the IoT Flood Detection System.

## ✨ Features

- **Real-time Monitoring** - Live sensor data from IoT nodes
- **Data Visualization** - Interactive charts with Recharts
- **User Authentication** - Secure login/signup with Supabase
- **Dark/Light Theme** - Toggle between themes
- **Responsive Design** - Works on desktop and mobile
- **Admin Dashboard** - Monitor nodes and system status
- **Telegram Bot Management** - Configure alert settings

## 🛠️ Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 16.0.5 | React framework (App Router) |
| React | 19.2.0 | UI library |
| Tailwind CSS | 4.x | Styling |
| Supabase | 2.86.0 | Authentication |
| Recharts | 2.15.4 | Data visualization |
| shadcn/ui | Latest | UI components |
| Lucide React | 0.555.0 | Icons |
| next-themes | 0.4.6 | Theme management |

## 📁 Project Structure

```
src/
├── app/
│   ├── (root)/              # Protected routes (requires auth)
│   │   ├── admin/           # Main dashboard
│   │   ├── bots/            # Telegram bot management
│   │   ├── settings/        # System settings
│   │   └── layout.js        # Sidebar layout
│   ├── api/                 # API routes
│   ├── auth/                # Auth pages
│   ├── login/               # Login page
│   ├── signup/              # Signup page
│   ├── middleware.js        # Auth middleware
│   ├── layout.js            # Root layout
│   └── page.js              # Home page
├── components/
│   ├── ui/                  # shadcn/ui components
│   │   ├── avatar.jsx
│   │   ├── badge.jsx
│   │   ├── button.jsx
│   │   ├── card.jsx
│   │   ├── chart.jsx
│   │   ├── dropdown-menu.jsx
│   │   ├── input.jsx
│   │   ├── label.jsx
│   │   ├── separator.jsx
│   │   ├── sheet.jsx
│   │   ├── sidebar.jsx
│   │   ├── skeleton.jsx
│   │   ├── switch.jsx
│   │   ├── tabs.jsx
│   │   ├── textarea.jsx
│   │   └── tooltip.jsx
│   ├── app-sidebar.jsx      # Navigation sidebar
│   ├── theme-provider.jsx   # Theme context
│   └── theme-toggle.jsx     # Dark/Light toggle
├── hooks/
│   └── use-mobile.js        # Mobile detection hook
├── lib/
│   └── utils.js             # Utility functions
└── utils/
    └── supabase/            # Supabase client config
```

## 📋 Prerequisites

- [Node.js](https://nodejs.org/) v18 or higher
- npm (comes with Node.js)
- Supabase account (for authentication)

## 🚀 Installation

1. **Navigate to the Web Application folder**
   ```bash
   cd "Web Application"
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   
   Create a `.env.local` file in the root folder:
   ```env
   # Supabase Configuration
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   
   # Backend API (FastAPI server)
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run the development server**
   ```bash
   npm run dev
   ```

5. **Open in browser**
   
   Go to [http://localhost:3000](http://localhost:3000)

## 📄 Pages

| Route | Description | Auth Required |
|-------|-------------|---------------|
| `/` | Home/Landing page | ❌ |
| `/login` | User login | ❌ |
| `/signup` | User registration | ❌ |
| `/admin` | Main dashboard | ✅ |
| `/bots` | Telegram bot settings | ✅ |
| `/settings` | System configuration | ✅ |

## 🎨 UI Components

This project uses [shadcn/ui](https://ui.shadcn.com/) components:

- **Button** - Various button styles
- **Card** - Content containers
- **Chart** - Recharts wrapper
- **Input/Label** - Form elements
- **Sidebar** - Navigation component
- **Tabs** - Tab navigation
- **Tooltip** - Hover tooltips
- **Badge** - Status indicators
- **Avatar** - User avatars
- **Switch** - Toggle switches
- **Sheet** - Slide-out panels

## ⚡ Quick Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server (port 3000) |
| `npm run build` | Build for production |
| `npm run start` | Run production build |
| `npm run lint` | Run ESLint |

## 🔗 API Integration

The dashboard connects to the FastAPI backend at `NEXT_PUBLIC_API_URL`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/sensor-data` | POST | Submit sensor data |
| `/api/predict` | POST | Get flood prediction |
| `/api/history` | GET | Get historical data |
| `/api/nodes` | GET | Get all nodes status |
| `/api/status/{node_id}` | GET | Get specific node |

## 🌙 Theme Support

The app supports dark and light themes using `next-themes`:

- Toggle via the theme button in the sidebar
- Persists user preference
- Follows system preference by default

## 🔐 Authentication Flow

1. User visits protected route (e.g., `/admin`)
2. Middleware checks for Supabase session
3. If no session, redirects to `/login`
4. After login, redirects back to original route

## 📱 Responsive Design

- **Desktop** - Full sidebar navigation
- **Tablet** - Collapsible sidebar
- **Mobile** - Sheet-based navigation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

Part of the ITT569 Group Assignment - Flood Detection and Rain Monitoring System
