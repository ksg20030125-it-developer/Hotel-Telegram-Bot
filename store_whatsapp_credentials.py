#!/usr/bin/env python3
"""
Store WhatsApp/Twilio credentials securely in database

Usage:
    python store_whatsapp_credentials.py
    
This script will prompt you for WhatsApp credentials and store them encrypted in the database.
"""

import os
import sys
from getpass import getpass


def main():
    """Main function to store WhatsApp credentials"""
    print("=" * 60)
    print("  WhatsApp/Twilio Credentials Storage Utility")
    print("=" * 60)
    print()
    print("This utility will securely store your WhatsApp/Twilio credentials")
    print("in the encrypted database.")
    print()
    
    # Import required modules
    try:
        from database import DatabaseManager, save_whatsapp_credentials
        from security_manager import SecurityManager
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("Make sure you're running this from the correct directory.")
        return 1
    
    # Get credentials from user
    print("Please enter your Twilio credentials:")
    print("(You can find these in your Twilio Console)")
    print()
    
    account_sid = input("Twilio Account SID: ").strip()
    if not account_sid:
        print("❌ Account SID is required")
        return 1
    
    auth_token = getpass("Twilio Auth Token (hidden): ").strip()
    if not auth_token:
        print("❌ Auth Token is required")
        return 1
    
    whatsapp_from = input("WhatsApp-enabled number (E.164 format, e.g., +14155238886): ").strip()
    if not whatsapp_from:
        print("❌ WhatsApp number is required")
        return 1
    
    # Validate format
    if not whatsapp_from.startswith('+'):
        print("⚠️  WhatsApp number should start with '+' (E.164 format)")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return 1
    
    print()
    print("=" * 60)
    print("Credentials Summary:")
    print(f"  Account SID: {account_sid[:10]}...{account_sid[-4:]}")
    print(f"  Auth Token: {auth_token[:4]}...{auth_token[-4:]}")
    print(f"  WhatsApp From: {whatsapp_from}")
    print("=" * 60)
    print()
    
    confirm = input("Save these credentials to database? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled by user")
        return 0
    
    print()
    print("💾 Saving credentials to database...")
    
    # Initialize database
    db = DatabaseManager()
    if not db.connect():
        print("❌ Failed to connect to database")
        return 1
    
    # Test encryption/decryption
    try:
        sec_mgr = SecurityManager()
        test_encrypted = sec_mgr.encrypt("test")
        test_decrypted = sec_mgr.decrypt(test_encrypted)
        if test_decrypted != "test":
            print("❌ Encryption test failed")
            return 1
        print("✅ Encryption system verified")
    except Exception as e:
        print(f"❌ Encryption system error: {e}")
        return 1
    
    # Save credentials
    try:
        success = save_whatsapp_credentials(db, account_sid, auth_token, whatsapp_from)
        
        if success:
            print("✅ WhatsApp credentials saved successfully!")
            print()
            print("You can now use WhatsApp messaging features in the bot.")
            print()
            
            # Test retrieval
            print("🔍 Testing credential retrieval...")
            from database import get_whatsapp_credentials_from_db
            
            retrieved = get_whatsapp_credentials_from_db(db)
            if retrieved:
                print("✅ Credentials retrieved successfully!")
                print(f"   Account SID: {retrieved['account_sid'][:10]}...{retrieved['account_sid'][-4:]}")
                print(f"   Auth Token: {'*' * 20}")
                print(f"   WhatsApp From: {retrieved['whatsapp_from']}")
            else:
                print("⚠️  Warning: Could not retrieve credentials (but save was successful)")
        else:
            print("❌ Failed to save credentials")
            return 1
            
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.disconnect()
    
    print()
    print("=" * 60)
    print("✅ All done!")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
