#!/usr/bin/env python3
"""
WhatsApp Reply Collection System
Handles incoming WhatsApp messages (replies) via Twilio webhook
"""

from flask import request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import time

# Load environment variables
load_dotenv()

# Configure Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Rate limiting and retry configuration
GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_DELAY = 60  # seconds
gemini_last_error_time = 0
gemini_consecutive_failures = 0

def setup_replies_database():
    """Create database table for storing WhatsApp replies"""
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            sender_name TEXT,
            message_content TEXT NOT NULL,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            campaign_id TEXT,
            original_message_id TEXT,
            reply_type TEXT DEFAULT 'text',
            media_url TEXT,
            media_type TEXT,
            sentiment TEXT,
            confidence_score REAL,
            is_opt_out BOOLEAN DEFAULT FALSE,
            requires_attention BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_replies_phone 
        ON replies(phone_number)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_replies_campaign 
        ON replies(campaign_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_replies_attention 
        ON replies(requires_attention)
    ''')
    
    conn.commit()
    conn.close()

def find_related_campaign(phone_number):
    """Find the most recent campaign this phone number was part of"""
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Find the most recent message sent to this phone number
        cursor.execute('''
            SELECT campaign_id, id FROM messages 
            WHERE phone_number = ? 
            ORDER BY sent_at DESC 
            LIMIT 1
        ''', (phone_number,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0], result[1]  # campaign_id, message_id
        return None, None
        
    except Exception as e:
        print(f"Error finding related campaign: {str(e)}")
        return None, None

def detect_reply_sentiment_gemini(message_content, phone_number=None, retry_count=0):
    """
    Advanced sentiment detection using Gemini AI with enhanced opt-out detection
    and robust error handling including rate limiting and retry logic.
    """
    global gemini_consecutive_failures, gemini_last_error_time
    
    try:
        # Check if we should wait due to rate limiting
        if gemini_consecutive_failures >= GEMINI_MAX_RETRIES:
            current_time = time.time()
            if current_time - gemini_last_error_time < GEMINI_RETRY_DELAY:
                print(f"⏳ Rate limited, using fallback detection")
                return detect_reply_sentiment_basic(message_content)
            else:
                # Reset failure count after waiting period
                gemini_consecutive_failures = 0
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Analyze this WhatsApp message reply to a business marketing campaign for Mwihaki Intimates (an intimate wear/lingerie business). 
        
        Message: "{message_content}"
        
        Classify it into ONE of these business-focused categories:
        
        1. **INTERESTED** - Shows clear interest in products/services, wants to buy, asks for more info, positive engagement
        2. **COMPLAINT** - Has an issue, complaint, dissatisfaction, problem with product/service (needs immediate attention)
        3. **QUESTION** - Asking about prices, availability, details, how-to, when, where (needs informative response)
        4. **DESIRED_OPT_OUT** - CRITICAL: Customer wants to stop receiving messages. Be EXTREMELY sensitive to ANY indication of wanting to stop messages, including:
            - Direct: "stop", "unsubscribe", "remove me", "delete my number", "don't message me", "not interested"
            - Swahili: "hatutaki", "sitaki", "acha", "wacha", "hapana"
            - Indirect: "remove from list", "I don't want these messages", "stop sending", "block me"
            - Frustrated: "enough", "too many messages", "annoying"
            - ANY language expressing desire to stop receiving messages
        5. **POSITIVE_FEEDBACK** - Happy customer, thanks, compliments, satisfied (good for testimonials)
        6. **NEUTRAL** - Simple acknowledgment, unclear intent, general response
        7. **URGENT** - Emergency, very angry, threatening, serious complaint (needs immediate human attention)
        
        IMPORTANT: If there's ANY doubt about opt-out intention, classify as DESIRED_OPT_OUT. Better to respect customer wishes than continue messaging.
        
        Consider:
        - Multiple languages (English, Swahili, etc.)
        - Emojis and their meanings
        - Cultural context
        - Business implications
        
        Respond with ONLY a JSON object:
        {{
            "category": "INTERESTED",
            "confidence": 0.95,
            "reasoning": "Brief explanation",
            "requires_human_attention": false,
            "suggested_priority": "medium"
        }}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean the response text to extract JSON
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].strip()
        
        print(f"🔍 Gemini raw response: {response_text[:100]}...")
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to clean up malformed JSON
            response_text = response_text.replace('\n', '').replace('\\', '')
            result = json.loads(response_text)
        
        # Map to our existing categories for backward compatibility
        category_mapping = {
            'INTERESTED': 'interested',
            'COMPLAINT': 'complaint', 
            'QUESTION': 'question',
            'DESIRED_OPT_OUT': 'desired_opt_out',
            'POSITIVE_FEEDBACK': 'positive_feedback',
            'NEUTRAL': 'neutral',
            'URGENT': 'urgent'
        }
        
        sentiment = category_mapping.get(result['category'], 'neutral')
        confidence = result.get('confidence', 0.8)
        requires_attention = result.get('requires_human_attention', False)
        
        # Mark urgent/complaint/opt-out items as requiring attention
        if result['category'] in ['URGENT', 'COMPLAINT', 'DESIRED_OPT_OUT']:
            requires_attention = True
        
        # Reset failure count on success
        gemini_consecutive_failures = 0
        
        print(f"🤖 Gemini Analysis: {message_content[:50]}... → {result['category']} ({sentiment}) - Confidence: {confidence}")
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'requires_attention': requires_attention,
            'detailed_category': result['category'],
            'reasoning': result.get('reasoning', '')
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ Gemini JSON parsing error: {str(e)}")
        print(f"📄 Raw response: {response_text if 'response_text' in locals() else 'No response'}")
        gemini_consecutive_failures += 1
        gemini_last_error_time = time.time()
        
        # Retry logic for malformed responses
        if retry_count < GEMINI_MAX_RETRIES:
            print(f"🔄 Retrying Gemini analysis (attempt {retry_count + 1})")
            time.sleep(5)  # Short delay for JSON parsing errors
            return detect_reply_sentiment_gemini(message_content, phone_number, retry_count + 1)
        
        return detect_reply_sentiment_basic(message_content)
        
    except Exception as e:
        print(f"❌ Gemini API error: {str(e)}")
        gemini_consecutive_failures += 1
        gemini_last_error_time = time.time()
        
        # Check if this is a rate limit error and we can retry
        if any(keyword in str(e).lower() for keyword in ['quota', 'rate', 'limit', 'exceeded']):
            if retry_count < GEMINI_MAX_RETRIES:
                print(f"⏳ Rate limited, retrying in {GEMINI_RETRY_DELAY} seconds...")
                time.sleep(GEMINI_RETRY_DELAY)
                return detect_reply_sentiment_gemini(message_content, phone_number, retry_count + 1)
        
        # Fallback to basic detection
        return detect_reply_sentiment_basic(message_content)

def detect_reply_sentiment_basic(message_content):
    """Enhanced fallback basic sentiment detection with comprehensive opt-out detection"""
    message_lower = message_content.lower()
    
    # Enhanced opt-out keywords (high priority) - multiple languages
    opt_out_keywords = [
        # English
        'stop', 'unsubscribe', 'remove', 'opt out', 'optout', 'quit', 'delete',
        'dont message', "don't message", 'not interested', 'no more', 'enough',
        'block', 'remove me', 'delete me', 'take me off', 'annoying',
        # Swahili
        'hatutaki', 'sitaki', 'acha', 'wacha', 'hapana', 'usinitumie',
        'sijadhani', 'sitaki ujumbe', 'ondoa', 'sikitaki'
    ]
    
    # Check for opt-out (most critical)
    if any(word in message_lower for word in opt_out_keywords):
        return {
            'sentiment': 'desired_opt_out',
            'confidence': 0.9,
            'requires_attention': True,
            'detailed_category': 'DESIRED_OPT_OUT',
            'reasoning': 'Contains opt-out keywords'
        }
    
    # Positive keywords (interest/satisfaction)
    positive_words = ['yes', 'interested', 'buy', 'purchase', 'want', 'like', 'love', 
                     'thank', 'good', 'great', 'excellent', 'amazing', 'perfect',
                     'asante', 'nataka', 'poa', 'sawa', 'vizuri']
    
    # Negative/complaint keywords
    negative_words = ['no', 'hate', 'bad', 'terrible', 'angry', 'complain', 'problem', 
                     'issue', 'wrong', 'awful', 'horrible', 'disappointed', 'refund',
                     'mbaya', 'haina', 'tatizo']
    
    # Question indicators
    question_words = ['?', 'how', 'what', 'when', 'where', 'why', 'which', 'price', 
                     'cost', 'available', 'je', 'vipi', 'bei', 'rahisi']
    
    # Urgent keywords
    urgent_words = ['urgent', 'emergency', 'immediately', 'asap', 'help', 'haraka']
    
    positive_count = sum(1 for word in positive_words if word in message_lower)
    negative_count = sum(1 for word in negative_words if word in message_lower)
    question_count = sum(1 for word in question_words if word in message_lower)
    urgent_count = sum(1 for word in urgent_words if word in message_lower)
    
    # Determine sentiment with priority
    if urgent_count > 0:
        sentiment = 'urgent'
        requires_attention = True
    elif negative_count > 0:
        sentiment = 'complaint'
        requires_attention = True
    elif positive_count > 0:
        sentiment = 'interested'
        requires_attention = False
    elif question_count > 0 or '?' in message_content:
        sentiment = 'question'
        requires_attention = False
    else:
        sentiment = 'neutral'
        requires_attention = False
    
    return {
        'sentiment': sentiment,
        'confidence': 0.6,
        'requires_attention': requires_attention,
        'detailed_category': sentiment.upper(),
        'reasoning': 'Basic keyword analysis'
    }

def detect_reply_sentiment(message_content, phone_number=None):
    """Main sentiment detection function with Gemini AI and fallback"""
    # Try Gemini first, fallback to basic if it fails
    if os.getenv('GEMINI_API_KEY'):
        return detect_reply_sentiment_gemini(message_content, phone_number)
    else:
        print("⚠️ No Gemini API key found, using basic detection")
        return detect_reply_sentiment_basic(message_content)

def is_opt_out_message(message_content):
    """Enhanced check if message is an opt-out request with multiple languages"""
    opt_out_keywords = [
        # English
        'stop', 'unsubscribe', 'remove', 'opt out', 'optout', 'quit', 'delete',
        'dont message', "don't message", 'not interested', 'no more', 'enough',
        'block', 'remove me', 'delete me', 'take me off', 'annoying',
        # Swahili
        'hatutaki', 'sitaki', 'acha', 'wacha', 'hapana', 'usinitumie',
        'sijadhani', 'sitaki ujumbe', 'ondoa', 'sikitaki'
    ]
    return any(keyword in message_content.lower() for keyword in opt_out_keywords)

def normalize_phone_number(phone_number):
    """Normalize phone numbers to find variations (0712345678 = +254712345678 = 254712345678)"""
    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone_number))
    
    # Handle common Kenyan number formats
    if digits_only.startswith('254'):
        # Already in international format
        normalized = '+' + digits_only
    elif digits_only.startswith('0') and len(digits_only) == 10:
        # Local format (0712345678) -> +254712345678
        normalized = '+254' + digits_only[1:]
    elif len(digits_only) == 9:
        # Missing leading zero (712345678) -> +254712345678  
        normalized = '+254' + digits_only
    else:
        # Default: add + if not present
        normalized = '+' + digits_only if not phone_number.startswith('+') else phone_number
    
    return normalized

def get_phone_number_variations(phone_number):
    """Get all possible variations of a phone number"""
    normalized = normalize_phone_number(phone_number)
    
    # Extract digits for variations
    digits_only = ''.join(filter(str.isdigit, normalized))
    
    variations = [
        normalized,  # +254712345678
        digits_only,  # 254712345678
        '0' + digits_only[3:] if digits_only.startswith('254') else normalized,  # 0712345678
        digits_only[3:] if digits_only.startswith('254') else normalized,  # 712345678
        'whatsapp:' + normalized,  # whatsapp:+254712345678
    ]
    
    return list(set(variations))  # Remove duplicates

def store_reply(phone_number, message_content, media_url=None, media_type=None):
    """Store incoming WhatsApp reply in database with enhanced opt-out handling"""
    try:
        # Setup database if needed
        setup_replies_database()
        
        # Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)
        
        # Find related campaign using phone number variations
        campaign_id, message_id = find_related_campaign(normalized_phone)
        if not campaign_id:
            # Try with variations
            for variation in get_phone_number_variations(phone_number):
                campaign_id, message_id = find_related_campaign(variation)
                if campaign_id:
                    break
        
        # Detect sentiment using Gemini AI
        sentiment_result = detect_reply_sentiment(message_content, normalized_phone)
        sentiment = sentiment_result['sentiment']
        confidence = sentiment_result['confidence']
        requires_attention = sentiment_result['requires_attention']
        
        # Check for opt-out (multiple methods for reliability)
        is_opt_out_detected = (
            is_opt_out_message(message_content) or 
            sentiment_result['detailed_category'] == 'DESIRED_OPT_OUT' or
            sentiment == 'desired_opt_out'
        )
        
        # Get sender name if we have it in our contacts
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Try to find name using phone number variations
        sender_name = 'Unknown'
        for variation in get_phone_number_variations(phone_number):
            cursor.execute('''
                SELECT name FROM messages 
                WHERE phone_number = ? 
                ORDER BY sent_at DESC 
                LIMIT 1
            ''', (variation,))
            
            name_result = cursor.fetchone()
            if name_result:
                sender_name = name_result[0]
                break
        
        # Store the reply with enhanced data
        cursor.execute('''
            INSERT INTO replies (
                phone_number, sender_name, message_content, 
                campaign_id, original_message_id, reply_type,
                media_url, media_type, sentiment, confidence_score,
                is_opt_out, requires_attention
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            normalized_phone, sender_name, message_content,
            campaign_id, message_id, 'media' if media_url else 'text',
            media_url, media_type, sentiment, confidence,
            is_opt_out_detected, requires_attention
        ))
        
        reply_id = cursor.lastrowid
        
        # If this is an opt-out, schedule opt-out confirmation and remove from future campaigns
        if is_opt_out_detected:
            schedule_opt_out_confirmation(normalized_phone, sender_name)
            mark_phone_as_opted_out(normalized_phone)
        
        conn.commit()
        conn.close()
        
        # Enhanced logging
        attention_flag = "🚨" if requires_attention else ""
        confidence_indicator = "🎯" if confidence > 0.8 else "📊"
        opt_out_flag = "🚫" if is_opt_out_detected else ""
        
        print(f"✅ Reply stored: ID {reply_id}, From: {normalized_phone}")
        print(f"   {confidence_indicator} Sentiment: {sentiment} (confidence: {confidence:.2f})")
        print(f"   {attention_flag} Category: {sentiment_result['detailed_category']}")
        if requires_attention:
            print(f"   ⚠️ Requires human attention: {sentiment_result['reasoning']}")
        if is_opt_out_detected:
            print(f"   {opt_out_flag} OPT-OUT DETECTED - Customer will be unsubscribed")
        
        return reply_id
        
    except Exception as e:
        print(f"❌ Error storing reply: {str(e)}")
        return None

def schedule_opt_out_confirmation(phone_number, sender_name, schedule_option="now"):
    """Schedule opt-out confirmation message to be sent"""
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Create opt_out_queue table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opt_out_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                sender_name TEXT,
                scheduled_time TIMESTAMP,
                sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Calculate scheduled time based on option
        if schedule_option == "now":
            scheduled_time = datetime.now().isoformat()
        elif schedule_option.startswith("after_"):
            hours = int(schedule_option.split("_")[1])
            from datetime import timedelta
            scheduled_time = (datetime.now() + timedelta(hours=hours)).isoformat()
        else:
            scheduled_time = datetime.now().isoformat()  # Default to now
        
        cursor.execute('''
            INSERT INTO opt_out_queue (phone_number, sender_name, scheduled_time)
            VALUES (?, ?, ?)
        ''', (phone_number, sender_name, scheduled_time))
        
        conn.commit()
        conn.close()
        
        print(f"📋 Opt-out confirmation scheduled for {phone_number} at {scheduled_time}")
        
    except Exception as e:
        print(f"❌ Error scheduling opt-out confirmation: {str(e)}")

def mark_phone_as_opted_out(phone_number):
    """Mark phone number and all its variations as opted out"""
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Create opt_out_list table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opt_out_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT UNIQUE,
                opted_out_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add all phone number variations to opt-out list
        variations = get_phone_number_variations(phone_number)
        for variation in variations:
            cursor.execute('''
                INSERT OR IGNORE INTO opt_out_list (phone_number)
                VALUES (?)
            ''', (variation,))
        
        conn.commit()
        conn.close()
        
        print(f"🚫 Phone number {phone_number} and variations marked as opted out")
        
    except Exception as e:
        print(f"❌ Error marking phone as opted out: {str(e)}")

def generate_auto_response(message_content, sentiment_result, is_opt_out):
    """
    Generate automatic response based on reply content and Gemini analysis.
    All responses are fully compliant with WhatsApp Business requirements.
    """
    
    sentiment = sentiment_result['sentiment']
    detailed_category = sentiment_result.get('detailed_category', sentiment.upper())
    
    # CRITICAL: Handle opt-out requests immediately and respectfully
    if is_opt_out or detailed_category == 'DESIRED_OPT_OUT' or sentiment == 'desired_opt_out':
        return "Thank you for your message. You have been unsubscribed and will not receive further marketing messages from Mwihaki Intimates. We respect your decision. Have a wonderful day! 🙏\n\nMwihaki Intimates"
    
    # Business-focused responses with mandatory compliance elements
    if detailed_category == 'INTERESTED' or sentiment == 'interested':
        return "Thank you for your interest in Mwihaki Intimates! 😊 We're excited to help you discover intimate wear that combines comfort, style & confidence. Our team will contact you with personalized recommendations.\n\nReply STOP to opt out | Mwihaki Intimates"
    
    elif detailed_category == 'POSITIVE_FEEDBACK' or sentiment == 'positive_feedback':
        return "Thank you so much for your wonderful feedback! 💝 Your satisfaction means everything to us at Mwihaki Intimates. We're delighted you're happy with your experience.\n\nReply STOP to opt out | Mwihaki Intimates"
    
    elif detailed_category == 'QUESTION' or sentiment == 'question':
        return "Thank you for your question! 🤔 Our expert customer service team will respond within 2 hours with detailed information. For immediate assistance, please call us or visit our store.\n\nReply STOP to opt out | Mwihaki Intimates"
    
    elif detailed_category in ['COMPLAINT', 'URGENT'] or sentiment in ['complaint', 'urgent']:
        return "We sincerely apologize for any inconvenience. 🙏 Your concern is very important to us. Our customer service manager will personally contact you within 1 hour to resolve this matter promptly.\n\nReply STOP to opt out | Mwihaki Intimates"
    
    else:  # NEUTRAL or others
        return "Thank you for your message! 📱 We've received your reply and appreciate you taking the time to respond to Mwihaki Intimates. Our team is here if you need any assistance.\n\nReply STOP to opt out | Mwihaki Intimates"

def get_compliant_opt_out_message(sender_name=""):
    """Generate compliant opt-out confirmation message"""
    name_part = f"{sender_name}, " if sender_name and sender_name != "Unknown" else ""
    
    return f"""Hello {name_part}you have been successfully unsubscribed from Mwihaki Intimates marketing messages.

✅ You will not receive further promotional messages
📞 You can still contact us directly for customer service
🏪 You're always welcome to visit our store

Thank you for your time with us.

Mwihaki Intimates Team"""

# Add this route to your main Flask app (app.py)
WEBHOOK_ROUTE_CODE = '''
@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages (replies to our campaigns)"""
    try:
        # Get incoming message details
        from_number = request.values.get('From', '')
        message_body = request.values.get('Body', '')
        num_media = int(request.values.get('NumMedia', 0))
        
        # Remove 'whatsapp:' prefix to get clean phone number
        clean_phone = from_number.replace('whatsapp:', '')
        
        print(f"📱 Incoming WhatsApp reply from {clean_phone}: {message_body}")
        
        # Handle media if present
        media_url = None
        media_type = None
        if num_media > 0:
            media_url = request.values.get('MediaUrl0')
            media_type = request.values.get('MediaContentType0')
            print(f"📷 Media received: {media_type} - {media_url}")
        
        # Store the reply
        from reply_handler import store_reply, detect_reply_sentiment, is_opt_out_message, generate_auto_response
        
        reply_id = store_reply(clean_phone, message_body, media_url, media_type)
        
        # Generate response
        sentiment = detect_reply_sentiment(message_body)
        opt_out = is_opt_out_message(message_body)
        auto_response = generate_auto_response(message_body, sentiment, opt_out)
        
        # Create TwiML response
        response = MessagingResponse()
        response.message(auto_response)
        
        print(f"🤖 Auto-response sent: {auto_response}")
        
        return str(response)
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        # Return empty response to avoid Twilio retries
        response = MessagingResponse()
        return str(response)

@app.route('/api/replies', methods=['GET'])
def get_replies():
    """Get all WhatsApp replies with pagination and filtering"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        campaign_id = request.args.get('campaign_id')
        sentiment = request.args.get('sentiment')
        
        offset = (page - 1) * per_page
        
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Build query with filters
        where_conditions = []
        params = []
        
        if campaign_id:
            where_conditions.append("campaign_id = ?")
            params.append(campaign_id)
        
        if sentiment:
            where_conditions.append("sentiment = ?")
            params.append(sentiment)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM replies {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Get replies with pagination
        query = f"""
            SELECT r.*, c.name as campaign_name
            FROM replies r
            LEFT JOIN campaigns c ON r.campaign_id = c.id
            {where_clause}
            ORDER BY r.received_at DESC
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, params + [per_page, offset])
        
        replies = []
        for row in cursor.fetchall():
            replies.append({
                'id': row[0],
                'phone_number': row[1],
                'sender_name': row[2],
                'message_content': row[3],
                'received_at': row[4],
                'campaign_id': row[5],
                'original_message_id': row[6],
                'reply_type': row[7],
                'media_url': row[8],
                'media_type': row[9],
                'sentiment': row[10],
                'is_opt_out': bool(row[11]),
                'campaign_name': row[13] if len(row) > 13 else 'Unknown'
            })
        
        conn.close()
        
        return jsonify({
            'replies': replies,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/replies/analytics', methods=['GET'])
def get_reply_analytics():
    """Get analytics about WhatsApp replies"""
    try:
        campaign_id = request.args.get('campaign_id')
        
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        where_clause = "WHERE campaign_id = ?" if campaign_id else ""
        params = [campaign_id] if campaign_id else []
        
        # Get sentiment breakdown
        cursor.execute(f"""
            SELECT sentiment, COUNT(*) as count
            FROM replies {where_clause}
            GROUP BY sentiment
        """, params)
        
        sentiment_data = dict(cursor.fetchall())
        
        # Get reply rate
        if campaign_id:
            cursor.execute("SELECT total_contacts FROM campaigns WHERE id = ?", (campaign_id,))
            total_sent = cursor.fetchone()
            total_sent = total_sent[0] if total_sent else 0
            
            cursor.execute("SELECT COUNT(DISTINCT phone_number) FROM replies WHERE campaign_id = ?", (campaign_id,))
            total_replies = cursor.fetchone()[0]
            
            reply_rate = (total_replies / total_sent * 100) if total_sent > 0 else 0
        else:
            reply_rate = 0
        
        # Get opt-out count
        cursor.execute(f"""
            SELECT COUNT(*) FROM replies 
            {where_clause} AND is_opt_out = 1
        """, params)
        
        opt_outs = cursor.fetchone()[0]
        
        # Get recent replies
        cursor.execute(f"""
            SELECT COUNT(*) FROM replies 
            {where_clause} AND received_at >= datetime('now', '-24 hours')
        """, params)
        
        recent_replies = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'sentiment_breakdown': sentiment_data,
            'reply_rate': round(reply_rate, 2),
            'total_opt_outs': opt_outs,
            'recent_replies_24h': recent_replies
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''

if __name__ == "__main__":
    print("🔧 Setting up WhatsApp Reply Collection System...")
    setup_replies_database()
    print("✅ Database setup complete!")
    print("\n📋 Next Steps:")
    print("1. Add the webhook route code to your app.py")
    print("2. Configure webhook URL in Twilio Console")
    print("3. Test with incoming messages")
