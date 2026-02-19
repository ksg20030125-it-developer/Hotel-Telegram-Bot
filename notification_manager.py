"""
Notification Manager for Hotel Management Bot
Handles email notifications and bulk messaging
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional, Any


class NotificationManager:
    """Manages email notifications and bulk messaging for hotel staff"""
    
    def __init__(self, db, application=None, email_user: str = None, email_password: str = None):
        """
        Initialize the NotificationManager
        
        Args:
            db: Database manager instance
            application: Telegram application instance (optional)
            email_user: Email address (optional, will use cache if not provided)
            email_password: Email password (optional, will use cache if not provided)
        """
        self.db = db
        self.application = application
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        
        # Use provided credentials or load from cache
        if email_user and email_password:
            self.email_user = email_user
            self.email_password = email_password
            self.email_from = email_user
            print(f"✅ Notification manager initialized with provided credentials")
        else:
            # Try to get from cache
            try:
                from email_ai_analyzer import _secrets_cache
                self.email_user = _secrets_cache.get('sender_email', '') or os.getenv('EMAIL_USER', '')
                self.email_password = _secrets_cache.get('app_password', '') or os.getenv('EMAIL_PASSWORD', '')
                self.email_from = self.email_user or os.getenv('EMAIL_FROM', '')
                if self.email_user and self.email_password:
                    print(f"✅ Notification manager initialized with cached credentials")
                else:
                    print(f"⚠️ Notification manager initialized without email credentials")
            except Exception as e:
                print(f"⚠️ Could not load email credentials: {e}")
                self.email_user = os.getenv('EMAIL_USER', '')
                self.email_password = os.getenv('EMAIL_PASSWORD', '')
                self.email_from = os.getenv('EMAIL_FROM', self.email_user)
    
    def get_departments_except_management(self) -> List[str]:
        """
        Get all departments except Management
        
        Returns:
            List of department names
        """
        try:
            self.db.cursor.execute("""
                SELECT DISTINCT department FROM tbl_employeer 
                WHERE department != 'Management' AND department IS NOT NULL
                ORDER BY department
            """)
            result = self.db.cursor.fetchall()
            return [row['department'] for row in result]
        except Exception as e:
            print(f"Error getting departments: {e}")
            return []
    
    def get_employees_by_department(self, department: str) -> List[Dict]:
        """
        Get employees in a specific department
        
        Args:
            department: Department name
            
        Returns:
            List of employee dictionaries
        """
        try:
            self.db.cursor.execute("""
                SELECT employee_id, name, gmail, telegram_user_id 
                FROM tbl_employeer 
                WHERE department = %s
                ORDER BY name
            """, (department,))
            result = self.db.cursor.fetchall()
            employees = []
            for row in result:
                emp_dict = dict(row)
                # Add has_email field based on whether gmail is set
                emp_dict['has_email'] = bool(emp_dict.get('gmail') and emp_dict['gmail'].strip())
                employees.append(emp_dict)
            return employees
        except Exception as e:
            print(f"Error getting employees: {e}")
            return []
    
    def format_mail_management_menu_text(self) -> str:
        """Format the mail management menu text"""
        return """📧 <b>Mail Management</b>

Select an option below to manage email notifications for hotel staff.

📤 <b>Send Reminder</b> - Send email registration reminder to employees
📋 <b>View Logs</b> - View recent email sending logs"""
    
    def format_department_selection_text(self) -> str:
        """Format the department selection text"""
        return """📧 <b>Send Email Reminder</b>

Please select a department to send email registration reminders:"""
    
    def format_employee_selection_text(self, department: str, employees: List[Dict], selected_ids: List[str]) -> str:
        """
        Format the employee selection text
        
        Args:
            department: Department name
            employees: List of employees
            selected_ids: List of selected employee IDs
            
        Returns:
            Formatted text string
        """
        text = f"""📧 <b>Send Email Reminder</b>

🏢 Department: <b>{department}</b>
👥 Total Employees: {len(employees)}
✅ Selected: {len(selected_ids)}

Select employees to send reminders:"""
        return text
    
    def format_email_confirmation_text(self, department: str, selected_count: int) -> str:
        """
        Format email confirmation text
        
        Args:
            department: Department name
            selected_count: Number of selected employees
            
        Returns:
            Formatted confirmation text
        """
        return f"""📧 <b>Confirm Email Send</b>

🏢 Department: <b>{department}</b>
📤 Recipients: {selected_count} employee(s)

Are you sure you want to send email registration reminders?"""
    
    def format_email_result_text(self, result: Dict) -> str:
        """
        Format email sending result text
        
        Args:
            result: Dictionary with success and failed counts
            
        Returns:
            Formatted result text
        """
        success = result.get('success', 0)
        failed = result.get('failed', 0)
        total = success + failed
        
        status_emoji = "✅" if failed == 0 else "⚠️"
        
        return f"""{status_emoji} <b>Email Sending Complete</b>

📊 Results:
✅ Successful: {success}
❌ Failed: {failed}
📧 Total: {total}"""
    
    def format_email_logs_text(self, logs: List[Dict]) -> str:
        """
        Format email logs text with enhanced details
        
        Args:
            logs: List of email log entries
            
        Returns:
            Formatted logs text
        """
        if not logs:
            return "📋 <b>Email Logs</b>\n\nNo email logs found."
        
        text = "📋 <b>Email Logs</b>\n\n"
        text += f"Recent {len(logs)} email(s):\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for log in logs[:20]:  # Limit to 20 entries
            timestamp = log.get('sent_at', 'N/A')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(timestamp, str):
                timestamp = timestamp[:19]
            
            recipient = log.get('recipient', 'Unknown')
            recipient_name = log.get('recipient_name', '')
            subject = log.get('subject', 'No subject')
            status = log.get('status', 'unknown')
            
            # Status display
            if status == 'sent':
                status_icon = "✅"
                status_text = "Sent"
            elif status == 'failed':
                status_icon = "❌"
                status_text = "Failed"
            else:
                status_icon = "⏳"
                status_text = "Pending"
            
            # Format recipient
            if recipient_name:
                recipient_display = f"{recipient_name} ({recipient})"
            else:
                recipient_display = recipient
            
            # Truncate subject if too long
            if len(subject) > 50:
                subject = subject[:47] + "..."
            
            text += f"{status_icon} <b>{status_text}</b>\n"
            text += f"📧 {recipient_display}\n"
            text += f"📝 {subject}\n"
            text += f"⏰ {timestamp}\n"
            
            # Show error for failed sends only
            if status == 'failed' and log.get('error_message'):
                error_msg = log.get('error_message', '')
                if len(error_msg) > 60:
                    error_msg = error_msg[:57] + "..."
                text += f"⚠️ Error: {error_msg}\n"
            
            text += "\n"
        
        return text
    
    async def send_email_registration_reminder(self, emp_id: str, emp_name: str) -> bool:
        """
        Send email registration reminder to a specific employee via Telegram
        
        Args:
            emp_id: Employee ID
            emp_name: Employee name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get employee's Telegram ID
            self.db.cursor.execute("""
                SELECT telegram_user_id FROM tbl_employeer WHERE id = %s
            """, (emp_id,))
            result = self.db.cursor.fetchone()
            
            if not result or not result['telegram_user_id']:
                print(f"No Telegram ID found for employee {emp_id}")
                return False
            
            telegram_id = result['telegram_user_id']
            
            # Send Telegram message
            message = f"""📧 <b>Email Registration Reminder</b>

Hello {emp_name}!

Please register your email address to receive important notifications.

Go to Settings → Register Email to add your email address."""
            
            if self.application:
                await self.application.bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                    parse_mode="HTML"
                )
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending reminder to {emp_id}: {e}")
            return False
    
    def send_bulk_email(self, recipients, subject: str, body: str) -> Dict:
        """
        Send bulk email to multiple recipients
        
        Args:
            recipients: List of employee IDs (integers) or list of recipient dictionaries with 'email' and 'name' keys
            subject: Email subject
            body: Email body
            
        Returns:
            Dictionary with success and failed counts
        """
        result = {'success': 0, 'failed': 0, 'errors': []}
        
        print(f"📧 send_bulk_email called")
        print(f"   Recipients type: {type(recipients)}")
        print(f"   Recipients: {recipients}")
        print(f"   Email user: {self.email_user[:20] if self.email_user else 'None'}...")
        print(f"   Email password: {'✓' if self.email_password else '✗'}")
        
        if not self.email_user or not self.email_password:
            print("❌ Email credentials not configured")
            result['failed'] = len(recipients) if isinstance(recipients, list) else 1
            result['errors'].append("Email credentials not configured")
            return result
        
        # Convert employee IDs to recipient dictionaries if needed
        if recipients and isinstance(recipients[0], (int, str)) and not isinstance(recipients[0], dict):
            print(f"🔄 Converting employee IDs to recipient list...")
            from database import DatabaseManager
            db = DatabaseManager()
            db.connect()
            
            recipient_list = []
            for emp_id in recipients:
                try:
                    emp_info = db.get_employee_by_id(emp_id)
                    if emp_info:
                        full_info = db.get_employee_info(emp_info['telegram_user_id'])
                        if full_info and full_info.get('gmail'):
                            recipient_list.append({
                                'email': full_info['gmail'],
                                'name': full_info['name']
                            })
                            print(f"   ✓ Added {full_info['name']} ({full_info['gmail']})")
                except Exception as e:
                    print(f"   ❌ Failed to get info for employee {emp_id}: {e}")
            
            db.disconnect()
            recipients = recipient_list
            print(f"✅ Converted to {len(recipients)} recipients")
        
        if not recipients:
            print("❌ No valid recipients found")
            result['failed'] = 1
            result['errors'].append("No valid recipients found")
            return result
        
        try:
            print(f"🔌 Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            # Connect to SMTP server with timeout
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            print(f"🔐 Starting TLS...")
            server.starttls()
            print(f"🔑 Logging in as {self.email_user}...")
            server.login(self.email_user, self.email_password)
            print(f"✅ SMTP connection established")
            
            for i, recipient in enumerate(recipients, 1):
                email = None  # Initialize email variable
                try:
                    email = recipient.get('email') or recipient.get('gmail')
                    name = recipient.get('name', 'Employee')
                    
                    print(f"📤 Sending {i}/{len(recipients)} to {email}...")
                    
                    if not email:
                        print(f"   ⚠️ No email address")
                        result['failed'] += 1
                        continue
                    
                    # Create message
                    msg = MIMEMultipart()
                    msg['From'] = self.email_from
                    msg['To'] = email
                    msg['Subject'] = subject
                    
                    # Import HTML template
                    from email_templates import create_html_email, format_message_body
                    
                    # Format message body
                    formatted_body = format_message_body(body)
                    
                    # Create beautiful HTML email
                    html_email = create_html_email(
                        recipient_name=name,
                        message_body=formatted_body,
                        sender_name="Hotel Manager",
                        sender_email=self.email_user,
                        sender_phone="",
                        hotel_name="Grand Hotel",
                        category="notification",
                        subject=subject
                    )
                    
                    msg.attach(MIMEText(html_email, 'html'))
                    
                    # Calculate email size
                    email_size = len(msg.as_string())
                    
                    # Send email
                    smtp_response = server.send_message(msg)
                    result['success'] += 1
                    print(f"   ✅ Sent successfully")
                    
                    # Log the email with SMTP details
                    self._log_email(
                        email, 
                        subject, 
                        True,
                        smtp_code=250,
                        smtp_message="Message accepted for delivery",
                        recipient_name=name,
                        email_size=email_size
                    )
                    
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    result['failed'] += 1
                    error_email = email if email else recipient.get('name', 'Unknown')
                    result['errors'].append(f"{error_email}: {str(e)}")
                    if email:
                        smtp_code = getattr(e, 'smtp_code', None)
                        smtp_msg = getattr(e, 'smtp_error', str(e))
                        self._log_email(
                            email, 
                            subject, 
                            False, 
                            error=str(e),
                            smtp_code=smtp_code,
                            smtp_message=smtp_msg,
                            recipient_name=name
                        )
            
            print(f"🔌 Closing SMTP connection")
            server.quit()
            print(f"✅ All emails processed")
            
        except Exception as e:
            print(f"❌ SMTP connection error: {e}")
            import traceback
            traceback.print_exc()
            result['failed'] = len(recipients) - result['success']
            result['errors'].append(f"SMTP error: {str(e)}")
            
            # Log failed emails for all recipients
            for recipient in recipients:
                email = recipient.get('email') or recipient.get('gmail')
                name = recipient.get('name', 'Employee')
                if email:
                    self._log_email(
                        email,
                        subject,
                        False,
                        error=f"SMTP connection error: {str(e)}",
                        smtp_code=None,
                        smtp_message=str(e),
                        recipient_name=name
                    )
                    print(f"   📝 Logged failed email to {email}")
        
        return result
    
    def _log_email(self, recipient: str, subject: str, success: bool, error: str = None,
                   smtp_code: int = None, smtp_message: str = None, recipient_name: str = None,
                   sent_by_user_id: int = None, email_size: int = 0):
        """
        Log email sending attempt with enhanced details
        
        Args:
            recipient: Email recipient
            subject: Email subject
            success: Whether the send was successful
            error: Error message if failed
            smtp_code: SMTP response code
            smtp_message: SMTP response message
            recipient_name: Name of recipient
            sent_by_user_id: Telegram user ID of sender
            email_size: Size of email in bytes
        """
        try:
            status = 'sent' if success else 'failed'
            self.db.cursor.execute("""
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
                smtp_code,
                smtp_message,
                error,
                self.email_user,
                'Hotel Management Bot',
                sent_by_user_id,
                email_size
            ))
            self.db.connection.commit()
            print(f"   📝 Email attempt logged to database")
        except Exception as e:
            print(f"Error logging email: {e}")
            import traceback
            traceback.print_exc()
    
    def get_email_logs(self, limit: int = 20) -> List[Dict]:
        """
        Get recent email logs with enhanced details
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of email log entries
        """
        try:
            # Check if table exists first
            self.db.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'tbl_email_logs'
                )
            """)
            exists = self.db.cursor.fetchone()[0]
            
            if not exists:
                return []
            
            self.db.cursor.execute("""
                SELECT id, recipient, recipient_name, subject, status, 
                       smtp_response_code, smtp_response_message, error_message, 
                       sender_email, sent_at, email_size_bytes
                FROM tbl_email_logs
                ORDER BY sent_at DESC
                LIMIT %s
            """, (limit,))
            
            result = self.db.cursor.fetchall()
            
            # Convert to list of dicts
            logs = []
            for row in result:
                log_dict = dict(row)
                logs.append(log_dict)
            
            return logs
            
        except Exception as e:
            print(f"Error getting email logs: {e}")
            return []
    
    async def send_email_notification_to_admin(self, admin_user_id: int, 
                                               success_count: int, 
                                               failed_count: int,
                                               details: List[Dict] = None):
        """
        Send real-time notification to admin about email sending results
        
        Args:
            admin_user_id: Telegram user ID of admin
            success_count: Number of successful sends
            failed_count: Number of failed sends
            details: Detailed results list
        """
        if not self.application:
            print("⚠️ Application not available for sending notifications")
            return
        
        try:
            # Create notification message
            status_emoji = "✅" if failed_count == 0 else "⚠️" if success_count > 0 else "❌"
            total = success_count + failed_count
            
            message = f"""{status_emoji} <b>Email Sending Complete</b>

📊 <b>Results:</b>
   ✅ Success: {success_count}
   ❌ Failed: {failed_count}
   📧 Total: {total} processed

⏰ <b>Sent at:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            # Add details if available and not too many
            if details and len(details) <= 5:
                message += "\n\n📋 <b>Details:</b>"
                for detail in details:
                    email = detail.get('email', 'Unknown')
                    name = detail.get('name', '')
                    status = detail.get('status', 'unknown')
                    
                    if status == 'sent':
                        smtp_code = detail.get('smtp_code', 250)
                        message += f"\n   ✅ {name} ({email[:20]}...) - Code: {smtp_code}"
                    else:
                        error = detail.get('error', 'Unknown error')[:50]
                        message += f"\n   ❌ {name} ({email[:20]}...) - {error}"
            elif details and len(details) > 5:
                message += f"\n\n💡 Too many details. Check /email_logs for full list."
            
            message += "\n\n📝 Logs saved to database."
            
            # Send notification
            await self.application.bot.send_message(
                chat_id=admin_user_id,
                text=message,
                parse_mode='HTML'
            )
            
            print(f"✅ Email notification sent to admin {admin_user_id}")
            
        except Exception as e:
            print(f"❌ Failed to send notification to admin: {e}")
            import traceback
            traceback.print_exc()


# Global instance
_notification_manager = None


def get_notification_manager(db, application=None, email_user: str = None, email_password: str = None) -> NotificationManager:
    """
    Get or create the NotificationManager singleton
    
    Args:
        db: Database manager instance
        application: Telegram application instance
        email_user: Email address (optional, for initialization)
        email_password: Email password (optional, for initialization)
        
    Returns:
        NotificationManager instance
    """
    global _notification_manager
    
    if _notification_manager is None:
        _notification_manager = NotificationManager(db, application, email_user, email_password)
    
    return _notification_manager
