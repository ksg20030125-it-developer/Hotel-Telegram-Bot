"""
HTML Email Templates for Hotel Management Bot
Professional email templates with styling
"""

from datetime import datetime
from typing import Dict, Optional


def create_html_email(
    recipient_name: str,
    message_body: str,
    sender_name: str = "Hotel Manager",
    sender_email: str = "",
    sender_phone: str = "",
    hotel_name: str = "Grand Hotel",
    category: str = "notification",
    subject: str = ""
) -> str:
    """
    Create a beautifully formatted HTML email
    
    Args:
        recipient_name: Name of the recipient
        message_body: Main message content (can include HTML)
        sender_name: Name of the sender
        sender_email: Email address of sender
        sender_phone: Phone number of sender
        hotel_name: Name of the hotel
        category: Email category (notification, reminder, announcement, etc.)
        subject: Email subject line
        
    Returns:
        Complete HTML email string
    """
    
    # Category-based header styling
    category_colors = {
        'notification': '#2196F3',  # Blue
        'reminder': '#FF9800',      # Orange
        'announcement': '#4CAF50',   # Green
        'urgent': '#F44336',         # Red
        'info': '#00BCD4',           # Cyan
        'warning': '#FFC107'         # Amber
    }
    
    category_icons = {
        'notification': '📢',
        'reminder': '⏰',
        'announcement': '📣',
        'urgent': '🚨',
        'info': 'ℹ️',
        'warning': '⚠️'
    }
    
    header_color = category_colors.get(category.lower(), '#2196F3')
    category_icon = category_icons.get(category.lower(), '📧')
    
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <!-- Main Container -->
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {header_color} 0%, {header_color}dd 100%); padding: 30px 40px; text-align: center;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="text-align: center;">
                                        <div style="font-size: 36px; margin-bottom: 10px;">🏨</div>
                                        <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">{hotel_name}</h1>
                                        <p style="color: #ffffff; margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Hotel Management System</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <!-- Greeting -->
                            <p style="margin: 0 0 20px 0; font-size: 16px; color: #333333;">
                                Dear <strong>{recipient_name}</strong>,
                            </p>
                            
                            <!-- Message Content -->
                            <div style="margin: 20px 0; padding: 20px; background-color: #f9f9f9; border-left: 4px solid {header_color}; border-radius: 4px;">
                                {message_body}
                            </div>
                            
                            <!-- Closing -->
                            <p style="margin: 30px 0 10px 0; font-size: 16px; color: #333333;">
                                If you have any questions or need assistance, please do not hesitate to reach out.
                            </p>
                            
                            <p style="margin: 20px 0 0 0; font-size: 16px; color: #333333;">
                                Best regards,<br>
                                <strong>{sender_name}</strong><br>
                                <span style="color: #666666; font-size: 14px;">{hotel_name}</span>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Contact Info -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #fafafa; border-top: 1px solid #eeeeee;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="text-align: center; padding-bottom: 15px;">
                                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #666666; font-weight: 600;">Contact Information</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="text-align: center;">
                                        <table width="100%" cellpadding="5" cellspacing="0" border="0">
                                            {f'''<tr>
                                                <td style="text-align: center;">
                                                    <span style="font-size: 16px;">📧</span>
                                                    <span style="color: #666666; font-size: 14px; margin-left: 5px;">
                                                        Email: <a href="mailto:{sender_email}" style="color: {header_color}; text-decoration: none;">{sender_email}</a>
                                                    </span>
                                                </td>
                                            </tr>''' if sender_email else ''}
                                            {f'''<tr>
                                                <td style="text-align: center;">
                                                    <span style="font-size: 16px;">📞</span>
                                                    <span style="color: #666666; font-size: 14px; margin-left: 5px;">
                                                        Phone: <a href="tel:{sender_phone}" style="color: {header_color}; text-decoration: none;">{sender_phone}</a>
                                                    </span>
                                                </td>
                                            </tr>''' if sender_phone else ''}
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f5f5f5; text-align: center; border-top: 1px solid #eeeeee;">
                            <p style="margin: 0 0 5px 0; font-size: 12px; color: #999999;">
                                © {datetime.now().year} {hotel_name}. All rights reserved.
                            </p>
                            <p style="margin: 0; font-size: 11px; color: #bbbbbb;">
                                This is an automated message from the Hotel Management System.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    return html_template


def create_list_html(items: list, ordered: bool = False) -> str:
    """
    Create HTML list from items
    
    Args:
        items: List of items to display
        ordered: Whether to use ordered list (True) or unordered (False)
        
    Returns:
        HTML list string
    """
    list_type = 'ol' if ordered else 'ul'
    items_html = '\n'.join([f'<li style="margin: 8px 0; color: #333333;">{item}</li>' for item in items])
    
    return f"""
    <{list_type} style="margin: 15px 0; padding-left: 20px; color: #333333;">
        {items_html}
    </{list_type}>
    """


def format_message_body(text: str) -> str:
    """
    Format plain text message body to HTML with proper styling
    Converts line breaks and adds basic formatting
    
    Args:
        text: Plain text message
        
    Returns:
        HTML formatted text
    """
    # Convert line breaks to <br>
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('<br>')
        else:
            # Check if line looks like a heading
            if line.endswith(':') and len(line) < 50:
                formatted_lines.append(f'<p style="margin: 15px 0 10px 0; font-weight: 600; color: #333333; font-size: 15px;">{line}</p>')
            # Check if line starts with bullet point
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                content = line[1:].strip()
                formatted_lines.append(f'<p style="margin: 5px 0 5px 20px; color: #333333;">• {content}</p>')
            else:
                formatted_lines.append(f'<p style="margin: 10px 0; color: #333333; line-height: 1.6;">{line}</p>')
    
    return '\n'.join(formatted_lines)
