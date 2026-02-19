"""
Email AI Analyzer for Hotel Management Bot
Uses AI to analyze and categorize incoming emails
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Check if OpenAI is available
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Cache for encrypted secrets - loaded once at module level
_secrets_cache = {}


def set_secrets_cache(secrets: dict):
    """
    Set the secrets cache from external source (e.g., main.py)
    This avoids creating multiple SecurityManager instances
    
    Args:
        secrets: Dictionary with 'openai_api_key', 'sender_email', 'app_password'
    """
    global _secrets_cache
    _secrets_cache = secrets
    print(f"🔐 Secrets cache updated")
    print(f"   - OpenAI API Key: {'✓' if secrets.get('openai_api_key') else '✗'}")
    print(f"   - Sender Email: {'✓' if secrets.get('sender_email') else '✗'}")
    print(f"   - App Password: {'✓' if secrets.get('app_password') else '✗'}")


def get_openai_key() -> Optional[str]:
    """
    Retrieve OpenAI API key from cache or environment variable
    Cache should be set by calling set_secrets_cache() first
    """
    # First try environment variable (for backward compatibility)
    env_key = os.getenv('OPENAI_API_KEY', '')
    if env_key:
        return env_key
    
    # Try cached secrets
    return _secrets_cache.get('openai_api_key', '')


def is_email_ai_enabled() -> bool:
    """Check if email AI analysis is enabled"""
    if not OPENAI_AVAILABLE:
        return False
    api_key = get_openai_key()
    return bool(api_key and len(api_key) > 10)


class EmailAIAnalyzer:
    """AI-powered email analysis and categorization"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.client = None
        
        if OPENAI_AVAILABLE:
            api_key = get_openai_key()
            if api_key:
                try:
                    self.client = AsyncOpenAI(api_key=api_key)
                    print(f"✅ EmailAIAnalyzer initialized with OpenAI")
                except Exception as e:
                    print(f"❌ Failed to initialize OpenAI client: {e}")
        
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    async def analyze_email(self, email_content: Dict) -> Optional[Dict]:
        """
        Analyze email content and extract key information
        
        Args:
            email_content: Dictionary with 'subject', 'body', 'sender'
            
        Returns:
            Analysis result dictionary or None if failed
        """
        if not self.client:
            return None
        
        try:
            prompt = f"""Analyze this email and extract key information:

Subject: {email_content.get('subject', '')}
From: {email_content.get('sender', '')}
Body: {email_content.get('body', '')[:2000]}

Please provide:
1. Category (booking, complaint, inquiry, feedback, spam, other)
2. Priority (high, medium, low)
3. Summary (1-2 sentences)
4. Suggested action
5. Key entities (names, dates, room numbers, etc.)

Respond in JSON format."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a hotel email analyzer. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                # Clean up response if needed
                if '```json' in result_text:
                    result_text = result_text.split('```json')[1].split('```')[0]
                elif '```' in result_text:
                    result_text = result_text.split('```')[1].split('```')[0]
                
                result = json.loads(result_text.strip())
                result['analyzed_at'] = datetime.now().isoformat()
                return result
                
            except json.JSONDecodeError:
                return {
                    'category': 'other',
                    'priority': 'medium',
                    'summary': 'Unable to parse AI response',
                    'raw_response': result_text,
                    'analyzed_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Email analysis error: {e}")
            return None
    
    async def categorize_emails(self, emails: List[Dict]) -> List[Dict]:
        """
        Categorize multiple emails
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            List of emails with added analysis
        """
        results = []
        
        for email in emails:
            analysis = await self.analyze_email(email)
            email_with_analysis = email.copy()
            email_with_analysis['analysis'] = analysis
            results.append(email_with_analysis)
        
        return results
    
    async def generate_reply_suggestion(self, email_content: Dict, lang: str = 'en') -> Optional[str]:
        """
        Generate a suggested reply for an email
        
        Args:
            email_content: Original email content
            lang: Language for reply
            
        Returns:
            Suggested reply text or None
        """
        if not self.client:
            return None
        
        try:
            lang_instruction = {
                'en': 'Reply in English',
                'sr': 'Reply in Serbian',
                'ko': 'Reply in Korean'
            }.get(lang, 'Reply in English')
            
            prompt = f"""Generate a professional hotel reply to this email:

Subject: {email_content.get('subject', '')}
From: {email_content.get('sender', '')}
Body: {email_content.get('body', '')[:1500]}

{lang_instruction}. Be polite, professional, and helpful.
If this is a booking inquiry, acknowledge and request more details.
If this is a complaint, apologize and offer solution.
Keep the reply concise."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional hotel receptionist writing email replies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Reply generation error: {e}")
            return None
    
    async def extract_booking_details(self, email_content: Dict) -> Optional[Dict]:
        """
        Extract booking details from an email
        
        Args:
            email_content: Email content dictionary
            
        Returns:
            Extracted booking details or None
        """
        if not self.client:
            return None
        
        try:
            prompt = f"""Extract booking details from this email:

Subject: {email_content.get('subject', '')}
Body: {email_content.get('body', '')[:2000]}

Extract if available:
- Guest name
- Check-in date
- Check-out date
- Number of guests
- Room type preference
- Special requests
- Contact information

Respond in JSON format. Use null for unavailable fields."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a booking information extractor. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400
            )
            
            result_text = response.choices[0].message.content
            
            try:
                if '```json' in result_text:
                    result_text = result_text.split('```json')[1].split('```')[0]
                elif '```' in result_text:
                    result_text = result_text.split('```')[1].split('```')[0]
                
                return json.loads(result_text.strip())
                
            except json.JSONDecodeError:
                return None
                
        except Exception as e:
            print(f"❌ Booking extraction error: {e}")
            return None
    
    async def analyze_and_generate_email_async(self, user_input: str, department: str, recipient_count: int, sender_info: Dict) -> Dict:
        """
        Async version: Analyze user input and generate professional email template
        
        Args:
            user_input: User's message describing what email they want
            department: Target department
            recipient_count: Number of recipients
            sender_info: Dictionary with sender information (name, email, phone, hotel_name)
            
        Returns:
            Dictionary with subject, body, body_html, summary, category, tone
        """
        print(f"🤖 analyze_and_generate_email_async called")
        print(f"   User input: {user_input[:50]}...")
        print(f"   Department: {department}")
        print(f"   Recipients: {recipient_count}")
        print(f"   Client available: {'Yes' if self.client else 'No'}")
        
        if not self.client:
            print(f"   ⚠️ No client available, using fallback template")
            # Fallback to simple template if AI not available
            return {
                'subject': f'{department} Department - Important Notice',
                'body': user_input,
                'body_html': f'<p>{user_input}</p>',
                'summary': user_input[:100],
                'category': 'general',
                'tone': 'professional'
            }
        
        try:
            print(f"   🚀 Calling OpenAI API...")
            # Create prompt for AI
            prompt = f"""You are a professional email composer for a hotel management system.

Task: Generate a professional email based on the following information:

USER REQUEST: {user_input}
DEPARTMENT: {department}
NUMBER OF RECIPIENTS: {recipient_count}
SENDER NAME: {sender_info.get('name', 'Hotel Manager')}
SENDER EMAIL: {sender_info.get('email', 'manager@hotel.com')}
HOTEL NAME: {sender_info.get('hotel_name', 'Grand Hotel')}

Please generate:
1. A clear, professional email subject line
2. A well-structured email body in plain text
3. An HTML version of the email body with basic formatting
4. A brief summary (1-2 sentences) of what the email is about
5. Category (reminder, announcement, instruction, request, other)
6. Tone (formal, professional, friendly, urgent)

The email should be:
- Professional and clear
- Appropriate for hotel staff communication
- Include proper greeting and closing
- Well-formatted and easy to read

Respond in JSON format with these exact keys:
{{
  "subject": "email subject",
  "body": "plain text body",
  "body_html": "HTML formatted body",
  "summary": "brief summary",
  "category": "category",
  "tone": "tone"
}}"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional hotel email composer. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            print(f"   ✅ OpenAI API response received")
            result_text = response.choices[0].message.content
            print(f"   Response length: {len(result_text)} characters")
            print(f"   First 100 chars: {result_text[:100]}")
            
            # Parse JSON response
            try:
                # Clean up response if needed
                if '```json' in result_text:
                    result_text = result_text.split('```json')[1].split('```')[0]
                elif '```' in result_text:
                    result_text = result_text.split('```')[1].split('```')[0]
                
                result = json.loads(result_text.strip())
                
                # Ensure all required keys are present
                result.setdefault('subject', f'{department} - Notice')
                result.setdefault('body', user_input)
                result.setdefault('body_html', f'<p>{user_input}</p>')
                result.setdefault('summary', user_input[:100])
                result.setdefault('category', 'general')
                result.setdefault('tone', 'professional')
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"Raw response: {result_text}")
                # Return fallback
                return {
                    'subject': f'{department} Department - Important Notice',
                    'body': user_input,
                    'body_html': f'<p>{user_input}</p>',
                    'summary': user_input[:100],
                    'category': 'general',
                    'tone': 'professional'
                }
                
        except Exception as e:
            print(f"❌ Email generation error: {e}")
            import traceback
            traceback.print_exc()
            # Return fallback
            return {
                'subject': f'{department} Department - Important Notice',
                'body': user_input,
                'body_html': f'<p>{user_input}</p>',
                'summary': user_input[:100],
                'category': 'general',
                'tone': 'professional'
            }
    
    async def analyze_and_generate_whatsapp_async(self, user_input: str, department: str, recipient_count: int, sender_info: Dict) -> Dict:
        """
        Async version: Analyze user input and generate professional WhatsApp message template
        
        Args:
            user_input: User's message describing what they want to send
            department: Target department
            recipient_count: Number of recipients
            sender_info: Dictionary with sender information (name, phone, hotel_name)
            
        Returns:
            Dictionary with message, summary, category, tone
        """
        print(f"📱 analyze_and_generate_whatsapp_async called")
        print(f"   User input: {user_input[:50]}...")
        print(f"   Department: {department}")
        print(f"   Recipients: {recipient_count}")
        print(f"   Client available: {'Yes' if self.client else 'No'}")
        
        if not self.client:
            print(f"   ⚠️ No client available, using fallback template")
            # Fallback to simple template if AI not available
            return {
                'message': user_input,
                'summary': user_input[:100],
                'category': 'general',
                'tone': 'professional'
            }
        
        try:
            print(f"   🚀 Calling OpenAI API...")
            # Create prompt for AI
            prompt = f"""You are a professional WhatsApp message composer for a hotel management system.

Task: Generate a professional WhatsApp message based on the following information:

USER REQUEST: {user_input}
DEPARTMENT: {department}
NUMBER OF RECIPIENTS: {recipient_count}
SENDER NAME: {sender_info.get('name', 'Hotel Manager')}
HOTEL NAME: {sender_info.get('hotel_name', 'Grand Hotel')}

Please generate:
1. A clear, professional WhatsApp message (should be concise, 2-3 paragraphs max)
2. A brief summary (1-2 sentences) of what the message is about
3. Category (reminder, announcement, instruction, request, urgent, other)
4. Tone (formal, professional, friendly, urgent)

The message should be:
- Professional but conversational (suitable for WhatsApp)
- Clear and concise
- Include proper greeting
- Direct and actionable
- Maximum 300 words (WhatsApp messages should be brief)

WhatsApp messages are different from emails - they should be:
- More conversational and direct
- Shorter and easier to read on mobile
- Use emojis sparingly and professionally
- Get to the point quickly

Respond in JSON format with these exact keys:
{{
  "message": "the WhatsApp message text",
  "summary": "brief summary",
  "category": "category",
  "tone": "tone"
}}"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional hotel WhatsApp message composer. Always respond with valid JSON only. Keep messages concise and suitable for WhatsApp."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            print(f"   ✅ OpenAI API response received")
            result_text = response.choices[0].message.content
            print(f"   Response length: {len(result_text)} characters")
            print(f"   First 100 chars: {result_text[:100]}")
            
            # Parse JSON response
            try:
                # Clean up response if needed
                if '```json' in result_text:
                    result_text = result_text.split('```json')[1].split('```')[0]
                elif '```' in result_text:
                    result_text = result_text.split('```')[1].split('```')[0]
                
                result = json.loads(result_text.strip())
                
                # Ensure all required keys are present
                result.setdefault('message', user_input)
                result.setdefault('summary', user_input[:100])
                result.setdefault('category', 'general')
                result.setdefault('tone', 'professional')
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"Raw response: {result_text}")
                # Return fallback
                return {
                    'message': user_input,
                    'summary': user_input[:100],
                    'category': 'general',
                    'tone': 'professional'
                }
                
        except Exception as e:
            print(f"❌ WhatsApp message generation error: {e}")
            import traceback
            traceback.print_exc()
            # Return fallback
            return {
                'message': user_input,
                'summary': user_input[:100],
                'category': 'general',
                'tone': 'professional'
            }


# Singleton instance
_email_analyzer = None


def get_email_analyzer() -> EmailAIAnalyzer:
    """Get or create the EmailAIAnalyzer singleton"""
    global _email_analyzer
    if _email_analyzer is None:
        _email_analyzer = EmailAIAnalyzer()
    return _email_analyzer
