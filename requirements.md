# Flood Detection and Rain Monitoring System

This is a project for the subject ITT569: Internet of Things (IoT)

---

## Tech Stack

1. AI Function
    - Python
    - FastAPI
    - Gemini API            (Perform prediction analysis)
    - Google Sheets API     (Database and Dataset collection)
    - Telegram Bot API      (Send Notification Alert)

2. IoT Source Code
    - ESP32 Microcontroller
    - Piezoelectronic Sensor (Detect Rain Intensity)
    - Ultrasonic Sensor      (Detect Water Level)
    - Rain Sensor            (Detect Rain)
    - LCD Screen             (Display Messages)
    - LEDs (in three different colors)

3. Web Application
    - Next.js (14)
    - Supabase Auth
    - Telegram Bot API (Configuration Settings)

---

## Briefing

This system consist of three (3) parts.

- AI Function
    [x] API Integration: Receive and parse incoming telemetry data from IoT nodes via FastAPI endpoints.
    [x] Predictive Analysis: Utilize the Gemini API to analyze rainfall intensity and water level trends to predict potential flooding before it occurs.
    [x] Data Logging: Automate data entry into Google Sheets to maintain a historical dataset for future trend analysis.
    [x] Automated Alerting: Trigger the Telegram Bot API to send instant emergency notifications to stakeholders when high-risk patterns are detected.

---

- IoT Source Code
    [x] Sensor Fusion: Aggregate real-time data from the ultrasonic sensor (water level) and piezoelectronic / rain sensor (rainfall volume and intensity).
    [x] Local Visual Feedback: Update the LCD Screen with current sensor readings and system status for on-site monitoring.
    [x] Tri-Color Alert System: Drive LEDs (Green/Yellow/Red) to provide an immediate, visual "Traffic Light" warning system based on current danger levels.
    [x] Data Transmission: Establish a Wi-Fi connection via the ESP32 to POST sensor payloads to the FastAPI backend at regular intervals.

---

- Web Application
    [x] Centralized Dashboard: Build a responsive UI using Next.js to visualize live sensor data and AI flood predictions.
    [x] Secure Access: Implement Supabase Auth to ensure only authorized personnel can access the monitoring dashboard and systems configurations.
    [x] Data Visualization: Preset historical flood data and rainfall trends using interactive charts.
    [x] System Health Monitoring: Provide a status overview to confirm if the IoT nodes are online and transmitting data directly