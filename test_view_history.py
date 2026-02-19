"""
Test script to view task status history
"""
from database import get_database_connection, get_task_status_history

db = get_database_connection()

# Get recent tasks
print("📊 Recent Task Status History\n")

result = db.execute_query("""
    SELECT DISTINCT task_id, task_table 
    FROM tbl_task_status_history 
    ORDER BY task_id DESC 
    LIMIT 5
""")

if result:
    for row in result:
        task_id = row[0]
        task_table = row[1]
        
        print(f"═══════════════════════════════")
        print(f"📋 Task ID: {task_id} (Table: {task_table})")
        print(f"───────────────────────────────")
        
        history = get_task_status_history(db, task_id, task_table)
        
        for h in history:
            status_change = f"{h['old_status']} → {h['new_status']}" if h['old_status'] else f"Created as {h['new_status']}"
            print(f"🔄 {status_change}")
            print(f"   👤 By: {h['changed_by_name'] or h['changed_by']}")
            print(f"   ⏰ At: {h['changed_at']}")
            if h['notes']:
                print(f"   📝 Notes: {h['notes']}")
            print()
else:
    print("No task history found yet.")
    print("💡 Try accepting or completing a task first!")
