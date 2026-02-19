import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="hotel_manage",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor(cursor_factory=RealDictCursor)

print("\n📧 EMAIL LOGS:")
cursor.execute("SELECT COUNT(*) as count FROM tbl_email_logs")
print(f"   Total: {cursor.fetchone()['count']}")

cursor.execute("""
    SELECT recipient, subject, status, error_message, sent_at
    FROM tbl_email_logs
    ORDER BY sent_at DESC
    LIMIT 5
""")
for log in cursor.fetchall():
    status_icon = "✅" if log['status'] == 'sent' else "❌"
    print(f"\n{status_icon} {log['recipient']}")
    print(f"   Subject: {log['subject']}")
    print(f"   Time: {log['sent_at']}")
    if log['error_message']:
        print(f"   Error: {log['error_message'][:80]}")

print("\n\n📱 WHATSAPP LOGS:")
cursor.execute("SELECT COUNT(*) as count FROM tbl_whatsapp_logs")
print(f"   Total: {cursor.fetchone()['count']}")

cursor.execute("""
    SELECT recipient, message_body, status, error_message, sent_at
    FROM tbl_whatsapp_logs
    ORDER BY sent_at DESC
    LIMIT 5
""")
for log in cursor.fetchall():
    status_icon = "✅" if log['status'] == 'sent' else "❌"
    print(f"\n{status_icon} {log['recipient']}")
    print(f"   Message: {log['message_body'][:60]}...")
    print(f"   Time: {log['sent_at']}")
    if log['error_message']:
        print(f"   Error: {log['error_message'][:80]}")

cursor.close()
conn.close()
