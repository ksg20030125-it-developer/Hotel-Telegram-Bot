import psycopg2
from psycopg2.extras import RealDictCursor

# Direct database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="hotel_manage",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "="*60)
print("📧 DIRECT EMAIL LOGS CHECK")
print("="*60)

# Check table
cursor.execute("SELECT COUNT(*) as count FROM tbl_email_logs")
total = cursor.fetchone()['count']
print(f"\n📊 Total email logs: {total}")

if total > 0:
    cursor.execute("""
        SELECT id, recipient, recipient_name, subject, status, 
               sent_at, smtp_response_code, error_message
        FROM tbl_email_logs
        ORDER BY sent_at DESC
        LIMIT 10
    """)
    logs = cursor.fetchall()
    
    print(f"\n📬 Recent {len(logs)} logs:")
    for log in logs:
        status_icon = "✅" if log['status'] == "sent" else "❌"
        print(f"\n{status_icon} Log #{log['id']}")
        print(f"   To: {log['recipient_name'] or 'N/A'} <{log['recipient']}>")
        print(f"   Subject: {log['subject']}")
        print(f"   Status: {log['status']}")
        print(f"   Time: {log['sent_at']}")
        if log['error_message']:
            print(f"   Error: {log['error_message'][:100]}")
else:
    print("\n⚠️ No logs in database - emails have not been recorded yet")

cursor.close()
conn.close()
print("\n" + "="*60)
