"""
Hotel Management Bot - Build Script
Creates standalone executable without Python installation
"""

import PyInstaller.__main__
import os
import shutil
from pathlib import Path

# 현재 디렉토리
current_dir = Path(__file__).parent

# 빌드 옵션
PyInstaller.__main__.run([
    'main.py',                          # Main file
    '--name=HotelManagementBot',        # Executable name
    '--onefile',                        # Single file build
    '--windowed',                       # Hide console window (remove if needed)
    '--icon=NONE',                      # Icon file (NONE if not available)
    
    # Include required modules
    '--hidden-import=telegram',
    '--hidden-import=telegram.ext',
    '--hidden-import=psycopg2',
    '--hidden-import=openai',
    '--hidden-import=cryptography',
    '--hidden-import=twilio',
    '--hidden-import=twilio.rest',
    
    # Include additional data files
    '--add-data=.env;.',
    
    # Exclude modules
    '--exclude-module=matplotlib',
    '--exclude-module=numpy',
    '--exclude-module=pandas',
    
    # Build directories
    '--distpath=release',
    '--workpath=build',
    '--specpath=.',
    
    # Cleanup options
    '--clean',
    '--noconfirm',
])

print("\n" + "="*60)
print("✅ Build Complete!")
print("="*60)
print(f"\n📁 Executable location: {current_dir / 'release' / 'HotelManagementBot.exe'}")
print("\n📝 To run on another computer:")
print("   1. Copy HotelManagementBot.exe from release folder")
print("   2. Copy .env file to same folder")
print("   3. Change DB_HOST in .env to this computer's IP")
print("   4. Run HotelManagementBot.exe")
print("\n⚠️  Important:")
print("   - PostgreSQL database must run on this computer")
print("   - Allow PostgreSQL port (5432) in firewall")
print("   - Change DB_HOST in .env to network IP")
print("="*60 + "\n")
