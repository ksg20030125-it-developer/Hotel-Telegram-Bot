"""
WhatsApp Service for Hotel Management Bot
Handles sending WhatsApp messages via Twilio API
"""

import os
import base64
import urllib.parse
import urllib.request
import json
from datetime import datetime
from typing import List, Dict, Optional


def get_whatsapp_credentials() -> tuple:
    """
    Retrieve WhatsApp/Twilio credentials from cache
    
    Returns:
        Tuple of (account_sid, auth_token, whatsapp_from)
    """
    account_sid = None
    auth_token = None
    whatsapp_from = None
    
    try:
        # Import the cached secrets from database or secure storage
        from database import DatabaseManager
        db = DatabaseManager()
        db.connect()
        
        # Get encrypted credentials from database
        credentials = db.get_whatsapp_credentials()
        if credentials:
            account_sid = credentials.get('account_sid')
            auth_token = credentials.get('auth_token')
            whatsapp_from = credentials.get('whatsapp_from')
            
            print(f"📱 WhatsApp credentials from database:")
            print(f"   - Account SID: {'✓ ' + account_sid[:10] + '...' if account_sid else '✗ Empty'}")
            print(f"   - Auth Token: {'✓ (length: ' + str(len(auth_token)) + ')' if auth_token else '✗ Empty'}")
            print(f"   - From Number: {'✓ ' + whatsapp_from if whatsapp_from else '✗ Empty'}")
        
        db.disconnect()
        
    except Exception as e:
        print(f"⚠️ Could not retrieve WhatsApp credentials from database: {e}")
    
    # Fallback to environment variables
    if not account_sid:
        account_sid = os.getenv('TWILIO_SID', '')
    if not auth_token:
        auth_token = os.getenv('TWILIO_TOKEN', '')
    if not whatsapp_from:
        whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM', '')
    
    return account_sid, auth_token, whatsapp_from


class WhatsAppService:
    """Service class for sending WhatsApp messages via Twilio"""
    
    def __init__(self, account_sid: str = None, auth_token: str = None, whatsapp_from: str = None):
        """
        Initialize WhatsApp service
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            whatsapp_from: WhatsApp-enabled Twilio number (E.164 format)
        """
        # Use provided credentials or load from cache
        if account_sid and auth_token and whatsapp_from:
            self.account_sid = account_sid
            self.auth_token = auth_token
            self.whatsapp_from = whatsapp_from
            print(f"✅ WhatsAppService initialized with provided credentials")
        else:
            # Fallback to loading from cache
            self.account_sid, self.auth_token, self.whatsapp_from = get_whatsapp_credentials()
            if self.account_sid and self.auth_token and self.whatsapp_from:
                print(f"✅ WhatsAppService initialized with cached credentials")
            else:
                print(f"⚠️ WhatsAppService initialized without credentials")
    
    def send_message(self, to_number: str, message_body: str) -> Dict:
        """
        Send a WhatsApp message via Twilio API
        
        Args:
            to_number: Recipient phone number in E.164 format (e.g., +381601234567)
            message_body: Message text to send
            
        Returns:
            Dictionary with response data or error information
        """
        if not self.account_sid or not self.auth_token or not self.whatsapp_from:
            return {
                'success': False,
                'error': 'WhatsApp credentials not configured'
            }
        
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            payload = {
                "From": f"whatsapp:{self.whatsapp_from}",
                "To": f"whatsapp:{to_number}",
                "Body": message_body
            }
            data = urllib.parse.urlencode(payload).encode("utf-8")
            
            auth_raw = f"{self.account_sid}:{self.auth_token}".encode("utf-8")
            auth_b64 = base64.b64encode(auth_raw).decode("ascii")
            
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Authorization", f"Basic {auth_b64}")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_text = resp.read().decode("utf-8")
                response_data = json.loads(resp_text)
                
                return {
                    'success': True,
                    'message_sid': response_data.get('sid'),
                    'status': response_data.get('status'),
                    'response': response_data
                }
        
        except urllib.error.HTTPError as he:
            err_text = he.read().decode('utf-8', errors='ignore')
            try:
                error_data = json.loads(err_text)
                error_msg = error_data.get('message', str(he))
            except:
                error_msg = err_text
            
            return {
                'success': False,
                'error': f"HTTP {he.code}: {error_msg}"
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_bulk_messages(self, recipients: List[Dict], message_body: str) -> Dict:
        """
        Send WhatsApp messages to multiple recipients
        
        Args:
            recipients: List of dicts with 'whatsapp' and 'name' keys
            message_body: Message text to send
            
        Returns:
            Dictionary with success/failure counts and details
        """
        results = {
            'total': len(recipients),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        # Import WhatsApp template
        from whatsapp_templates import create_whatsapp_message, format_whatsapp_body
        
        for recipient in recipients:
            whatsapp_number = recipient.get('whatsapp')
            name = recipient.get('name', 'Unknown')
            
            if not whatsapp_number:
                results['failed'] += 1
                results['details'].append({
                    'name': name,
                    'success': False,
                    'error': 'No WhatsApp number'
                })
                continue
            
            # Format message body
            formatted_body = format_whatsapp_body(message_body)
            
            # Create beautiful WhatsApp message
            formatted_message = create_whatsapp_message(
                recipient_name=name,
                message_body=formatted_body,
                sender_name="Hotel Manager",
                sender_phone=self.whatsapp_from if self.whatsapp_from else "",
                hotel_name="Grand Hotel",
                category="notification"
            )
            
            # Send message
            result = self.send_message(whatsapp_number, formatted_message)
            
            if result.get('success'):
                results['success'] += 1
                results['details'].append({
                    'name': name,
                    'whatsapp': whatsapp_number,
                    'success': True,
                    'message_sid': result.get('message_sid')
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'name': name,
                    'whatsapp': whatsapp_number,
                    'success': False,
                    'error': result.get('error')
                })
        
        return results
    
    def send_notification(self, to_number: str, title: str, message: str, notification_type: str = 'info') -> bool:
        """
        Send a formatted notification message
        
        Args:
            to_number: Recipient phone number
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, alert, success)
            
        Returns:
            True if successful
        """
        # Emoji mapping for notification types
        type_emojis = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'alert': '🚨',
            'success': '✅',
            'task': '📋',
            'reminder': '🔔'
        }
        
        emoji = type_emojis.get(notification_type, 'ℹ️')
        
        formatted_message = f"{emoji} *{title}*\n\n{message}\n\n_Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        result = self.send_message(to_number, formatted_message)
        return result.get('success', False)


# Singleton instance
_whatsapp_service = None


def get_whatsapp_service(account_sid: str = None, auth_token: str = None, whatsapp_from: str = None) -> WhatsAppService:
    """
    Get or create the WhatsAppService singleton
    
    Args:
        account_sid: Twilio Account SID (optional)
        auth_token: Twilio Auth Token (optional)
        whatsapp_from: WhatsApp number (optional)
    """
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService(account_sid, auth_token, whatsapp_from)
    return _whatsapp_service


def init_whatsapp_service(account_sid: str, auth_token: str, whatsapp_from: str):
    """
    Initialize WhatsApp service with credentials
    Called once at startup with decrypted credentials
    
    Args:
        account_sid: Twilio Account SID
        auth_token: Twilio Auth Token
        whatsapp_from: WhatsApp-enabled number
    """
    global _whatsapp_service
    _whatsapp_service = WhatsAppService(account_sid, auth_token, whatsapp_from)
    print(f"📱 WhatsApp service initialized with credentials")
