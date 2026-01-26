"""
Test Unit for Google Sheets - Flood Detection System

This script tests read/write operations on Google Sheets and populates
the spreadsheet with dummy flood and rain data based on Malaysian
geographical locations known for flooding.

Usage:
    python test_spreadsheet.py

Features:
    - Test Google Sheets connection
    - Read existing data
    - Write dummy sensor data for Malaysian locations
    - Generate realistic flood scenarios
"""

import os
import random
from datetime import datetime, timedelta
from typing import List, Dict
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============== CONFIGURATION ==============

GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "FloodData")

# ============== MALAYSIAN FLOOD-PRONE LOCATIONS ==============
# Based on historical flood data in Malaysia

MALAYSIAN_LOCATIONS = [
    # Kelantan - Most flood-prone state
    {"node_id": "KLT-001", "location": "Kota Bharu, Kelantan", "flood_risk": "high"},
    {"node_id": "KLT-002", "location": "Kuala Krai, Kelantan", "flood_risk": "critical"},
    {"node_id": "KLT-003", "location": "Gua Musang, Kelantan", "flood_risk": "high"},
    
    # Terengganu
    {"node_id": "TRG-001", "location": "Kuala Terengganu, Terengganu", "flood_risk": "high"},
    {"node_id": "TRG-002", "location": "Kemaman, Terengganu", "flood_risk": "moderate"},
    
    # Pahang
    {"node_id": "PHG-001", "location": "Kuantan, Pahang", "flood_risk": "high"},
    {"node_id": "PHG-002", "location": "Temerloh, Pahang", "flood_risk": "moderate"},
    {"node_id": "PHG-003", "location": "Pekan, Pahang", "flood_risk": "high"},
    
    # Johor
    {"node_id": "JHR-001", "location": "Kota Tinggi, Johor", "flood_risk": "moderate"},
    {"node_id": "JHR-002", "location": "Segamat, Johor", "flood_risk": "moderate"},
    
    # Selangor/KL
    {"node_id": "SGR-001", "location": "Shah Alam, Selangor", "flood_risk": "moderate"},
    {"node_id": "SGR-002", "location": "Klang, Selangor", "flood_risk": "moderate"},
    {"node_id": "KUL-001", "location": "Kuala Lumpur City Centre", "flood_risk": "low"},
    
    # Penang
    {"node_id": "PNG-001", "location": "George Town, Penang", "flood_risk": "moderate"},
    {"node_id": "PNG-002", "location": "Bukit Mertajam, Penang", "flood_risk": "low"},
    
    # Kedah/Perlis
    {"node_id": "KDH-001", "location": "Alor Setar, Kedah", "flood_risk": "moderate"},
    {"node_id": "PLS-001", "location": "Kangar, Perlis", "flood_risk": "low"},
    
    # Sabah/Sarawak
    {"node_id": "SBH-001", "location": "Kota Kinabalu, Sabah", "flood_risk": "moderate"},
    {"node_id": "SWK-001", "location": "Kuching, Sarawak", "flood_risk": "moderate"},
    {"node_id": "SWK-002", "location": "Sibu, Sarawak", "flood_risk": "high"},
]

# ============== GOOGLE SHEETS CLIENT ==============

def get_google_sheets_client():
    """Initialize and return Google Sheets client"""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        if os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FILE):
            creds = Credentials.from_service_account_file(
                GOOGLE_SHEETS_CREDENTIALS_FILE,
                scopes=scopes
            )
            client = gspread.authorize(creds)
            print(f"✅ Connected to Google Sheets with credentials from: {GOOGLE_SHEETS_CREDENTIALS_FILE}")
            return client
        else:
            print(f"❌ Credentials file not found: {GOOGLE_SHEETS_CREDENTIALS_FILE}")
            return None
    except Exception as e:
        print(f"❌ Error initializing Google Sheets client: {e}")
        return None

def get_or_create_spreadsheet(client):
    """Get existing spreadsheet or create new one"""
    try:
        # Try to open existing spreadsheet
        spreadsheet = client.open(SPREADSHEET_NAME)
        print(f"✅ Opened existing spreadsheet: {SPREADSHEET_NAME}")
        return spreadsheet
    except gspread.SpreadsheetNotFound:
        # Create new spreadsheet
        print(f"📝 Spreadsheet '{SPREADSHEET_NAME}' not found. Creating new one...")
        spreadsheet = client.create(SPREADSHEET_NAME)
        # Share with anyone (optional - for testing)
        # spreadsheet.share('', perm_type='anyone', role='reader')
        print(f"✅ Created new spreadsheet: {SPREADSHEET_NAME}")
        return spreadsheet

# ============== DATA GENERATION ==============

def generate_sensor_reading(location: Dict, scenario: str = "normal") -> Dict:
    """
    Generate realistic sensor data based on location risk and scenario.
    
    Scenarios:
        - normal: Regular day with low-moderate readings
        - rainy: Monsoon season with elevated readings
        - flood: Active flooding with critical readings
    """
    risk_level = location["flood_risk"]
    
    # Base values based on risk level
    if risk_level == "critical":
        base_water = random.uniform(60, 90)
        base_rain = random.uniform(50, 80)
        base_piezo = random.uniform(55, 85)
    elif risk_level == "high":
        base_water = random.uniform(40, 70)
        base_rain = random.uniform(40, 70)
        base_piezo = random.uniform(40, 70)
    elif risk_level == "moderate":
        base_water = random.uniform(20, 50)
        base_rain = random.uniform(25, 55)
        base_piezo = random.uniform(25, 50)
    else:  # low
        base_water = random.uniform(5, 30)
        base_rain = random.uniform(5, 35)
        base_piezo = random.uniform(5, 30)
    
    # Apply scenario multiplier
    if scenario == "flood":
        multiplier = random.uniform(1.3, 1.6)
        base_water = min(base_water * multiplier, 150)
        base_rain = min(base_rain * multiplier, 100)
        base_piezo = min(base_piezo * multiplier, 100)
    elif scenario == "rainy":
        multiplier = random.uniform(1.1, 1.3)
        base_water = min(base_water * multiplier, 120)
        base_rain = min(base_rain * multiplier, 100)
        base_piezo = min(base_piezo * multiplier, 100)
    elif scenario == "dry":
        multiplier = random.uniform(0.3, 0.6)
        base_water *= multiplier
        base_rain = random.uniform(0, 10)
        base_piezo = random.uniform(0, 15)
    
    return {
        "node_id": location["node_id"],
        "piezo_value": round(base_piezo, 2),
        "ultrasonic_value": round(base_water, 2),
        "rain_sensor_value": round(base_rain, 2),
        "location": location["location"]
    }

def generate_historical_data(days: int = 7, readings_per_day: int = 24) -> List[Dict]:
    """
    Generate historical sensor data for all Malaysian locations.
    
    Simulates Northeast Monsoon season (Nov-Mar) which causes
    major floods in East Coast states.
    
    Args:
        days: Number of days of historical data
        readings_per_day: Number of readings per location per day
    
    Returns:
        List of sensor readings with timestamps
    """
    all_data = []
    start_date = datetime.now() - timedelta(days=days)
    
    print(f"\n📊 Generating {days} days of data for {len(MALAYSIAN_LOCATIONS)} locations...")
    print(f"   Total readings: {days * readings_per_day * len(MALAYSIAN_LOCATIONS)}")
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        # Simulate weather patterns
        # Higher chance of rain/flood during certain periods
        if day % 7 < 2:  # Beginning of week - simulate storm
            scenarios = ["rainy", "flood", "flood", "rainy"]
        elif day % 7 < 5:  # Mid week - moderate
            scenarios = ["normal", "rainy", "normal", "normal"]
        else:  # Weekend - dry spell
            scenarios = ["normal", "dry", "normal", "dry"]
        
        for hour in range(0, 24, 24 // readings_per_day):
            timestamp = current_date.replace(hour=hour, minute=0, second=0)
            
            # Night hours more likely to have rain accumulation
            if 0 <= hour <= 6 or 18 <= hour <= 23:
                scenario = random.choice(scenarios)
            else:
                scenario = random.choice(["normal", scenarios[0]])
            
            for location in MALAYSIAN_LOCATIONS:
                reading = generate_sensor_reading(location, scenario)
                reading["timestamp"] = timestamp.isoformat()
                
                # Generate unique data_id
                reading["data_id"] = f"{location['node_id']}_{timestamp.strftime('%Y%m%d%H%M%S')}"
                
                all_data.append(reading)
    
    return all_data

# ============== SPREADSHEET OPERATIONS ==============

def setup_headers(worksheet):
    """Ensure spreadsheet has proper headers"""
    headers = [
        "data_id",
        "node_id", 
        "piezo_value", 
        "ultrasonic_value",
        "rain_sensor_value",
        "location",
        "timestamp"
    ]
    
    try:
        existing_headers = worksheet.row_values(1)
        if not existing_headers or existing_headers != headers:
            worksheet.update('A1:G1', [headers])
            print("✅ Headers set up successfully")
        else:
            print("✅ Headers already exist")
    except Exception as e:
        worksheet.update('A1:G1', [headers])
        print(f"✅ Headers created: {e}")

def write_data_to_sheet(worksheet, data: List[Dict]):
    """Write sensor data to spreadsheet"""
    if not data:
        print("⚠️ No data to write")
        return
    
    # Prepare rows for batch update
    rows = []
    for reading in data:
        row = [
            reading.get("data_id", ""),
            reading.get("node_id", ""),
            reading.get("piezo_value", 0),
            reading.get("ultrasonic_value", 0),
            reading.get("rain_sensor_value", 0),
            reading.get("location", ""),
            reading.get("timestamp", "")
        ]
        rows.append(row)
    
    # Batch update for efficiency
    print(f"\n📤 Writing {len(rows)} rows to spreadsheet...")
    
    # Write in chunks to avoid API limits
    chunk_size = 500
    total_written = 0
    
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        start_row = i + 2  # +2 because row 1 is headers, and sheets are 1-indexed
        end_row = start_row + len(chunk) - 1
        
        cell_range = f"A{start_row}:G{end_row}"
        worksheet.update(cell_range, chunk)
        
        total_written += len(chunk)
        print(f"   Written {total_written}/{len(rows)} rows...")
    
    print(f"✅ Successfully wrote {len(rows)} rows to spreadsheet")

def read_data_from_sheet(worksheet, limit: int = None) -> List[Dict]:
    """Read sensor data from spreadsheet"""
    try:
        records = worksheet.get_all_records()
        
        if limit:
            records = records[-limit:]
        
        print(f"✅ Read {len(records)} records from spreadsheet")
        return records
    except Exception as e:
        print(f"❌ Error reading data: {e}")
        return []

def clear_sheet_data(worksheet):
    """Clear all data except headers"""
    try:
        # Get the number of rows
        all_values = worksheet.get_all_values()
        if len(all_values) > 1:
            # Clear all rows except header
            worksheet.delete_rows(2, len(all_values))
            print(f"✅ Cleared {len(all_values) - 1} rows from spreadsheet")
        else:
            print("ℹ️ Spreadsheet is already empty (only headers)")
    except Exception as e:
        print(f"❌ Error clearing data: {e}")

# ============== TEST FUNCTIONS ==============

def test_connection():
    """Test 1: Verify Google Sheets connection"""
    print("\n" + "="*60)
    print("TEST 1: Google Sheets Connection")
    print("="*60)
    
    client = get_google_sheets_client()
    if client:
        spreadsheet = get_or_create_spreadsheet(client)
        if spreadsheet:
            print(f"   Spreadsheet URL: {spreadsheet.url}")
            return True
    return False

def test_write_single_reading():
    """Test 2: Write a single sensor reading"""
    print("\n" + "="*60)
    print("TEST 2: Write Single Sensor Reading")
    print("="*60)
    
    client = get_google_sheets_client()
    if not client:
        return False
    
    spreadsheet = get_or_create_spreadsheet(client)
    worksheet = spreadsheet.sheet1
    setup_headers(worksheet)
    
    # Generate single test reading
    test_location = MALAYSIAN_LOCATIONS[0]  # Kota Bharu
    test_reading = generate_sensor_reading(test_location, "normal")
    test_reading["timestamp"] = datetime.now().isoformat()
    test_reading["data_id"] = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    print(f"\n📍 Test Location: {test_location['location']}")
    print(f"   Node ID: {test_reading['node_id']}")
    print(f"   Water Level: {test_reading['ultrasonic_value']} cm")
    print(f"   Rain Sensor: {test_reading['rain_sensor_value']}%")
    print(f"   Piezo Value: {test_reading['piezo_value']}")
    
    write_data_to_sheet(worksheet, [test_reading])
    return True

def test_read_data():
    """Test 3: Read data from spreadsheet"""
    print("\n" + "="*60)
    print("TEST 3: Read Data from Spreadsheet")
    print("="*60)
    
    client = get_google_sheets_client()
    if not client:
        return False
    
    spreadsheet = get_or_create_spreadsheet(client)
    worksheet = spreadsheet.sheet1
    
    records = read_data_from_sheet(worksheet, limit=5)
    
    if records:
        print("\n📊 Last 5 readings:")
        print("-" * 80)
        for record in records:
            print(f"   {record.get('node_id', 'N/A'):10} | "
                  f"{record.get('location', 'N/A'):30} | "
                  f"Water: {record.get('ultrasonic_value', 0):6} cm | "
                  f"Rain: {record.get('rain_sensor_value', 0):5}%")
        print("-" * 80)
    
    return True

def test_populate_historical_data(days: int = 3, readings_per_day: int = 4):
    """Test 4: Populate spreadsheet with historical dummy data"""
    print("\n" + "="*60)
    print("TEST 4: Populate Historical Dummy Data")
    print("="*60)
    
    client = get_google_sheets_client()
    if not client:
        return False
    
    spreadsheet = get_or_create_spreadsheet(client)
    worksheet = spreadsheet.sheet1
    setup_headers(worksheet)
    
    # Generate historical data
    historical_data = generate_historical_data(days=days, readings_per_day=readings_per_day)
    
    # Write to spreadsheet
    write_data_to_sheet(worksheet, historical_data)
    
    return True

def test_summary_statistics():
    """Test 5: Generate summary statistics from data"""
    print("\n" + "="*60)
    print("TEST 5: Summary Statistics")
    print("="*60)
    
    client = get_google_sheets_client()
    if not client:
        return False
    
    spreadsheet = get_or_create_spreadsheet(client)
    worksheet = spreadsheet.sheet1
    
    records = read_data_from_sheet(worksheet)
    
    if not records:
        print("⚠️ No data available for statistics")
        return False
    
    # Calculate statistics per location
    location_stats = {}
    for record in records:
        node_id = record.get("node_id", "unknown")
        if node_id not in location_stats:
            location_stats[node_id] = {
                "location": record.get("location", "Unknown"),
                "readings": 0,
                "total_water": 0,
                "total_rain": 0,
                "max_water": 0,
                "max_rain": 0
            }
        
        stats = location_stats[node_id]
        water = float(record.get("ultrasonic_value", 0) or 0)
        rain = float(record.get("rain_sensor_value", 0) or 0)
        
        stats["readings"] += 1
        stats["total_water"] += water
        stats["total_rain"] += rain
        stats["max_water"] = max(stats["max_water"], water)
        stats["max_rain"] = max(stats["max_rain"], rain)
    
    print(f"\n📈 Statistics for {len(location_stats)} nodes ({len(records)} total readings):")
    print("-" * 100)
    print(f"{'Node ID':<12} {'Location':<35} {'Readings':<10} {'Avg Water':<12} {'Max Water':<12} {'Max Rain':<10}")
    print("-" * 100)
    
    for node_id, stats in sorted(location_stats.items()):
        avg_water = stats["total_water"] / stats["readings"] if stats["readings"] > 0 else 0
        print(f"{node_id:<12} {stats['location'][:34]:<35} {stats['readings']:<10} "
              f"{avg_water:<12.2f} {stats['max_water']:<12.2f} {stats['max_rain']:<10.2f}")
    
    print("-" * 100)
    
    return True

# ============== MAIN MENU ==============

def print_menu():
    """Print interactive menu"""
    print("\n" + "="*60)
    print("🌊 FLOOD DETECTION - SPREADSHEET TEST UNIT")
    print("="*60)
    print("\nSelect an option:")
    print("  1. Test Google Sheets connection")
    print("  2. Write single test reading")
    print("  3. Read last 5 readings")
    print("  4. Populate with dummy data (3 days)")
    print("  5. Populate with dummy data (7 days)")
    print("  6. Populate with dummy data (30 days)")
    print("  7. View summary statistics")
    print("  8. Clear all data (keep headers)")
    print("  9. Run all tests")
    print("  0. Exit")
    print("-"*60)

def main():
    """Main entry point with interactive menu"""
    while True:
        print_menu()
        choice = input("\nEnter your choice (0-9): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            test_connection()
        elif choice == "2":
            test_write_single_reading()
        elif choice == "3":
            test_read_data()
        elif choice == "4":
            test_populate_historical_data(days=3, readings_per_day=6)
        elif choice == "5":
            test_populate_historical_data(days=7, readings_per_day=4)
        elif choice == "6":
            test_populate_historical_data(days=30, readings_per_day=2)
        elif choice == "7":
            test_summary_statistics()
        elif choice == "8":
            confirm = input("⚠️ Are you sure you want to clear all data? (yes/no): ")
            if confirm.lower() == "yes":
                client = get_google_sheets_client()
                if client:
                    spreadsheet = get_or_create_spreadsheet(client)
                    clear_sheet_data(spreadsheet.sheet1)
        elif choice == "9":
            print("\n🚀 Running all tests...")
            test_connection()
            test_write_single_reading()
            test_read_data()
            test_populate_historical_data(days=3, readings_per_day=4)
            test_summary_statistics()
            print("\n✅ All tests completed!")
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
