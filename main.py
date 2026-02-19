import os
import sys
import asyncio
import subprocess
import py_compile
import glob
import time
from dotenv import load_dotenv
from database import get_database_connection, DatabaseManager, create_action_history_table
from bot import HotelBot
from security_manager import SecurityManager

# Enable UTF-8 mode for Windows (prevents UnicodeEncodeError with emoji)
os.environ.setdefault("PYTHONUTF8", "1")

# Windows asyncio event loop policy setting (error prevention)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def main():
    """Main function"""
    print("=" * 50)
    print("Hotel Management System Starting")
    print("=" * 50)
    
    # When running as EXE, find .env file in the same directory as executable
    if getattr(sys, 'frozen', False):
        # When packaged with PyInstaller, use executable directory
        env_path = os.path.join(os.path.dirname(sys.executable), '.env')
    else:
        # In development, use script file directory
        env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    # Load environment variables (non-sensitive data only)
    load_dotenv(env_path)
    
    # Initialize database connection to retrieve encrypted secrets
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'name': os.getenv('DB_NAME', 'hotel_manage'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    
    # Initialize security manager for encrypted secrets
    security = SecurityManager(db_config)
    
    # Retrieve all sensitive data from encrypted storage at once
    telegram_token = security.get_secret('telegram_bot_token')
    openai_api_key = security.get_secret('openai_api_key') or ''
    sender_email = security.get_secret('sender_email') or ''
    app_password = security.get_secret('app_password') or ''
    
    # Close security manager connection
    security.close()
    
    # Set secrets cache for AI module (avoids multiple DB connections)
    from email_ai_analyzer import set_secrets_cache
    set_secrets_cache({
        'openai_api_key': openai_api_key,
        'sender_email': sender_email,
        'app_password': app_password
    })
    
    # Initialize email service with credentials
    try:
        from email_service import init_email_service
        init_email_service(sender_email, app_password)
    except Exception as e:
        print(f"⚠️ Could not initialize email service: {e}")
    
    if not telegram_token:
        print("❌ Error: telegram_bot_token not found in encrypted storage.")
        print("📝 Please run: python security_manager.py")
        return
    
    # Connect to database
    db = get_database_connection()
    db.create_tables()
    
    # Add check_admin column to existing table (if not exists)
    db.add_check_admin_column()
    
    # Add guest columns to customer_rooms table (if not exists)
    db.add_customer_rooms_guest_columns()
    
    # Add contact columns to employee table (if not exists)
    db.add_employee_contact_columns()
    
    # Create action history table
    create_action_history_table(db)
    
    # Initialize accounting tasks table and sample data
    from database import create_accounting_tasks_table, insert_sample_accounting_data
    create_accounting_tasks_table(db)
    insert_sample_accounting_data(db)
    
    # Initialize hotel finance tables and sample data
    from database import upgrade_hotel_accounts_table, create_financial_transactions_table, insert_sample_financial_data
    upgrade_hotel_accounts_table(db)
    create_financial_transactions_table(db)
    insert_sample_financial_data(db)
    
    # Initialize kitchen and inventory tables
    from database import create_kitchen_menu_table, create_inventory_table
    create_kitchen_menu_table(db)
    create_inventory_table(db)
    
    print("✅ Database ready!")
    
    # Auto-register first admin (only if no admin exists)
    result = db.execute_query("SELECT COUNT(*) FROM tbl_employeer WHERE department = 'Management'")
    admin_count = result[0][0] if result else 0
    
    if admin_count == 0:
        print("\n⚠️  No admin registered. Registering first admin...")
        print("📝 Registering Telegram ID 8261255116 as admin.")
        
        db.execute_query(
            "INSERT INTO tbl_employeer (employee_id, telegram_user_id, name, department) VALUES (%s, %s, %s, %s)",
            ('EMP00001', 8261255116, 'Sven', 'Management')
        )
        print("✅ First admin registered!")
    else:
        print(f"✅ {admin_count} admin(s) already registered.")
    
    # Initialize WhatsApp service with credentials from database (after DB is connected)
    try:
        from database import get_whatsapp_credentials_from_db
        from whatsapp_service import init_whatsapp_service
        
        whatsapp_creds = get_whatsapp_credentials_from_db(db)
        if whatsapp_creds:
            init_whatsapp_service(
                whatsapp_creds['account_sid'],
                whatsapp_creds['auth_token'],
                whatsapp_creds['whatsapp_from']
            )
            print("✅ WhatsApp service initialized")
        else:
            print("⚠️ WhatsApp credentials not found in database")
            print("   Run: python store_whatsapp_credentials.py")
    except Exception as e:
        print(f"⚠️ Could not initialize WhatsApp service: {e}")
    
    # Start Telegram bot
    bot = HotelBot(telegram_token, db)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n⚠️ User interrupted the program...")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
    finally:
        db.disconnect()
        print("=" * 50)
        print("Program Terminated")
        print("=" * 50)


if __name__ == "__main__":
    # Simple CLI: support 'check' and 'run' commands
    # Usage:
    #   python main.py            -> normal start
    #   python main.py check      -> analyze project and restart the program
    #   python main.py run        -> install requirements (if any) and run

    def check_project():
        """
        Perform syntax checks on .py files and verify image files referenced in fix_icons.py.
        After analysis, restart the program without CLI args.
        """

        errors = []
        py_files = glob.glob("*.py")
        for f in py_files:
            try:
                py_compile.compile(f, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append((f, str(e)))

        # Check referenced image files in fix_icons.py (if exists)
        missing_images = []
        icons_path = os.path.join(os.path.dirname(__file__), "fix_icons.py")
        if os.path.exists(icons_path):
            try:
                with open(icons_path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                import re
                imgs = re.findall(r"[\"']([\w\-./\\]+\.(?:png|jpg|jpeg|svg))[\"']", content, re.IGNORECASE)
                for img in imgs:
                    img_path = os.path.join(os.path.dirname(__file__), img)
                    if not os.path.exists(img_path):
                        missing_images.append(img)
            except Exception as e:
                print(f"Error checking images: {e}")

        print("\nCheck results:")
        if errors:
            print(f"❌ Syntax errors found: {len(errors)} files")
            for f, msg in errors:
                print(f"- {f}: {msg}")
        else:
            print("✅ All .py files passed syntax check")

        if missing_images:
            print(f"❌ Missing image files: {len(missing_images)}")
            for img in missing_images:
                print(f"- {img}")
        else:
            print("✅ Image files check passed")

        # Restart the program (without CLI arg to start normally)
        print("\nRestarting project...")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable, __file__])

    def run_and_rebuild():
        """
        Install requirements (if requirements.txt exists) and run the program.
        """
        req = os.path.join(os.path.dirname(__file__), "requirements.txt")
        if os.path.exists(req):
            print("requirements.txt found: Installing dependencies...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", req], check=True)
                print("✅ Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies: {e}")
        else:
            print("requirements.txt not found - skipping installation")

        print("Running program...")
        time.sleep(0.5)
        os.execv(sys.executable, [sys.executable, __file__])

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "check":
            check_project()
        elif cmd == "run":
            run_and_rebuild()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python main.py [check|run]")
    else:
        main()
