"""
Restore Shift Utility Script
Restore or reset shift data in database
"""

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(host='localhost', port=5432, database='hotel_manage', user='postgres', password='postgres')
cursor = conn.cursor(cursor_factory=RealDictCursor)

print("=== Restoring Default Shifts ===\n")

# Default shifts
default_shifts = [
    ('Morning', '06:00', '14:00'),
    ('Afternoon', '14:00', '22:00'),
    ('Night', '22:00', '06:00'),
]

# Check existing shifts
cursor.execute("SELECT COUNT(*) as count FROM tbl_shifts")
count = cursor.fetchone()['count']

if count == 0:
    print("No shifts found. Creating default shifts...")
    for name, start, end in default_shifts:
        cursor.execute("""
            INSERT INTO tbl_shifts (shift_name, start_time, end_time)
            VALUES (%s, %s, %s)
        """, (name, start, end))
    conn.commit()
    print(f"Created {len(default_shifts)} default shifts")
else:
    print(f"Found {count} existing shifts. No action needed.")

cursor.close()
conn.close()
