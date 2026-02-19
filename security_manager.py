"""
Security Manager - Encrypted Secrets Storage
Handles encryption/decryption of sensitive data stored in database
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import psycopg2
from typing import Optional, Dict


class SecurityManager:
    """
    Manages encrypted storage of sensitive credentials in database
    Uses Fernet symmetric encryption with a master key derived from system info
    """
    
    def __init__(self, db_config: Dict[str, str], ensure_table: bool = True):
        """
        Initialize security manager
        
        Args:
            db_config: Database connection parameters (host, port, name, user, password)
            ensure_table: If True, creates table if not exists. Set False for read-only operations.
        """
        self.db_config = db_config
        self.connection = None
        self._cipher = None
        if ensure_table:
            self._ensure_table_exists()
    
    def _get_master_key(self) -> bytes:
        """
        Generate master encryption key from system-specific data
        This creates a deterministic key based on database credentials
        
        Returns:
            32-byte encryption key
        """
        # Use database password as base for key derivation
        # In production, consider using hardware security module or key management service
        password = self.db_config['password'].encode()
        salt = b'hotel_management_system_2026'  # Static salt (in production, store securely)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _get_cipher(self) -> Fernet:
        """Get or create Fernet cipher instance"""
        if self._cipher is None:
            key = self._get_master_key()
            self._cipher = Fernet(key)
        return self._cipher
    
    def _get_connection(self):
        """Get database connection"""
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['name'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
        return self.connection
    
    def _ensure_table_exists(self):
        """Create encrypted secrets table if not exists"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_encrypted_secrets (
                    secret_key VARCHAR(100) PRIMARY KEY,
                    encrypted_value TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create trigger to update updated_at
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_secret_timestamp()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            cursor.execute("""
                DROP TRIGGER IF EXISTS trigger_update_secret_timestamp ON tbl_encrypted_secrets;
                CREATE TRIGGER trigger_update_secret_timestamp
                BEFORE UPDATE ON tbl_encrypted_secrets
                FOR EACH ROW
                EXECUTE FUNCTION update_secret_timestamp();
            """)
            
            conn.commit()
            print("✅ Encrypted secrets table initialized")
            
        except Exception as e:
            print(f"❌ Error creating secrets table: {e}")
            if self.connection:
                self.connection.rollback()
    
    def store_secret(self, key: str, value: str, description: str = "") -> bool:
        """
        Encrypt and store a secret in database
        
        Args:
            key: Unique identifier for the secret (e.g., 'telegram_bot_token')
            value: Plain text value to encrypt and store
            description: Optional description of what this secret is for
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cipher = self._get_cipher()
            encrypted_value = cipher.encrypt(value.encode()).decode()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tbl_encrypted_secrets (secret_key, encrypted_value, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (secret_key) 
                DO UPDATE SET encrypted_value = EXCLUDED.encrypted_value,
                             description = EXCLUDED.description,
                             updated_at = CURRENT_TIMESTAMP
            """, (key, encrypted_value, description))
            
            conn.commit()
            print(f"✅ Secret stored: {key}")
            return True
            
        except Exception as e:
            print(f"❌ Error storing secret '{key}': {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Retrieve and decrypt a secret from database
        
        Args:
            key: Unique identifier for the secret
        
        Returns:
            Decrypted plain text value or None if not found
        
        Security: Secret values are never logged
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT encrypted_value FROM tbl_encrypted_secrets
                WHERE secret_key = %s
            """, (key,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            cipher = self._get_cipher()
            decrypted_value = cipher.decrypt(result[0].encode()).decode()
            return decrypted_value
            
        except Exception as e:
            # Log error without exposing key name or value
            return None
    
    def delete_secret(self, key: str) -> bool:
        """
        Delete a secret from database
        
        Args:
            key: Unique identifier for the secret
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM tbl_encrypted_secrets
                WHERE secret_key = %s
            """, (key,))
            
            conn.commit()
            print(f"✅ Secret deleted: {key}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting secret '{key}': {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def list_secrets(self) -> list:
        """
        List all stored secret keys (without values)
        
        Returns:
            List of tuples: (key, description, updated_at)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT secret_key, description, updated_at
                FROM tbl_encrypted_secrets
                ORDER BY secret_key
            """)
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error listing secrets: {e}")
            return []
    
    def encrypt(self, value: str) -> bytes:
        """
        Encrypt a string value and return encrypted bytes
        
        Args:
            value: Plain text string to encrypt
        
        Returns:
            Encrypted bytes
        """
        cipher = self._get_cipher()
        return cipher.encrypt(value.encode())
    
    def decrypt(self, encrypted_value: bytes) -> str:
        """
        Decrypt encrypted bytes and return plain text string
        
        Args:
            encrypted_value: Encrypted bytes to decrypt
        
        Returns:
            Decrypted plain text string
        """
        cipher = self._get_cipher()
        return cipher.decrypt(encrypted_value).decode()
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            print("🔒 Security manager connection closed")


def migrate_env_to_encrypted_storage():
    """
    Migration script to move secrets from .env to encrypted database storage
    Run this once during initial setup
    """
    import os
    from dotenv import load_dotenv
    
    # Load current .env file
    load_dotenv()
    
    # Database config (non-sensitive)
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'name': os.getenv('DB_NAME', 'hotel_manage'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    
    # Initialize security manager
    security = SecurityManager(db_config)
    
    # Define secrets to migrate
    secrets_to_migrate = [
        ('telegram_bot_token', os.getenv('TELEGRAM_BOT_TOKEN'), 'Telegram Bot API Token'),
        ('openai_api_key', os.getenv('OPENAI_API_KEY'), 'OpenAI API Key for AI Analysis'),
        ('anthropic_api_key', os.getenv('ANTHROPIC_API_KEY'), 'Anthropic Claude API Key'),
        ('sender_email', os.getenv('SENDER_EMAIL'), 'Gmail address for sending emails'),
        ('app_password', os.getenv('APP_PASSWORD'), 'Gmail app-specific password'),
    ]
    
    print("\n" + "="*60)
    print("MIGRATING SECRETS TO ENCRYPTED DATABASE STORAGE")
    print("="*60 + "\n")
    
    success_count = 0
    for key, value, description in secrets_to_migrate:
        if value:
            if security.store_secret(key, value, description):
                success_count += 1
                print(f"  ✓ Migrated: {key}")
        else:
            print(f"  ⊘ Skipped (not set): {key}")
    
    print(f"\n✅ Migration complete: {success_count} secrets stored securely")
    print("⚠️  Next step: Update .env file to remove sensitive data\n")
    
    security.close()
    return success_count > 0


if __name__ == "__main__":
    # Run migration if executed directly
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        # Verification mode
        print("\n" + "="*60)
        print("VERIFYING ENCRYPTED SECRETS STORAGE")
        print("="*60 + "\n")
        
        from dotenv import load_dotenv
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
        secrets = security.list_secrets()
        for key, desc, updated in secrets:
            print(f"  🔑 {key}")
            print(f"     Description: {desc}")
            print(f"     Last updated: {updated}")
            
            # Test decryption
            value = security.get_secret(key)
            if value:
                # Show masked value
                if len(value) > 20:
                    masked = value[:8] + "..." + value[-4:]
                else:
                    masked = value[:4] + "..." if len(value) > 8 else "***"
                print(f"     ✅ Decrypted successfully: {masked}")
            else:
                print(f"     ❌ Failed to decrypt")
            print()
        
        print(f"✅ Verification complete: {len(secrets)} secrets verified\n")
        security.close()
    else:
        # Migration mode
        migrate_env_to_encrypted_storage()
