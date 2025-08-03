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

# Load environment variables
load_dotenv()

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
            is_opt_out BOOLEAN DEFAULT FALSE,
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

def detect_reply_sentiment(message_content):
    """Basic sentiment detection for replies"""
    message_lower = message_content.lower()
    
    # Positive keywords
    positive_words = ['yes', 'interested', 'great', 'awesome', 'love', 'want', 'buy', 'purchase', 'order', 'info', 'information', 'tell me more', 'sounds good']
    
    # Negative keywords  
    negative_words = ['no', 'not interested', 'stop', 'unsubscribe', 'remove', 'dont', "don't", 'never', 'hate', 'spam']
    
    # Neutral/Question keywords
    question_words = ['?', 'how', 'what', 'when', 'where', 'price', 'cost', 'available']
    
    positive_count = sum(1 for word in positive_words if word in message_lower)
    negative_count = sum(1 for word in negative_words if word in message_lower)
    question_count = sum(1 for word in question_words if word in message_lower)
    
    if negative_count > 0:
        return 'negative'
    elif positive_count > 0:
        return 'positive' 
    elif question_count > 0:
        return 'question'
    else:
        return 'neutral'

def is_opt_out_message(message_content):
    """Check if message is an opt-out request"""
    opt_out_keywords = ['stop', 'unsubscribe', 'remove', 'opt out', 'optout', 'quit']
    return any(keyword in message_content.lower() for keyword in opt_out_keywords)

def store_reply(phone_number, message_content, media_url=None, media_type=None):
    """Store incoming WhatsApp reply in database"""
    try:
        # Setup database if needed
        setup_replies_database()
        
        # Find related campaign
        campaign_id, message_id = find_related_campaign(phone_number)
        
        # Detect sentiment
        sentiment = detect_reply_sentiment(message_content)
        
        # Check for opt-out
        opt_out = is_opt_out_message(message_content)
        
        # Get sender name if we have it in our contacts
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name FROM messages 
            WHERE phone_number = ? 
            ORDER BY sent_at DESC 
            LIMIT 1
        ''', (phone_number,))
        
        name_result = cursor.fetchone()
        sender_name = name_result[0] if name_result else 'Unknown'
        
        # Store the reply
        cursor.execute('''
            INSERT INTO replies (
                phone_number, sender_name, message_content, 
                campaign_id, original_message_id, reply_type,
                media_url, media_type, sentiment, is_opt_out
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            phone_number, sender_name, message_content,
            campaign_id, message_id, 'media' if media_url else 'text',
            media_url, media_type, sentiment, opt_out
        ))
        
        reply_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Reply stored: ID {reply_id}, From: {phone_number}, Sentiment: {sentiment}")
        return reply_id
        
    except Exception as e:
        print(f"❌ Error storing reply: {str(e)}")
        return None

def generate_auto_response(message_content, sentiment, is_opt_out):
    """Generate automatic response based on reply content"""
    
    if is_opt_out:
        return "Thank you for your message. You have been removed from our messaging list. You will not receive further messages from Mwihaki Intimates."
    
    if sentiment == 'positive':
        return "Thank you for your interest in Mwihaki Intimates! 😊 A member of our team will contact you shortly with more information. You can also visit our store or browse our collection online."
    
    elif sentiment == 'question':
        return "Thank you for your question! 🤔 Our customer service team will get back to you within 24 hours with detailed information. For immediate assistance, please call us or visit our store."
    
    elif sentiment == 'negative':
        return "We appreciate your feedback. If you no longer wish to receive messages, please reply with STOP. Thank you for considering Mwihaki Intimates."
    
    else:  # neutral
        return "Thank you for your message! 📱 We've received your reply and will follow up if needed. For immediate assistance, please contact our customer service team."

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
