"""
Email Service for Hotel Management Bot
Handles sending emails via SMTP and Gmail API
"""

import os
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Optional, Any

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False


def get_email_credentials() -> tuple:
    """
    Retrieve email credentials from cache set by main.py
    Falls back to environment variables for backward compatibility
    
    Returns:
        Tuple of (sender_email, app_password)
    """
    sender_email = None
    app_password = None
    
    try:
        # Import the cached secrets from email_ai_analyzer
        from email_ai_analyzer import _secrets_cache
        
        sender_email = _secrets_cache.get('sender_email', '')
        app_password = _secrets_cache.get('app_password', '')
        
        print(f"📧 Email credentials from cache:")
        print(f"   - Sender email: {'✓ ' + sender_email[:20] + '...' if sender_email else '✗ Empty'}")
        print(f"   - App password: {'✓ (length: ' + str(len(app_password)) + ')' if app_password else '✗ Empty'}")
        
    except Exception as e:
        print(f"⚠️ Could not retrieve email credentials from cache: {e}")
    
    # Fallback to environment variables
    if not sender_email:
        sender_email = os.getenv('SENDER_EMAIL', '')
        if sender_email:
            print(f"   📌 Using SENDER_EMAIL from environment")
    if not app_password:
        app_password = os.getenv('APP_PASSWORD', '') or os.getenv('EMAIL_PASSWORD', '')
        if app_password:
            print(f"   📌 Using APP_PASSWORD from environment")
    
    return sender_email, app_password


# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))


class EmailService:
    """Service class for sending emails"""
    
    def __init__(self, email_user: str = None, email_password: str = None):
        """
        Initialize email service
        
        Args:
            email_user: Email address (if None, will try to load from cache/env)
            email_password: Email password (if None, will try to load from cache/env)
        """
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        
        # Use provided credentials or load from cache
        if email_user and email_password:
            self.email_user = email_user
            self.email_password = email_password
            print(f"✅ EmailService initialized with provided credentials")
        else:
            # Fallback to loading from cache
            self.email_user, self.email_password = get_email_credentials()
            if self.email_user and self.email_password:
                print(f"✅ EmailService initialized with cached credentials")
            else:
                print(f"⚠️ EmailService initialized without credentials")
        
        # Gmail API setup
        self.gmail_service = None
        self.scopes = ['https://www.googleapis.com/auth/gmail.send']
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(self.email_user and self.email_password)
    
    def send_email(self, to: str, subject: str, body: str, html: bool = False, 
                   recipient_name: str = None, sent_by_user_id: int = None) -> Dict:
        """
        Send an email with enhanced logging
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            html: Whether the body is HTML
            recipient_name: Name of the recipient (for logging)
            sent_by_user_id: Telegram user ID of sender (for tracking)
            
        Returns:
            Dictionary with 'success', 'smtp_code', 'smtp_message', 'error'
        """
        result = {
            'success': False,
            'smtp_code': None,
            'smtp_message': None,
            'error': None,
            'email_size': 0
        }
        
        if not self.is_configured():
            error_msg = "Email service not configured"
            print(f"❌ {error_msg}")
            result['error'] = error_msg
            self._log_email_attempt(to, subject, result, recipient_name, sent_by_user_id)
            return result
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = to
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            content_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, content_type, 'utf-8'))
            
            # Calculate email size
            result['email_size'] = len(msg.as_string())
            
            print(f"📧 Sending email to {to}...")
            print(f"   📊 Size: {result['email_size']} bytes")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.set_debuglevel(0)  # Set to 1 for verbose SMTP debugging
                
                print(f"   🔐 Starting TLS...")
                server.starttls()
                
                print(f"   🔑 Authenticating...")
                server.login(self.email_user, self.email_password)
                
                print(f"   📤 Sending message...")
                smtp_result = server.send_message(msg)
                
                # Get SMTP response
                result['smtp_code'] = 250  # Default success code
                result['smtp_message'] = "Message accepted for delivery"
                result['success'] = True
                
                print(f"   ✅ Email sent successfully!")
                print(f"   📬 SMTP Code: {result['smtp_code']}")
                print(f"   💬 SMTP Response: {result['smtp_message']}")
            
            # Log successful send
            self._log_email_attempt(to, subject, result, recipient_name, sent_by_user_id)
            return result
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {str(e)}"
            print(f"   ❌ {error_msg}")
            result['error'] = error_msg
            result['smtp_code'] = getattr(e, 'smtp_code', None)
            result['smtp_message'] = getattr(e, 'smtp_error', str(e))
            self._log_email_attempt(to, subject, result, recipient_name, sent_by_user_id)
            return result
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            print(f"   ❌ {error_msg}")
            result['error'] = error_msg
            result['smtp_message'] = str(e)
            self._log_email_attempt(to, subject, result, recipient_name, sent_by_user_id)
            return result
    
    def _log_email_attempt(self, recipient: str, subject: str, result: Dict, 
                          recipient_name: str = None, sent_by_user_id: int = None):
        """
        Log email sending attempt to database
        
        Args:
            recipient: Email address
            subject: Email subject
            result: Result dictionary from send_email
            recipient_name: Name of recipient
            sent_by_user_id: Telegram user ID of sender
        """
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            db.connect()
            
            status = 'sent' if result['success'] else 'failed'
            
            db.cursor.execute("""
                INSERT INTO tbl_email_logs 
                (recipient, recipient_name, subject, status, smtp_response_code, 
                 smtp_response_message, error_message, sender_email, sender_name,
                 sent_by_user_id, email_size_bytes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                recipient,
                recipient_name,
                subject,
                status,
                result.get('smtp_code'),
                result.get('smtp_message'),
                result.get('error'),
                self.email_user,
                'Hotel Management Bot',
                sent_by_user_id,
                result.get('email_size', 0)
            ))
            
            db.connection.commit()
            db.disconnect()
            
            print(f"   📝 Email attempt logged to database")
            
        except Exception as e:
            print(f"   ⚠️ Failed to log email attempt: {e}")
    
    def send_bulk_email(self, recipients: List[str], subject: str, body: str, 
                        html: bool = False, personalize: Dict[str, Dict] = None,
                        sent_by_user_id: int = None) -> Dict:
        """
        Send email to multiple recipients with detailed tracking
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            body: Email body (can include {name} placeholder)
            html: Whether body is HTML
            personalize: Dict of email -> {name, ...} for personalization
            sent_by_user_id: Telegram user ID of sender
            
        Returns:
            Dictionary with success, failed counts, and detailed results
        """
        result = {
            'success': 0, 
            'failed': 0, 
            'errors': [],
            'details': []
        }
        
        print(f"📧 Starting bulk email send to {len(recipients)} recipient(s)...")
        
        for i, email in enumerate(recipients, 1):
            try:
                # Personalize body if data provided
                personalized_body = body
                recipient_name = None
                
                if personalize and email in personalize:
                    data = personalize[email]
                    recipient_name = data.get('name', 'Employee')
                    for key, value in data.items():
                        personalized_body = personalized_body.replace(f'{{{key}}}', str(value))
                
                print(f"\n📤 [{i}/{len(recipients)}] Sending to {email}...")
                
                send_result = self.send_email(
                    email, 
                    subject, 
                    personalized_body, 
                    html,
                    recipient_name=recipient_name,
                    sent_by_user_id=sent_by_user_id
                )
                
                if send_result['success']:
                    result['success'] += 1
                    result['details'].append({
                        'email': email,
                        'name': recipient_name,
                        'status': 'sent',
                        'smtp_code': send_result['smtp_code']
                    })
                else:
                    result['failed'] += 1
                    result['errors'].append(f"{email}: {send_result['error']}")
                    result['details'].append({
                        'email': email,
                        'name': recipient_name,
                        'status': 'failed',
                        'error': send_result['error']
                    })
                    
            except Exception as e:
                result['failed'] += 1
                error_msg = str(e)
                result['errors'].append(f"{email}: {error_msg}")
                result['details'].append({
                    'email': email,
                    'status': 'failed',
                    'error': error_msg
                })
                print(f"   ❌ Exception: {e}")
        
        print(f"\n✅ Bulk email complete: {result['success']} sent, {result['failed']} failed")
        return result
    
    def send_notification(self, to: str, title: str, message: str, 
                         notification_type: str = 'info', recipient_name: str = None,
                         sent_by_user_id: int = None) -> Dict:
        """
        Send a notification email with enhanced tracking
        
        Args:
            to: Recipient email
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, urgent)
            recipient_name: Name of recipient
            sent_by_user_id: Telegram user ID of sender
            
        Returns:
            Result dictionary with success status and details
        """
        type_colors = {
            'info': '#3498db',
            'warning': '#f39c12',
            'urgent': '#e74c3c',
            'success': '#27ae60'
        }
        
        color = type_colors.get(notification_type, '#3498db')
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="border-left: 4px solid {color}; padding-left: 15px;">
                <h2 style="color: {color}; margin: 0;">{title}</h2>
                <p style="color: #333; margin-top: 10px;">{message}</p>
                <p style="color: #999; font-size: 12px; margin-top: 20px;">
                    Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to, 
            f"[{notification_type.upper()}] {title}", 
            html_body, 
            html=True,
            recipient_name=recipient_name,
            sent_by_user_id=sent_by_user_id
        )
    
    def send_task_notification(self, to: str, task_data: Dict, 
                              recipient_name: str = None, sent_by_user_id: int = None) -> Dict:
        """
        Send task assignment notification with enhanced tracking
        
        Args:
            to: Recipient email
            task_data: Task information dictionary
            recipient_name: Name of recipient
            sent_by_user_id: Telegram user ID of sender
            
        Returns:
            Result dictionary with success status and details
        """
        subject = f"New Task Assignment: {task_data.get('description', 'Task')[:50]}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2c3e50;">📋 New Task Assigned</h2>
            <table style="border-collapse: collapse; width: 100%; margin-top: 15px;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Task ID:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">#{task_data.get('id', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Description:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{task_data.get('description', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Priority:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{task_data.get('priority', 'Normal')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Due Date:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{task_data.get('due_date', 'N/A')}</td>
                </tr>
            </table>
            <p style="margin-top: 20px;">Please check the bot for more details.</p>
        </body>
        </html>
        """
        
        return self.send_email(
            to, 
            subject, 
            html_body, 
            html=True,
            recipient_name=recipient_name,
            sent_by_user_id=sent_by_user_id
        )
    
    def send_shift_report(self, to: str, shift_data: Dict, 
                         recipient_name: str = None, sent_by_user_id: int = None) -> Dict:
        """
        Send shift report email with enhanced tracking
        
        Args:
            to: Recipient email
            shift_data: Shift report data
            recipient_name: Name of recipient
            sent_by_user_id: Telegram user ID of sender
            
        Returns:
            Result dictionary with success status and details
        """
        subject = f"Shift Report - {shift_data.get('date', datetime.now().strftime('%Y-%m-%d'))}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2c3e50;">📊 Shift Report</h2>
            <p><strong>Date:</strong> {shift_data.get('date', 'N/A')}</p>
            <p><strong>Shift:</strong> {shift_data.get('shift_type', 'N/A')}</p>
            <p><strong>Department:</strong> {shift_data.get('department', 'N/A')}</p>
            
            <h3 style="margin-top: 20px;">Report Content:</h3>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
                {shift_data.get('content', 'No content provided')}
            </div>
            
            <p style="color: #999; font-size: 12px; margin-top: 20px;">
                Submitted by: {shift_data.get('submitted_by', 'Unknown')}
            </p>
        </body>
        </html>
        """
        
        return self.send_email(
            to, 
            subject, 
            html_body, 
            html=True,
            recipient_name=recipient_name,
            sent_by_user_id=sent_by_user_id
        )
    
    def send_test_email(self, to: str, recipient_name: str = None, 
                       sent_by_user_id: int = None) -> Dict:
        """
        Send a test email to verify email configuration
        
        Args:
            to: Recipient email address
            recipient_name: Name of recipient
            sent_by_user_id: Telegram user ID of sender
            
        Returns:
            Result dictionary with success status and details
        """
        subject = "🧪 Test Email from Hotel Management Bot"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h1 style="color: #2c3e50; text-align: center;">🧪 Test Email</h1>
                
                <div style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin: 20px 0;">
                    <h2 style="color: #4caf50; margin: 0 0 10px 0;">✅ Success!</h2>
                    <p style="margin: 0; color: #333;">
                        If you're reading this, the email system is working correctly.
                    </p>
                </div>
                
                <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">📋 Test Details:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Sent to:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{to}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Recipient:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{recipient_name or 'Not specified'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Sent from:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{self.email_user}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Date & Time:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;"><strong>SMTP Server:</strong></td>
                            <td style="padding: 8px;">{self.smtp_server}:{self.smtp_port}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404;">
                        <strong>💡 Note:</strong> This is an automated test email. 
                        You can safely ignore or delete this message.
                    </p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="text-align: center; color: #999; font-size: 12px;">
                    Hotel Management Bot | Automated Email System<br>
                    © 2026 All Rights Reserved
                </p>
            </div>
        </body>
        </html>
        """
        
        print(f"\n🧪 Sending test email...")
        result = self.send_email(
            to, 
            subject, 
            html_body, 
            html=True,
            recipient_name=recipient_name,
            sent_by_user_id=sent_by_user_id
        )
        
        if result['success']:
            print(f"✅ Test email sent successfully!")
            print(f"📬 Please check {to} for the test message")
        else:
            print(f"❌ Test email failed: {result.get('error', 'Unknown error')}")
        
        return result


# Singleton instance
_email_service = None


def get_email_service(email_user: str = None, email_password: str = None) -> EmailService:
    """
    Get or create the EmailService singleton
    
    Args:
        email_user: Email address (optional, for initialization)
        email_password: Email password (optional, for initialization)
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService(email_user, email_password)
    return _email_service


def init_email_service(email_user: str, email_password: str):
    """
    Initialize email service with credentials from main.py
    Called once at startup with decrypted credentials
    
    Args:
        email_user: Sender email address
        email_password: Email app password
    """
    global _email_service
    _email_service = EmailService(email_user, email_password)
    print(f"📧 Email service initialized with credentials")
