"""
Message Sender for Hotel Management Bot
Handles sending messages via various channels (Telegram, Email, WhatsApp)
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any, Union

# Import email service
try:
    from email_service import get_email_service
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False


class MessageSender:
    """Unified message sender for multiple channels"""
    
    def __init__(self, bot=None, db=None):
        """
        Initialize the message sender
        
        Args:
            bot: Telegram bot instance
            db: Database manager instance
        """
        self.bot = bot
        self.db = db
        self.email_service = get_email_service() if EMAIL_AVAILABLE else None
    
    async def send_telegram_message(self, chat_id: int, text: str, 
                                    parse_mode: str = "HTML",
                                    reply_markup=None) -> bool:
        """
        Send a Telegram message
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Parse mode (HTML, Markdown, etc.)
            reply_markup: Optional keyboard markup
            
        Returns:
            True if successful
        """
        if not self.bot:
            print("❌ Bot instance not available")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            print(f"❌ Failed to send Telegram message to {chat_id}: {e}")
            return False
    
    async def send_telegram_photo(self, chat_id: int, photo: str,
                                  caption: str = None,
                                  parse_mode: str = "HTML") -> bool:
        """
        Send a photo via Telegram
        
        Args:
            chat_id: Telegram chat ID
            photo: Photo file_id or URL
            caption: Photo caption
            parse_mode: Parse mode for caption
            
        Returns:
            True if successful
        """
        if not self.bot:
            return False
        
        try:
            await self.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            print(f"❌ Failed to send photo to {chat_id}: {e}")
            return False
    
    def send_email(self, to: str, subject: str, body: str, html: bool = True) -> bool:
        """
        Send an email
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            html: Whether body is HTML
            
        Returns:
            True if successful
        """
        if not self.email_service:
            print("❌ Email service not available")
            return False
        
        return self.email_service.send_email(to, subject, body, html)
    
    async def send_to_employee(self, employee_id: str, message: str,
                               channels: List[str] = None,
                               subject: str = "Hotel Notification") -> Dict:
        """
        Send message to an employee via multiple channels
        
        Args:
            employee_id: Employee ID
            message: Message content
            channels: List of channels to use ('telegram', 'email', 'whatsapp')
            subject: Email subject if sending email
            
        Returns:
            Dictionary with results for each channel
        """
        if channels is None:
            channels = ['telegram']
        
        results = {}
        
        # Get employee info from database
        if not self.db:
            return {'error': 'Database not available'}
        
        try:
            self.db.cursor.execute("""
                SELECT telegram_user_id, gmail, whatsapp, name
                FROM tbl_employeer WHERE id = %s
            """, (employee_id,))
            employee = self.db.cursor.fetchone()
            
            if not employee:
                return {'error': 'Employee not found'}
            
            # Send via Telegram
            if 'telegram' in channels and employee['telegram_user_id']:
                results['telegram'] = await self.send_telegram_message(
                    employee['telegram_user_id'],
                    message
                )
            
            # Send via Email
            if 'email' in channels and employee['gmail']:
                results['email'] = self.send_email(
                    employee['gmail'],
                    subject,
                    message,
                    html=True
                )
            
            # WhatsApp would go here if implemented
            if 'whatsapp' in channels:
                results['whatsapp'] = False  # Not implemented
            
            return results
            
        except Exception as e:
            print(f"❌ Error sending to employee {employee_id}: {e}")
            return {'error': str(e)}
    
    async def send_to_department(self, department: str, message: str,
                                 channels: List[str] = None,
                                 subject: str = "Department Notification") -> Dict:
        """
        Send message to all employees in a department
        
        Args:
            department: Department name
            message: Message content
            channels: Channels to use
            subject: Email subject
            
        Returns:
            Dictionary with results summary
        """
        if channels is None:
            channels = ['telegram']
        
        if not self.db:
            return {'error': 'Database not available'}
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        try:
            self.db.cursor.execute("""
                SELECT id, telegram_user_id, gmail, name
                FROM tbl_employeer WHERE department = %s
            """, (department,))
            employees = self.db.cursor.fetchall()
            
            results['total'] = len(employees)
            
            for emp in employees:
                emp_result = await self.send_to_employee(
                    emp['id'],
                    message.replace('{name}', emp['name']),
                    channels,
                    subject
                )
                
                if 'error' not in emp_result and any(emp_result.values()):
                    results['success'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append({
                    'employee_id': emp['id'],
                    'name': emp['name'],
                    'result': emp_result
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Error sending to department {department}: {e}")
            return {'error': str(e)}
    
    async def broadcast(self, message: str, 
                        exclude_management: bool = False,
                        channels: List[str] = None,
                        subject: str = "Hotel Broadcast") -> Dict:
        """
        Broadcast message to all employees
        
        Args:
            message: Message content
            exclude_management: Whether to exclude Management department
            channels: Channels to use
            subject: Email subject
            
        Returns:
            Dictionary with results summary
        """
        if channels is None:
            channels = ['telegram']
        
        if not self.db:
            return {'error': 'Database not available'}
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'by_department': {}
        }
        
        try:
            query = "SELECT DISTINCT department FROM tbl_employeer WHERE department IS NOT NULL"
            if exclude_management:
                query += " AND department != 'Management'"
            
            self.db.cursor.execute(query)
            departments = [row['department'] for row in self.db.cursor.fetchall()]
            
            for dept in departments:
                dept_result = await self.send_to_department(dept, message, channels, subject)
                results['by_department'][dept] = dept_result
                results['total'] += dept_result.get('total', 0)
                results['success'] += dept_result.get('success', 0)
                results['failed'] += dept_result.get('failed', 0)
            
            return results
            
        except Exception as e:
            print(f"❌ Broadcast error: {e}")
            return {'error': str(e)}
    
    async def send_task_notification(self, task_id: int, 
                                     notification_type: str = 'assigned') -> bool:
        """
        Send task-related notification
        
        Args:
            task_id: Task ID
            notification_type: Type of notification (assigned, reminder, completed)
            
        Returns:
            True if successful
        """
        if not self.db:
            return False
        
        try:
            # Get task info
            task = self.db.get_task_by_id(task_id)
            if not task:
                return False
            
            # Build notification message based on type
            if notification_type == 'assigned':
                message = f"""📋 <b>New Task Assigned</b>

Task #{task_id}
Description: {task[5] if len(task) > 5 else 'N/A'}
Priority: {task[6] if len(task) > 6 else 'Normal'}
Due: {task[7] if len(task) > 7 else 'N/A'}

Please check the bot for details."""

            elif notification_type == 'reminder':
                message = f"""⏰ <b>Task Reminder</b>

Task #{task_id} is due soon!
Description: {task[5] if len(task) > 5 else 'N/A'}

Please complete this task as soon as possible."""

            elif notification_type == 'completed':
                message = f"""✅ <b>Task Completed</b>

Task #{task_id} has been marked as completed."""

            else:
                message = f"Task #{task_id} notification"
            
            # Get assignee's Telegram ID
            assignee_id = task[3] if len(task) > 3 else None
            if assignee_id and self.bot:
                self.db.cursor.execute("""
                    SELECT telegram_user_id FROM tbl_employeer WHERE id = %s
                """, (assignee_id,))
                result = self.db.cursor.fetchone()
                
                if result and result['telegram_user_id']:
                    return await self.send_telegram_message(
                        result['telegram_user_id'],
                        message
                    )
            
            return False
            
        except Exception as e:
            print(f"❌ Task notification error: {e}")
            return False


# Factory function
def create_message_sender(bot=None, db=None) -> MessageSender:
    """Create a new MessageSender instance"""
    return MessageSender(bot=bot, db=db)
