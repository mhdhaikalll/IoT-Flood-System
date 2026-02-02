# 🌊 Flood Detection IoT Node

ESP32/ESP8266-based IoT sensor node for real-time flood detection and rain monitoring. Sends sensor data to FastAPI backend via WiFi.

## ✨ Features

- **Multi-Sensor Support** - Piezoelectric, Ultrasonic, and Rain sensors
- **LCD Display** - 16x2 I2C display with custom characters
- **Traffic Light LEDs** - Green/Yellow/Red alert system
- **WiFi Connectivity** - Auto-connect with retry logic
- **Real-time Monitoring** - Continuous sensor readings
- **Backend Integration** - Sends JSON data to FastAPI server

## 🛠️ Hardware Components

| Component | Model | Purpose |
|-----------|-------|---------|
| Microcontroller | ESP32 / ESP8266 | Main controller with WiFi |
| Piezoelectric Sensor | - | Rain intensity detection |
| Ultrasonic Sensor | HC-SR04 | Water level measurement |
| Rain Sensor | Rain Module | Rain detection |
| LCD Display | 16x2 I2C | Visual feedback |
| Green LED | 5mm | Safe/Low risk indicator |
| Yellow LED | 5mm | Warning/Moderate risk |
| Red LED | 5mm | Danger/High-Critical risk |

## 📌 Pin Configuration (ESP32)

### Sensors
| Component | Pin | GPIO | Notes |
|-----------|-----|------|-------|
| Piezoelectric Sensor | ADC | GPIO34 | Analog input |
| Ultrasonic Trigger | Digital | GPIO5 | Output |
| Ultrasonic Echo | Digital | GPIO18 | Input |
| Rain Sensor | ADC | GPIO35 | Analog input |

### LEDs (Traffic Light System)
| LED | GPIO | Alert Level |
|-----|------|-------------|
| 🟢 Green | GPIO25 | LOW (Safe) |
| 🟡 Yellow | GPIO26 | MODERATE (Caution) |
| 🔴 Red | GPIO27 | HIGH/CRITICAL (Danger) |

### LCD I2C
| Pin | GPIO |
|-----|------|
| SDA | GPIO21 |
| SCL | GPIO22 |
| Address | 0x27 |

## 🚨 Alert Levels

| Level | Water Level | Rain Intensity | LED | Action |
|-------|-------------|----------------|-----|--------|
| LOW | < 30 cm | < 40% | 🟢 Green | Normal monitoring |
| MODERATE | 30-50 cm | 40-70% | 🟡 Yellow | Increased alert |
| HIGH | 50-80 cm | 70-90% | 🔴 Red | Warning state |
| CRITICAL | > 80 cm | > 90% | 🔴 Red (Blinking) | Emergency! |

## 📋 Prerequisites

### Software
- [Arduino IDE](https://www.arduino.cc/en/software) 2.x or later
- ESP32 Board Support Package
- Required Libraries (see below)

### Libraries to Install
1. **LiquidCrystal_I2C** - LCD display driver
2. **WiFi** (ESP32) or **ESP8266WiFi** (ESP8266)
3. **HTTPClient** (ESP32) or **ESP8266HTTPClient** (ESP8266)

### Install ESP32 Board Support
1. Open Arduino IDE
2. Go to **File → Preferences**
3. Add to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Go to **Tools → Board → Board Manager**
5. Search "ESP32" and install

## 🚀 Installation

### 1. Open the Sketch
```bash
# Navigate to folder and open in Arduino IDE
Arduino IDE → File → Open → main.ino
```

### 2. Configure WiFi Credentials
Edit lines 30-31 in `main.ino`:
```cpp
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
```

### 3. Configure Backend API
Edit lines 34-36 in `main.ino`:
```cpp
const char* API_URL = "http://YOUR_SERVER_IP:8000/api/sensor-data";
const char* NODE_ID = "node_001";
const char* LOCATION = "your_location";
```

### 4. Select Board
- **Tools → Board → ESP32 Arduino → ESP32 Dev Module** (or your specific board)

### 5. Select Port
- **Tools → Port → COMx** (Windows) or **/dev/ttyUSBx** (Linux/Mac)

### 6. Upload
- Click **Upload** button (→) or press **Ctrl+U**

## 📊 Wiring Diagram

```
                    ESP32
                 ┌─────────┐
                 │         │
    Piezo ───────┤ GPIO34  │
                 │         │
    HC-SR04 ─────┤ GPIO5   │──── Trigger
         ────────┤ GPIO18  │──── Echo
                 │         │
    Rain ────────┤ GPIO35  │
                 │         │
    Green LED ───┤ GPIO25  │
    Yellow LED ──┤ GPIO26  │
    Red LED ─────┤ GPIO27  │
                 │         │
    LCD SDA ─────┤ GPIO21  │
    LCD SCL ─────┤ GPIO22  │
                 │         │
                 └─────────┘
```

## 📱 LCD Display Modes

The LCD cycles through 4 display modes every 2 seconds:

| Mode | Display |
|------|---------|
| 1 | 💧 Water Level + Alert Status |
| 2 | 🌧️ Rain Intensity + Level |
| 3 | Combined Status (W/R) + WiFi |
| 4 | Node ID + IP Address |

### Custom LCD Characters
- 💧 Droplet - Rain indicator
- 🌊 Wave - Water level indicator  
- ⚠️ Warning - Alert indicator

## 📡 Data Transmission

### JSON Payload Format
```json
{
  "node_id": "node_001",
  "piezo_value": 45.50,
  "ultrasonic_value": 35.00,
  "rain_sensor_value": 60.00,
  "location": "default_location"
}
```

### Timing
| Setting | Value | Purpose |
|---------|-------|---------|
| `SEND_INTERVAL` | 30 seconds | Data transmission frequency |
| `LCD_UPDATE_INTERVAL` | 2 seconds | Display refresh rate |
| `RETRY_DELAY` | 5 seconds | Retry wait time |
| `MAX_RETRIES` | 3 | Maximum send attempts |

## 🔧 Configuration Options

### Thresholds (Adjustable)
```cpp
// Alert thresholds
const float WATER_LEVEL_WARNING = 50.0;  // cm - Yellow LED
const float WATER_LEVEL_DANGER = 80.0;   // cm - Red LED
const float RAIN_INTENSITY_HIGH = 70.0;  // % - High rain

// Calibration
const float WATER_LEVEL_MAX = 400.0;     // Maximum sensor range (cm)
const int SENSOR_MAX = 4095;             // ESP32 12-bit ADC max
```

### Timing (Adjustable)
```cpp
const unsigned long SEND_INTERVAL = 30000;       // 30 seconds
const unsigned long LCD_UPDATE_INTERVAL = 2000;  // 2 seconds
const unsigned long RETRY_DELAY = 5000;          // 5 seconds
const int MAX_RETRIES = 3;
```

## 🖥️ Serial Monitor

Open Serial Monitor at **115200 baud** to see debug output:

```
=================================
Flood Detection IoT Node
=================================
Node ID: node_001
Location: default_location

LCD initialized
LEDs initialized
Sensors initialized
Connecting to WiFi: YOUR_SSID
.....
WiFi connected!
IP address: 192.168.1.100
Setup complete. Starting main loop...

--- Sensor Readings ---
Piezo (Rain Intensity): 25.50%
Ultrasonic (Water Level): 15.30 cm
Rain Sensor: 30.20%
Alert Level: SAFE
Data sent successfully!
```

## ❗ Troubleshooting

| Issue | Solution |
|-------|----------|
| LCD not displaying | Check I2C address (try 0x3F), verify SDA/SCL connections |
| WiFi not connecting | Verify SSID/password, check router range |
| Sensors reading 0 | Check wiring, verify pin assignments |
| HTTP error | Ensure backend server is running, check API_URL |
| Upload failed | Select correct board/port, press BOOT button during upload |

### Common I2C Addresses for LCD
- `0x27` (most common)
- `0x3F` (alternative)

Run I2C scanner sketch to find your LCD address.

## 📄 License

Part of the ITT569 Group Assignment - Flood Detection and Rain Monitoring System