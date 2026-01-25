/**
 * Flood Detection and Rain Monitoring System - IoT Node
 * 
 * Hardware Components:
 * - ESP32/ESP8266 Microcontroller
 * - Piezoelectric Sensor (Rain intensity)
 * - Ultrasonic Sensor HC-SR04 (Water level)
 * - Rain Sensor Module (Rain detection)
 * - LCD I2C Display 16x2 (Visual feedback)
 * - LEDs: Green, Yellow, Red (Alert system)
 * 
 * Communication: WiFi -> FastAPI Backend
 */

#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#ifdef ESP32
  #include <WiFi.h>
  #include <HTTPClient.h>
#else
  #include <ESP8266WiFi.h>
  #include <ESP8266HTTPClient.h>
#endif

// ============== CONFIGURATION ==============

// WiFi Configuration
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Backend API Configuration
const char* API_URL = "http://YOUR_SERVER_IP:8000/api/sensor-data";
const char* NODE_ID = "node_001";
const char* LOCATION = "default_location";

// Sensor Pins
#define PIEZO_PIN 34              // GPIO34 (ADC) for piezoelectric sensor
#define ULTRASONIC_TRIG_PIN 5     // GPIO5 for ultrasonic trigger
#define ULTRASONIC_ECHO_PIN 18    // GPIO18 for ultrasonic echo
#define RAIN_SENSOR_PIN 35        // GPIO35 (ADC) for rain sensor

// LED Pins (Traffic Light Alert System)
#define LED_GREEN_PIN 25          // GPIO25 - Safe/Low risk
#define LED_YELLOW_PIN 26         // GPIO26 - Warning/Moderate risk
#define LED_RED_PIN 27            // GPIO27 - Danger/High-Critical risk

// LCD Configuration (I2C)
#define LCD_ADDRESS 0x27          // Common I2C address for LCD
#define LCD_COLUMNS 16
#define LCD_ROWS 2

// I2C Pins (ESP32 default)
#define I2C_SDA 21
#define I2C_SCL 22

// Timing Configuration
const unsigned long SEND_INTERVAL = 30000;  // Send data every 30 seconds
const unsigned long LCD_UPDATE_INTERVAL = 2000;  // Update LCD every 2 seconds
const unsigned long RETRY_DELAY = 5000;     // Retry connection every 5 seconds
const int MAX_RETRIES = 3;                  // Maximum connection retries

// Alert Thresholds
const float WATER_LEVEL_WARNING = 50.0;     // cm - Yellow LED
const float WATER_LEVEL_DANGER = 80.0;      // cm - Red LED
const float RAIN_INTENSITY_HIGH = 70.0;     // % - Contributes to alert level

// Calibration Values
const float WATER_LEVEL_MAX = 400.0;        // Maximum distance in cm
const int SENSOR_MIN = 0;
const int SENSOR_MAX = 4095;                // ESP32 12-bit ADC

// ============== GLOBAL VARIABLES ==============

LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLUMNS, LCD_ROWS);

unsigned long lastSendTime = 0;
unsigned long lastLcdUpdate = 0;
bool wifiConnected = false;
int displayMode = 0;  // Cycle through different display modes

// Alert levels
enum AlertLevel {
  ALERT_LOW,      // Green
  ALERT_MODERATE, // Yellow
  ALERT_HIGH,     // Red
  ALERT_CRITICAL  // Red blinking
};

AlertLevel currentAlert = ALERT_LOW;

// ============== LCD CUSTOM CHARACTERS ==============

byte dropletChar[8] = {
  0b00100,
  0b00100,
  0b01110,
  0b01110,
  0b11111,
  0b11111,
  0b01110,
  0b00000
};

byte waveChar[8] = {
  0b00000,
  0b00000,
  0b00000,
  0b11011,
  0b00100,
  0b11011,
  0b00000,
  0b00000
};

byte warningChar[8] = {
  0b00100,
  0b01110,
  0b01110,
  0b11111,
  0b11111,
  0b00100,
  0b00100,
  0b00000
};

// ============== INITIALIZATION ==============

void initLCD() {
  Wire.begin(I2C_SDA, I2C_SCL);
  lcd.init();
  lcd.backlight();
  
  // Create custom characters
  lcd.createChar(0, dropletChar);
  lcd.createChar(1, waveChar);
  lcd.createChar(2, warningChar);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Flood Detection");
  lcd.setCursor(0, 1);
  lcd.print("System v1.0");
  
  Serial.println("LCD initialized");
}

void initLEDs() {
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_YELLOW_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);
  
  // Test all LEDs
  digitalWrite(LED_GREEN_PIN, HIGH);
  delay(200);
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_YELLOW_PIN, HIGH);
  delay(200);
  digitalWrite(LED_YELLOW_PIN, LOW);
  digitalWrite(LED_RED_PIN, HIGH);
  delay(200);
  digitalWrite(LED_RED_PIN, LOW);
  
  Serial.println("LEDs initialized");
}

void initSensors() {
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
  
  // Configure ADC for ESP32
  #ifdef ESP32
    analogReadResolution(12);  // 12-bit resolution
    analogSetAttenuation(ADC_11db);  // Full range 0-3.3V
  #endif
  
  Serial.println("Sensors initialized");
}

// ============== LED ALERT FUNCTIONS ==============

void setAlertLevel(float waterLevel, float rainIntensity) {
  // Determine alert level based on water level and rain
  if (waterLevel >= WATER_LEVEL_DANGER || rainIntensity >= 90) {
    currentAlert = ALERT_CRITICAL;
  } else if (waterLevel >= WATER_LEVEL_WARNING || rainIntensity >= RAIN_INTENSITY_HIGH) {
    currentAlert = ALERT_HIGH;
  } else if (waterLevel >= WATER_LEVEL_WARNING * 0.6 || rainIntensity >= 40) {
    currentAlert = ALERT_MODERATE;
  } else {
    currentAlert = ALERT_LOW;
  }
}

void updateLEDs() {
  static unsigned long lastBlink = 0;
  static bool blinkState = false;
  
  // Turn off all LEDs first
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_YELLOW_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
  
  switch (currentAlert) {
    case ALERT_LOW:
      // Green - Safe
      digitalWrite(LED_GREEN_PIN, HIGH);
      break;
      
    case ALERT_MODERATE:
      // Yellow - Warning
      digitalWrite(LED_YELLOW_PIN, HIGH);
      break;
      
    case ALERT_HIGH:
      // Red - Danger
      digitalWrite(LED_RED_PIN, HIGH);
      break;
      
    case ALERT_CRITICAL:
      // Red blinking - Critical
      if (millis() - lastBlink >= 250) {
        blinkState = !blinkState;
        lastBlink = millis();
      }
      digitalWrite(LED_RED_PIN, blinkState ? HIGH : LOW);
      break;
  }
}

const char* getAlertString() {
  switch (currentAlert) {
    case ALERT_LOW: return "SAFE";
    case ALERT_MODERATE: return "CAUTION";
    case ALERT_HIGH: return "WARNING";
    case ALERT_CRITICAL: return "DANGER!";
    default: return "UNKNOWN";
  }
}

// ============== LCD DISPLAY FUNCTIONS ==============

void updateLCD(float waterLevel, float rainIntensity, float piezoValue) {
  lcd.clear();
  
  switch (displayMode) {
    case 0:
      // Water Level Display
      lcd.setCursor(0, 0);
      lcd.write(1);  // Wave character
      lcd.print(" Water Level");
      lcd.setCursor(0, 1);
      lcd.print(waterLevel, 1);
      lcd.print(" cm ");
      lcd.print(getAlertString());
      break;
      
    case 1:
      // Rain Intensity Display
      lcd.setCursor(0, 0);
      lcd.write(0);  // Droplet character
      lcd.print(" Rain Intensity");
      lcd.setCursor(0, 1);
      lcd.print(rainIntensity, 1);
      lcd.print("% ");
      if (rainIntensity < 10) lcd.print("None");
      else if (rainIntensity < 30) lcd.print("Light");
      else if (rainIntensity < 60) lcd.print("Moderate");
      else lcd.print("Heavy");
      break;
      
    case 2:
      // Combined Status Display
      lcd.setCursor(0, 0);
      lcd.print("W:");
      lcd.print(waterLevel, 0);
      lcd.print("cm R:");
      lcd.print(rainIntensity, 0);
      lcd.print("%");
      lcd.setCursor(0, 1);
      lcd.write(2);  // Warning character
      lcd.print(" ");
      lcd.print(getAlertString());
      lcd.print(" ");
      lcd.print(wifiConnected ? "WiFi" : "NoWiFi");
      break;
      
    case 3:
      // System Status
      lcd.setCursor(0, 0);
      lcd.print("Node: ");
      lcd.print(NODE_ID);
      lcd.setCursor(0, 1);
      lcd.print(wifiConnected ? "Online " : "Offline");
      lcd.print(WiFi.localIP().toString().substring(0, 9));
      break;
  }
  
  // Cycle through display modes
  displayMode = (displayMode + 1) % 4;
}

void showError(const char* message) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.write(2);  // Warning character
  lcd.print(" ERROR");
  lcd.setCursor(0, 1);
  lcd.print(message);
}

void showSuccess(const char* message) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("OK: ");
  lcd.print(message);
}

// ============== SENSOR FUNCTIONS ==============

float readPiezoSensor() {
  int rawValue = analogRead(PIEZO_PIN);
  float normalized = map(rawValue, SENSOR_MIN, SENSOR_MAX, 0, 100);
  return constrain(normalized, 0, 100);
}

float readUltrasonicSensor() {
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  
  long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, 30000);
  float distance = duration * 0.0343 / 2.0;
  
  if (distance <= 0 || distance > WATER_LEVEL_MAX) {
    distance = WATER_LEVEL_MAX;
  }
  
  float waterLevel = WATER_LEVEL_MAX - distance;
  return constrain(waterLevel, 0, WATER_LEVEL_MAX);
}

float readRainSensor() {
  int rawValue = analogRead(RAIN_SENSOR_PIN);
  // Rain sensor gives LOW when wet, invert the reading
  int invertedValue = SENSOR_MAX - rawValue;
  float normalized = map(invertedValue, SENSOR_MIN, SENSOR_MAX, 0, 100);
  return constrain(normalized, 0, 100);
}

// ============== WIFI FUNCTIONS ==============

void connectWiFi() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");
  lcd.setCursor(0, 1);
  
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    lcd.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Connected!");
    lcd.setCursor(0, 1);
    lcd.print(WiFi.localIP());
    delay(2000);
  } else {
    wifiConnected = false;
    Serial.println("\nWiFi connection failed!");
    showError("WiFi Failed");
    delay(2000);
  }
}

void checkWiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    wifiConnected = false;
    Serial.println("WiFi disconnected. Reconnecting...");
    connectWiFi();
  }
}

// ============== API FUNCTIONS ==============

bool sendSensorData(float piezoValue, float ultrasonicValue, float rainSensorValue) {
  if (!wifiConnected) {
    Serial.println("Cannot send data: WiFi not connected");
    return false;
  }
  
  HTTPClient http;
  WiFiClient client;
  
  String jsonPayload = "{";
  jsonPayload += "\"node_id\":\"" + String(NODE_ID) + "\",";
  jsonPayload += "\"piezo_value\":" + String(piezoValue, 2) + ",";
  jsonPayload += "\"ultrasonic_value\":" + String(ultrasonicValue, 2) + ",";
  jsonPayload += "\"rain_sensor_value\":" + String(rainSensorValue, 2) + ",";
  jsonPayload += "\"location\":\"" + String(LOCATION) + "\"";
  jsonPayload += "}";
  
  Serial.println("Sending data to API:");
  Serial.println(jsonPayload);
  
  #ifdef ESP32
    http.begin(API_URL);
  #else
    http.begin(client, API_URL);
  #endif
  
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    
    if (httpResponseCode == 200) {
      String response = http.getString();
      Serial.println("Response: " + response);
      http.end();
      return true;
    }
  } else {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
  return false;
}

bool sendDataWithRetry(float piezoValue, float ultrasonicValue, float rainSensorValue) {
  for (int i = 0; i < MAX_RETRIES; i++) {
    if (sendSensorData(piezoValue, ultrasonicValue, rainSensorValue)) {
      return true;
    }
    Serial.print("Retry ");
    Serial.print(i + 1);
    Serial.print("/");
    Serial.println(MAX_RETRIES);
    delay(RETRY_DELAY);
  }
  Serial.println("Failed to send data after retries");
  return false;
}

// ============== MAIN FUNCTIONS ==============

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=================================");
  Serial.println("Flood Detection IoT Node");
  Serial.println("=================================");
  Serial.print("Node ID: ");
  Serial.println(NODE_ID);
  Serial.print("Location: ");
  Serial.println(LOCATION);
  Serial.println();
  
  // Initialize components
  initLCD();
  delay(2000);
  initLEDs();
  initSensors();
  
  // Connect to WiFi
  connectWiFi();
  
  Serial.println("Setup complete. Starting main loop...\n");
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
  lcd.setCursor(0, 1);
  lcd.print("Monitoring...");
  delay(1500);
}

void loop() {
  // Check WiFi connection
  checkWiFi();
  
  // Read sensor values
  float piezoValue = readPiezoSensor();
  float ultrasonicValue = readUltrasonicSensor();
  float rainSensorValue = readRainSensor();
  
  // Update alert level and LEDs
  setAlertLevel(ultrasonicValue, rainSensorValue);
  updateLEDs();
  
  // Update LCD periodically
  unsigned long currentTime = millis();
  if (currentTime - lastLcdUpdate >= LCD_UPDATE_INTERVAL) {
    lastLcdUpdate = currentTime;
    updateLCD(ultrasonicValue, rainSensorValue, piezoValue);
  }
  
  // Print sensor readings to Serial
  Serial.println("--- Sensor Readings ---");
  Serial.print("Piezo (Rain Intensity): ");
  Serial.print(piezoValue, 2);
  Serial.println("%");
  Serial.print("Ultrasonic (Water Level): ");
  Serial.print(ultrasonicValue, 2);
  Serial.println(" cm");
  Serial.print("Rain Sensor: ");
  Serial.print(rainSensorValue, 2);
  Serial.println("%");
  Serial.print("Alert Level: ");
  Serial.println(getAlertString());
  
  // Send data to backend periodically
  if (currentTime - lastSendTime >= SEND_INTERVAL || lastSendTime == 0) {
    lastSendTime = currentTime;
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Sending data...");
    
    if (sendDataWithRetry(piezoValue, ultrasonicValue, rainSensorValue)) {
      Serial.println("Data sent successfully!");
      lcd.setCursor(0, 1);
      lcd.print("Sent OK!");
    } else {
      Serial.println("Failed to send data!");
      lcd.setCursor(0, 1);
      lcd.print("Send Failed!");
    }
    
    delay(1000);
    Serial.println();
  }
  
  // Small delay
  delay(100);
}