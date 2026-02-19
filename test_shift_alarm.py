"""
Test Shift Alarm Utility Script
Test the shift alarm functionality
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

conn = psycopg2.connect(host='localhost', port=5432, database='hotel_manage', user='postgres', password='postgres')
cursor = conn.cursor(cursor_factory=RealDictCursor)

print("=== Testing Shift Alarm ===\n")

# Get current time
now = datetime.now()
current_time = now.strftime('%H:%M')
print(f"Current time: {current_time}")

# Get shifts
cursor.execute("SELECT * FROM tbl_shifts")
shifts = cursor.fetchall()

print(f"\nFound {len(shifts)} shifts:\n")

for shift in shifts:
    shift_name = shift.get('shift_name', 'Unknown')
    start_time = shift.get('start_time', '00:00')
    end_time = shift.get('end_time', '00:00')
    
    # Convert to string if needed
    if hasattr(start_time, 'strftime'):
        start_time = start_time.strftime('%H:%M')
    if hasattr(end_time, 'strftime'):
        end_time = end_time.strftime('%H:%M')
    
    print(f"  {shift_name}: {start_time} - {end_time}")
    
    # Check if shift is ending soon (within 30 minutes)
    try:
        end_hour, end_min = map(int, str(end_time).split(':'))
        end_dt = now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
        
        diff = (end_dt - now).total_seconds() / 60
        
        if 0 <= diff <= 30:
            print(f"    ⚠️ ENDING SOON! ({int(diff)} minutes)")
        elif -30 <= diff < 0:
            print(f"    ✅ Just ended ({abs(int(diff))} minutes ago)")
        else:
            print(f"    ⏰ Ends in {int(diff)} minutes")
    except Exception as e:
        print(f"    ❌ Error calculating: {e}")

print("\nTest complete.")

cursor.close()
conn.close()
