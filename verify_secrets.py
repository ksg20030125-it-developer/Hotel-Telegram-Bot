"""
Verification Script for Encrypted Secrets
Run this to verify that all secrets are properly stored and can be decrypted
"""
import os
from dotenv import load_dotenv
from security_manager import SecurityManager

def verify_encrypted_secrets():
    """Verify all encrypted secrets in database"""
    
    print("\n" + "="*60)
    print("VERIFYING ENCRYPTED SECRETS STORAGE")
    print("="*60 + "\n")
    
    load_dotenv()
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'name': os.getenv('DB_NAME', 'hotel_manage'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    
    security = SecurityManager(db_config)
    
    print("📋 Stored Secrets:")
    print("-" * 60)
    
    secrets = security.list_secrets()
    
    if not secrets:
        print("⚠️  No secrets found in database!")
        print("    Run: py security_manager.py (to migrate)")
        security.close()
        return False
    
    success_count = 0
    fail_count = 0
    
    for key, desc, updated in secrets:
        print(f"\n🔑 {key}")
        print(f"   Description: {desc}")
        print(f"   Last updated: {updated}")
        
        # Test decryption
        value = security.get_secret(key)
        if value:
            # Show masked value
            if len(value) > 20:
                masked = value[:8] + "..." + value[-4:]
            else:
                masked = value[:4] + "..." if len(value) > 8 else "***"
            print(f"   ✅ Decrypted: {masked}")
            success_count += 1
        else:
            print(f"   ❌ Failed to decrypt")
            fail_count += 1
    
    print("\n" + "="*60)
    print(f"✅ Verification complete:")
    print(f"   • Total secrets: {len(secrets)}")
    print(f"   • Successfully decrypted: {success_count}")
    print(f"   • Failed: {fail_count}")
    print("="*60 + "\n")
    
    security.close()
    return fail_count == 0

if __name__ == "__main__":
    success = verify_encrypted_secrets()
    exit(0 if success else 1)
