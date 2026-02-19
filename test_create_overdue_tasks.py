"""
Test script to create overdue tasks for escalation testing
"""
from database import get_database_connection
from datetime import datetime, timedelta

db = get_database_connection()

EMPLOYEE_TELEGRAM_ID = 8261255116  # Replace with your Telegram ID
ADMIN_TELEGRAM_ID = 8261255116

# Create task that's 5 hours overdue (Level 1 escalation)
overdue_5h = (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M')

db.execute_query("""
    INSERT INTO tbl_tasks 
    (Date, department, assignee_id, assignee_name, description, 
     priority, due_date, is_materials, is_check, is_perform, proof_path, 
     created_by, proof_required, status, task_type)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    datetime.now().date(),
    'Housekeeping',
    EMPLOYEE_TELEGRAM_ID,
    'Test Employee',
    '🧪 TEST: Overdue 5 hours - Should escalate Level 1',
    'Urgent',
    overdue_5h,
    0, 0, 0, '', ADMIN_TELEGRAM_ID, 0,
    'in_progress',  # Already started
    'test_escalation'
))

# Create task that's 9 hours overdue (Level 2 escalation)
overdue_9h = (datetime.now() - timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')

db.execute_query("""
    INSERT INTO tbl_tasks 
    (Date, department, assignee_id, assignee_name, description, 
     priority, due_date, is_materials, is_check, is_perform, proof_path, 
     created_by, proof_required, status, task_type)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    datetime.now().date(),
    'Housekeeping',
    EMPLOYEE_TELEGRAM_ID,
    'Test Employee',
    '🧪 TEST: Overdue 9 hours - Should escalate Level 2',
    'Urgent',
    overdue_9h,
    0, 0, 0, '', ADMIN_TELEGRAM_ID, 0,
    'in_progress',
    'test_escalation'
))

print("✅ Overdue test tasks created!")
print("\n📋 Task 1: 5 hours overdue (Level 1)")
print("   → Should trigger assignee alert on next hour")
print("\n📋 Task 2: 9 hours overdue (Level 2)")
print("   → Should escalate to manager on next hour")
print("\n⏰ Escalation scheduler runs every hour")
print("📱 Wait for next hour or manually trigger by restarting bot")
