"""
WhatsApp Message Templates for Hotel Management Bot
Professional WhatsApp message formatting
"""

from datetime import datetime


def create_whatsapp_message(
    recipient_name: str,
    message_body: str,
    sender_name: str = "Hotel Manager",
    sender_phone: str = "",
    hotel_name: str = "Grand Hotel",
    category: str = "notification"
) -> str:
    """
    Create a beautifully formatted WhatsApp message
    
    Args:
        recipient_name: Name of the recipient
        message_body: Main message content
        sender_name: Name of the sender
        sender_phone: Phone number of sender
        hotel_name: Name of the hotel
        category: Message category (notification, reminder, announcement, etc.)
        
    Returns:
        Formatted WhatsApp message string
    """
    
    # Category-based icons
    category_icons = {
        'notification': '📢',
        'reminder': '⏰',
        'announcement': '📣',
        'urgent': '🚨',
        'info': 'ℹ️',
        'warning': '⚠️',
        'task': '📋',
        'schedule': '📅'
    }
    
    icon = category_icons.get(category.lower(), '📧')
    
    # Build message with WhatsApp formatting
    message = f"""🏨 *{hotel_name}*
{icon} _{category.upper()}_
━━━━━━━━━━━━━━━━━━━━━━━━

Dear *{recipient_name}*,

{message_body}

━━━━━━━━━━━━━━━━━━━━━━━━
📝 If you have any questions, please contact us.

Best regards,
*{sender_name}*
_{hotel_name}_"""

    if sender_phone:
        message += f"\n📞 {sender_phone}"
    
    message += f"\n\n_Sent: {datetime.now().strftime('%Y-%m-%d %H:%M')}_"
    
    return message


def format_whatsapp_list(items: list, title: str = "") -> str:
    """
    Format a list for WhatsApp
    
    Args:
        items: List of items
        title: Optional title for the list
        
    Returns:
        Formatted list string
    """
    result = ""
    if title:
        result += f"*{title}*\n\n"
    
    for i, item in enumerate(items, 1):
        result += f"  {i}. {item}\n"
    
    return result


def format_whatsapp_bullet_list(items: list, title: str = "") -> str:
    """
    Format a bullet list for WhatsApp
    
    Args:
        items: List of items
        title: Optional title for the list
        
    Returns:
        Formatted bullet list string
    """
    result = ""
    if title:
        result += f"*{title}*\n\n"
    
    for item in items:
        result += f"  • {item}\n"
    
    return result


def format_whatsapp_table(data: list, headers: list = None) -> str:
    """
    Format a simple table for WhatsApp
    
    Args:
        data: List of rows (each row is a list)
        headers: Optional list of header names
        
    Returns:
        Formatted table string
    """
    result = ""
    
    if headers:
        result += "```\n"
        result += " | ".join(headers) + "\n"
        result += "─" * (len(" | ".join(headers))) + "\n"
    
    for row in data:
        result += " | ".join(str(cell) for cell in row) + "\n"
    
    if headers:
        result += "```"
    
    return result


def add_whatsapp_emphasis(text: str, style: str = "bold") -> str:
    """
    Add WhatsApp text emphasis
    
    Args:
        text: Text to emphasize
        style: Style type ('bold', 'italic', 'strikethrough', 'monospace')
        
    Returns:
        Formatted text
    """
    styles = {
        'bold': f"*{text}*",
        'italic': f"_{text}_",
        'strikethrough': f"~{text}~",
        'monospace': f"```{text}```"
    }
    
    return styles.get(style, text)


def create_whatsapp_divider(char: str = "━", length: int = 30) -> str:
    """
    Create a visual divider for WhatsApp messages
    
    Args:
        char: Character to use for divider
        length: Length of divider
        
    Returns:
        Divider string
    """
    return char * length


def format_whatsapp_body(text: str) -> str:
    """
    Format plain text message body for WhatsApp with proper styling
    Auto-detects structure and adds appropriate formatting
    
    Args:
        text: Plain text message
        
    Returns:
        WhatsApp formatted text
    """
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
        
        # Check if line looks like a heading
        if line.endswith(':') and len(line) < 50:
            formatted_lines.append(f"*{line}*")
        # Check if line starts with bullet point
        elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
            content = line[1:].strip()
            formatted_lines.append(f"  • {content}")
        # Check if line looks like a list item (starts with number)
        elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            formatted_lines.append(f"  {line}")
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)
