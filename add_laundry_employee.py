"""
Add Laundry Employee Utility Script
Add a new employee to the Laundry department
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

conn = psycopg2.connect(host='localhost', port=5432, database='hotel_manage', user='postgres', password='postgres')
cursor = conn.cursor(cursor_factory=RealDictCursor)

print("=== Add Laundry Employee ===\n")

# Get next employee ID
cursor.execute("SELECT id FROM tbl_employeer ORDER BY id DESC LIMIT 1")
result = cursor.fetchone()

if result:
    last_id = result['id']
    # Extract number and increment
    num = int(last_id.replace('EMP', ''))
    new_id = f"EMP{num + 1:05d}"
else:
    new_id = "EMP00001"

print(f"New Employee ID: {new_id}")

# Get employee details
if len(sys.argv) > 1:
    name = sys.argv[1]
else:
    name = input("Enter employee name: ")

# Insert new employee
try:
    cursor.execute("""
        INSERT INTO tbl_employeer (id, name, department, work_role)
        VALUES (%s, %s, 'Laundry', 'Staff')
    """, (new_id, name))
    conn.commit()
    print(f"\n✅ Successfully added: {name} ({new_id}) to Laundry department")
except Exception as e:
    print(f"\n❌ Error: {e}")
    conn.rollback()

cursor.close()
conn.close()
