"""
Test script to create a task with proof requirement
"""
from database import get_database_connection
from datetime import datetime, timedelta

# Connect to database
db = get_database_connection()

# Get your telegram user ID (replace with actual ID)
EMPLOYEE_TELEGRAM_ID = 8261255116  # Replace with your Telegram ID
ADMIN_TELEGRAM_ID = 8261255116

# Create test task with proof requirement
due_date = (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M')

db.execute_query("""
    INSERT INTO tbl_tasks 
    (Date, department, assignee_id, assignee_name, description, 
     priority, due_date, is_materials, is_check, is_perform, proof_path, 
     created_by, proof_required, proof_type, status, task_type)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    datetime.now().date(),
    'Housekeeping',
    EMPLOYEE_TELEGRAM_ID,
    'Test Employee',
    '🧪 TEST: Clean room 101 - PROOF REQUIRED',
    'Urgent',
    due_date,
    0,  # is_materials
    0,  # is_check
    0,  # is_perform
    '',  # proof_path (empty initially)
    ADMIN_TELEGRAM_ID,
    1,  # proof_required = 1 (REQUIRED!)
    'photo',  # proof_type
    'pending',
    'test'
))

print("✅ Test task created!")
print(f"📋 Task: Clean room 101 - PROOF REQUIRED")
print(f"👤 Assigned to: {EMPLOYEE_TELEGRAM_ID}")
print(f"⏰ Due: {due_date}")
print(f"🔒 Proof: REQUIRED (photo)")
print(f"📊 Status: pending")
print("\n📱 Check your Telegram bot to see the task!")
