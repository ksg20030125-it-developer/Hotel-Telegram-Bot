

import subprocess
import sys
from pathlib import Path

# Current directory
current_dir = Path(__file__).parent

print("="*60)
print("🏨 Hotel Management Bot Build Starting")
print("="*60)

# PyInstaller command
cmd = [
    sys.executable,
    '-m', 'PyInstaller',
    'main.py',
    '--name=HotelManagementBot',
    '--onefile',
    '--console',  # Show console window
    '--noupx',    # Disable UPX compression (faster)
    
    # Required modules
    '--hidden-import=telegram',
    '--hidden-import=telegram.ext',
    '--hidden-import=psycopg2',
    '--hidden-import=openai',
    '--hidden-import=cryptography',
    '--hidden-import=cryptography.fernet',
    '--hidden-import=twilio',
    '--hidden-import=twilio.rest',
    '--hidden-import=email_ai_analyzer',
    '--hidden-import=whatsapp_service',
    '--hidden-import=notification_manager',
    '--hidden-import=security_manager',
    '--hidden-import=database',
    '--hidden-import=languages',
    '--hidden-import=templates',
    '--hidden-import=email_templates',
    '--hidden-import=whatsapp_templates',
    
    # Output directories
    '--distpath=release',
    '--workpath=build',
    '--specpath=.',
    
    # Options
    '--clean',
    '--noconfirm',
]

# Run build
print("\n🔨 Running PyInstaller...")
result = subprocess.run(cmd, cwd=current_dir)

if result.returncode == 0:
    print("\n" + "="*60)
    print("✅ Build Successful!")
    print("="*60)
    print(f"\n📁 Executable location:")
    print(f"   {current_dir / 'release' / 'HotelManagementBot.exe'}")
    print("\n📋 Deployment files:")
    print("   ✓ HotelManagementBot.exe")
    print("   ✓ .env (configuration file)")
    print("\n📝 To run on another computer:")
    print("   1. Copy release/HotelManagementBot.exe")
    print("   2. Copy .env file to same location")
    print("   3. Edit .env file:")
    print("      DB_HOST=localhost → DB_HOST=<this_computer_IP>")
    print("   4. Double-click HotelManagementBot.exe to run")
    print("\n⚠️  Database setup:")
    print("   - PostgreSQL continues running on this computer")
    print("   - postgresql.conf: listen_addresses = '*'")
    print("   - pg_hba.conf: allow external connections")
    print("   - Firewall: allow port 5432")
    print("="*60 + "\n")
else:
    print("\n❌ Build Failed!")
    print(f"Error code: {result.returncode}")
    sys.exit(1)
