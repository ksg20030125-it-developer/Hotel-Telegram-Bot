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
print("📱 WHATSAPP STATUS CHECK")
print("="*60)

# Check WhatsApp credentials
print("\n🔐 WhatsApp Credentials:")
cursor.execute("""
    SELECT account_sid, whatsapp_from, auth_token 
    FROM tbl_whatsapp_credentials 
    ORDER BY id DESC LIMIT 1
""")
cred = cursor.fetchone()
if cred:
    print(f"   Account SID: {cred['account_sid'][:20]}...")
    print(f"   WhatsApp From: {cred['whatsapp_from']}")
    print(f"   Auth Token: {'✓ Set' if cred['auth_token'] else '✗ Missing'}")
else:
    print("   ❌ No credentials found")

# Check WhatsApp logs
print("\n📊 WhatsApp Logs:")
cursor.execute("SELECT COUNT(*) as count FROM tbl_whatsapp_logs")
total = cursor.fetchone()['count']
print(f"   Total logs: {total}")

if total > 0:
    cursor.execute("""
        SELECT id, recipient, recipient_name, message_body, status, 
               error_message, sent_at
        FROM tbl_whatsapp_logs
        ORDER BY sent_at DESC
        LIMIT 10
    """)
    logs = cursor.fetchall()
    
    print(f"\n📬 Recent {len(logs)} WhatsApp logs:")
    for log in logs:
        status_icon = "✅" if log['status'] == 'sent' else "❌"
        print(f"\n{status_icon} Log #{log['id']}")
        print(f"   To: {log['recipient_name'] or 'N/A'} ({log['recipient']})")
        print(f"   Message: {log['message_body'][:50]}...")
        print(f"   Status: {log['status']}")
        print(f"   Time: {log['sent_at']}")
        if log['error_message']:
            print(f"   Error: {log['error_message']}")
else:
    print("   ⚠️ No WhatsApp messages have been logged yet")

# Check employees with WhatsApp numbers
print("\n👥 Employees with WhatsApp:")
cursor.execute("""
    SELECT employee_id, name, whatsapp, department
    FROM tbl_employeer
    WHERE whatsapp IS NOT NULL AND whatsapp != ''
    ORDER BY name
    LIMIT 10
""")
employees = cursor.fetchall()
print(f"   Found {len(employees)} employees with WhatsApp numbers:")
for emp in employees:
    print(f"   - {emp['name']} ({emp['department']}): {emp['whatsapp']}")

cursor.close()
conn.close()
print("\n" + "="*60)
