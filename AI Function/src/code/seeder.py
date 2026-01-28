"""
Test Unit for Google Sheets - Flood Detection System

Independent test script for read/write operations on Google Sheets.
Generates dummy flood and rain sensor data for a single IoT node.

NO NOTIFICATIONS - Pure data generation and spreadsheet operations only.

Usage:
    python pp.py [command]

Commands:
    connect     - Test Google Sheets connection
    write       - Write single test reading
    read        - Read last 10 readings
    populate    - Populate with 7 days dummy data
    populate30  - Populate with 30 days dummy data
    stats       - View summary statistics
    clear       - Clear all data (keeps headers)
    menu        - Interactive menu (default)

Examples:
    python test_spreadsheet.py connect
    python test_spreadsheet.py populate
    python test_spreadsheet.py read
"""

import os
import sys
import random
from datetime import datetime, timedelta
from typing import List, Dict
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables from the script's directory
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

# ============== CONFIGURATION ==============

# Use absolute path based on script location
_creds_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")
if not os.path.isabs(_creds_file):
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, _creds_file)
else:
    GOOGLE_SHEETS_CREDENTIALS_FILE = _creds_file

SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "FloodData")

# ============== SINGLE NODE CONFIGURATION ==============
# Configure your IoT node here (single sensor node setup)

# Change these values to match your actual node setup
NODE_CONFIG = {
    "node_id": "NODE-001",           # Your node ID
    "location": "Shah Alam, Selangor",  # Your node location
    "flood_risk": "moderate"          # Risk level: low, moderate, high, critical
}

# Wrap in list for compatibility with generate functions
SENSOR_NODE = [NODE_CONFIG]

# ============== GOOGLE SHEETS CLIENT ==============

def get_sheets_client():
    """Initialize and return Google Sheets client"""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        print(f"🔍 Looking for credentials at: {GOOGLE_SHEETS_CREDENTIALS_FILE}")
        
        if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FILE):
            print(f"❌ Credentials file not found: {GOOGLE_SHEETS_CREDENTIALS_FILE}")
            print(f"   Script directory: {SCRIPT_DIR}")
            print(f"   Files in directory: {os.listdir(SCRIPT_DIR)}")
            return None
        
        print(f"✅ Found credentials file")
        creds = Credentials.from_service_account_file(
            GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=scopes
        )
        client = gspread.authorize(creds)
        return client
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_spreadsheet(client):
    """Get existing spreadsheet or create new one"""
    try:
        return client.open(SPREADSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        print(f"📝 Creating new spreadsheet: {SPREADSHEET_NAME}")
        return client.create(SPREADSHEET_NAME)

def setup_headers(worksheet):
    """Ensure spreadsheet has proper headers"""
    headers = ["data_id", "node_id", "piezo_value", "ultrasonic_value", 
               "rain_sensor_value", "location", "timestamp"]
    
    existing = worksheet.row_values(1)
    if existing != headers:
        worksheet.update('A1:G1', [headers])
        print("✅ Headers configured")

# ============== DATA GENERATION ==============

def generate_reading(location: Dict, scenario: str = "normal") -> Dict:
    """Generate realistic sensor data based on location and weather scenario"""
    risk = location["flood_risk"]
    
    # Base values by risk level
    ranges = {
        "critical": {"water": (60, 90), "rain": (50, 80), "piezo": (55, 85)},
        "high":     {"water": (40, 70), "rain": (40, 70), "piezo": (40, 70)},
        "moderate": {"water": (20, 50), "rain": (25, 55), "piezo": (25, 50)},
        "low":      {"water": (5, 30),  "rain": (5, 35),  "piezo": (5, 30)}
    }
    
    r = ranges.get(risk, ranges["low"])
    water = random.uniform(*r["water"])
    rain = random.uniform(*r["rain"])
    piezo = random.uniform(*r["piezo"])
    
    # Apply scenario multiplier
    if scenario == "flood":
        mult = random.uniform(1.3, 1.6)
        water = min(water * mult, 150)
        rain = min(rain * mult, 100)
        piezo = min(piezo * mult, 100)
    elif scenario == "rainy":
        mult = random.uniform(1.1, 1.3)
        water = min(water * mult, 120)
        rain = min(rain * mult, 100)
        piezo = min(piezo * mult, 100)
    elif scenario == "dry":
        water *= random.uniform(0.3, 0.6)
        rain = random.uniform(0, 10)
        piezo = random.uniform(0, 15)
    
    return {
        "node_id": location["node_id"],
        "piezo_value": round(piezo, 2),
        "ultrasonic_value": round(water, 2),
        "rain_sensor_value": round(rain, 2),
        "location": location["location"]
    }

def generate_dummy_data(
    days: int = 30,
    readings_per_day: int = 48,
    force_levels: bool = True
) -> List[Dict]:
    """
    Generate LARGE historical dataset (>1000 rows).
    Ensures LOW, MODERATE, HIGH flood risks exist.
    """
    data = []
    start = datetime.now() - timedelta(days=days)

    risk_cycle = ["low", "moderate", "high"]
    scenario_map = {
        "low": "dry",
        "moderate": "normal",
        "high": "flood"
    }

    print(
        f"📊 Generating data: "
        f"{days} days × {readings_per_day}/day = "
        f"{days * readings_per_day} rows"
    )

    for day in range(days):
        date = start + timedelta(days=day)
        risk_level = risk_cycle[day % len(risk_cycle)]

        for i in range(readings_per_day):
            hour = int((24 / readings_per_day) * i)
            ts = date.replace(hour=hour, minute=0, second=0)

            for loc in SENSOR_NODE:
                loc["flood_risk"] = risk_level
                scenario = scenario_map[risk_level]

                reading = generate_reading(loc, scenario)
                reading["timestamp"] = ts.isoformat()
                reading["data_id"] = f"{loc['node_id']}_{ts.strftime('%Y%m%d%H%M%S')}"
                data.append(reading)

    print(f"✅ Generated {len(data)} records")
    return data


# ============== SPREADSHEET OPERATIONS ==============

def write_data(worksheet, data: List[Dict]):
    """Write data to spreadsheet in chunks"""
    if not data:
        print("⚠️ No data to write")
        return
    
    rows = [[d["data_id"], d["node_id"], d["piezo_value"], d["ultrasonic_value"],
             d["rain_sensor_value"], d["location"], d["timestamp"]] for d in data]
    
    print(f"📤 Writing {len(rows)} rows...")
    
    chunk_size = 500
    written = 0
    
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        start_row = i + 2
        worksheet.update(f"A{start_row}:G{start_row + len(chunk) - 1}", chunk)
        written += len(chunk)
        print(f"   {written}/{len(rows)} rows written")
    
    print(f"✅ Done! {len(rows)} rows written")

def read_data(worksheet, limit: int = None) -> List[Dict]:
    """Read data from spreadsheet"""
    records = worksheet.get_all_records()
    if limit:
        records = records[-limit:]
    return records

def clear_data(worksheet):
    """Clear all data except headers"""
    values = worksheet.get_all_values()
    if len(values) > 1:
        worksheet.delete_rows(2, len(values))
        print(f"✅ Cleared {len(values) - 1} rows")
    else:
        print("ℹ️ Already empty")

# ============== COMMANDS ==============

def cmd_connect():
    """Test connection"""
    print("\n🔗 Testing Google Sheets Connection...")
    client = get_sheets_client()
    if client:
        sheet = get_spreadsheet(client)
        print(f"✅ Connected to: {SPREADSHEET_NAME}")
        print(f"   URL: {sheet.url}")
        return True
    return False

def cmd_write():
    """Write single test reading"""
    print("\n📝 Writing Single Test Reading...")
    client = get_sheets_client()
    if not client:
        return False
    
    sheet = get_spreadsheet(client)
    ws = sheet.sheet1
    setup_headers(ws)
    
    loc = NODE_CONFIG  # Use single node
    reading = generate_reading(loc, "normal")
    reading["timestamp"] = datetime.now().isoformat()
    reading["data_id"] = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    print(f"📍 {loc['location']}")
    print(f"   Water: {reading['ultrasonic_value']} cm")
    print(f"   Rain:  {reading['rain_sensor_value']}%")
    print(f"   Piezo: {reading['piezo_value']}")
    
    write_data(ws, [reading])
    return True

def cmd_read(limit: int = 10):
    """Read recent data"""
    print(f"\n📖 Reading Last {limit} Records...")
    client = get_sheets_client()
    if not client:
        return False
    
    sheet = get_spreadsheet(client)
    records = read_data(sheet.sheet1, limit)
    
    if not records:
        print("⚠️ No data found")
        return False
    
    print(f"\n{'Node':<12} {'Location':<32} {'Water':<10} {'Rain':<8} {'Timestamp':<20}")
    print("-" * 90)
    for r in records:
        print(f"{r.get('node_id',''):<12} {str(r.get('location',''))[:31]:<32} "
              f"{r.get('ultrasonic_value',0):<10} {r.get('rain_sensor_value',0):<8} "
              f"{str(r.get('timestamp',''))[:19]:<20}")
    
    return True

def cmd_populate(days: int = 7):
    """Populate with dummy data"""
    print(f"\n🌧️ Populating {days} Days of Dummy Data...")
    client = get_sheets_client()
    if not client:
        return False
    
    sheet = get_spreadsheet(client)
    ws = sheet.sheet1
    setup_headers(ws)
    
    data = generate_dummy_data(days=days, readings_per_day=4)
    write_data(ws, data)
    return True

def cmd_populate1000():
    """
    Populate spreadsheet with >1000 deterministic rows
    """
    print("\n🚀 Populating dataset (>1000 rows)...")
    client = get_sheets_client()
    if not client:
        return False

    sheet = get_spreadsheet(client)
    ws = sheet.sheet1
    setup_headers(ws)

    data = generate_dummy_data(
        days=30,
        readings_per_day=48  # 30 × 48 = 1440 rows
    )

    write_data(ws, data)
    return True

def cmd_stats():
    """View statistics"""
    print("\n📈 Summary Statistics...")
    client = get_sheets_client()
    if not client:
        return False
    
    sheet = get_spreadsheet(client)
    records = read_data(sheet.sheet1)
    
    if not records:
        print("⚠️ No data")
        return False
    
    stats = {}
    for r in records:
        nid = r.get("node_id", "?")
        if nid not in stats:
            stats[nid] = {"loc": r.get("location",""), "n": 0, "water": 0, "rain": 0, 
                          "max_w": 0, "max_r": 0}
        s = stats[nid]
        w = float(r.get("ultrasonic_value", 0) or 0)
        rn = float(r.get("rain_sensor_value", 0) or 0)
        s["n"] += 1
        s["water"] += w
        s["rain"] += rn
        s["max_w"] = max(s["max_w"], w)
        s["max_r"] = max(s["max_r"], rn)
    
    print(f"\n📊 {len(stats)} nodes, {len(records)} total readings\n")
    print(f"{'Node':<12} {'Location':<32} {'Count':<8} {'Avg Water':<12} {'Max Water':<12} {'Max Rain':<10}")
    print("-" * 95)
    
    for nid, s in sorted(stats.items()):
        avg_w = s["water"] / s["n"] if s["n"] else 0
        print(f"{nid:<12} {s['loc'][:31]:<32} {s['n']:<8} {avg_w:<12.1f} {s['max_w']:<12.1f} {s['max_r']:<10.1f}")
    
    return True

def cmd_clear():
    """Clear all data"""
    print("\n🗑️ Clearing All Data...")
    client = get_sheets_client()
    if not client:
        return False
    
    sheet = get_spreadsheet(client)
    clear_data(sheet.sheet1)
    return True

def interactive_menu():
    """Interactive menu"""
    commands = {
        "1": ("Test connection", cmd_connect),
        "2": ("Write single reading", cmd_write),
        "3": ("Read last 10 records", lambda: cmd_read(10)),
        "4": ("Populate 7 days data", lambda: cmd_populate(7)),
        "5": ("Populate 30 days data", lambda: cmd_populate(30)),
        "6": ("View statistics", cmd_stats),
        "7": ("Clear all data", cmd_clear),
        "8": ("Populate >1000 rows (LOW/MED/HIGH)", cmd_populate1000),
        "0": ("Exit", None)
    }
    
    while True:
        print("\n" + "="*50)
        print("🌊 FLOOD DATA - SPREADSHEET TEST")
        print("="*50)
        for k, (desc, _) in commands.items():
            print(f"  {k}. {desc}")
        print("-"*50)
        
        choice = input("Choice: ").strip()
        
        if choice == "0":
            print("👋 Bye!")
            break
        elif choice == "7":
            if input("⚠️ Confirm clear? (yes/no): ").lower() == "yes":
                cmd_clear()
        elif choice in commands:
            commands[choice][1]()
        else:
            print("❌ Invalid choice")
        
        input("\nPress Enter...")

# ============== MAIN ==============

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else ["menu"]
    cmd = args[0].lower()
    
    if cmd == "connect":
        cmd_connect()
    elif cmd == "write":
        cmd_write()
    elif cmd == "read":
        limit = int(args[1]) if len(args) > 1 else 10
        cmd_read(limit)
    elif cmd == "populate":
        days = int(args[1]) if len(args) > 1 else 7
        cmd_populate(days)
    elif cmd == "populate30":
        cmd_populate(30)
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "clear":
        if input("⚠️ Clear all data? (yes/no): ").lower() == "yes":
            cmd_clear()
    elif cmd == "menu":
        interactive_menu()
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
