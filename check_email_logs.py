"""
Check email logs in database
"""
from database import DatabaseManager

db = DatabaseManager()
db.connect()

print("\n" + "="*60)
print("📧 EMAIL LOGS CHECK")
print("="*60)

# Check if table exists
db.cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'tbl_email_logs'
    )
""")
exists = db.cursor.fetchone()[0]

if not exists:
    print("❌ tbl_email_logs table does not exist!")
else:
    print("✅ tbl_email_logs table exists")
    
    # Get column names
    db.cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'tbl_email_logs'
        ORDER BY ordinal_position
    """)
    columns = db.cursor.fetchall()
    print(f"\n📋 Table structure ({len(columns)} columns):")
    for col in columns:
        print(f"   - {col[0]}: {col[1]}")
    
    # Get total count
    db.cursor.execute("SELECT COUNT(*) FROM tbl_email_logs")
    total = db.cursor.fetchone()[0]
    print(f"\n📊 Total email logs: {total}")
    
    if total > 0:
        # Get recent logs
        db.cursor.execute("""
            SELECT id, recipient, recipient_name, subject, status, 
                   sent_at, smtp_response_code, error_message
            FROM tbl_email_logs
            ORDER BY sent_at DESC
            LIMIT 10
        """)
        logs = db.cursor.fetchall()
        
        print(f"\n📬 Recent {len(logs)} logs:")
        for log in logs:
            log_id, recipient, recipient_name, subject, status, sent_at, smtp_code, error = log
            status_icon = "✅" if status == "sent" else "❌"
            print(f"\n{status_icon} Log #{log_id}")
            print(f"   To: {recipient_name or 'N/A'} <{recipient}>")
            print(f"   Subject: {subject}")
            print(f"   Status: {status}")
            print(f"   Time: {sent_at}")
            print(f"   SMTP Code: {smtp_code}")
            if error:
                print(f"   Error: {error}")
    else:
        print("\n⚠️ No logs found in database!")
        print("   This means no emails have been sent yet, or logs were not recorded.")

db.disconnect()
print("\n" + "="*60)
