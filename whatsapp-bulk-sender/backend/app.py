# app.py - Main Flask Application
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import sqlite3
import uuid
import os
from datetime import datetime
import re
from celery import Celery
import json
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Celery
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6380/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6380/0')

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    # Campaigns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            message_template TEXT NOT NULL,
            total_contacts INTEGER,
            rate_limit INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT,
            phone_number TEXT,
            name TEXT,
            message_content TEXT,
            status TEXT DEFAULT 'pending',
            sent_at TIMESTAMP,
            delivered_at TIMESTAMP,
            failed_at TIMESTAMP,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def validate_phone_number(phone):
    """Validate and format phone number"""
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', str(phone))
    
    # Add country code if missing (assuming Kenya +254)
    if len(phone) == 9 and phone.startswith('7'):
        phone = '254' + phone
    elif len(phone) == 10 and phone.startswith('07'):
        phone = '254' + phone[1:]
    
    # Validate final format
    if len(phone) >= 10 and phone.isdigit():
        return phone
    return None

def parse_excel_file(file_path):
    """Parse Excel file and extract contact information"""
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Clean column names (remove extra spaces)
        df.columns = df.columns.str.strip().str.lower()
        
        # Required columns validation
        required_cols = ['phone', 'name']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return None, f"Missing required columns: {missing_cols}"
        
        contacts = []
        for _, row in df.iterrows():
            phone = validate_phone_number(row['phone'])
            if phone:
                contact = {
                    'phone': phone,
                    'name': str(row['name']).strip(),
                }
                
                # Add any additional columns as custom fields
                for col in df.columns:
                    if col not in ['phone', 'name']:
                        contact[col] = str(row[col]) if pd.notna(row[col]) else ''
                
                contacts.append(contact)
        
        return contacts, None
    
    except Exception as e:
        return None, f"Error parsing Excel file: {str(e)}"

def personalize_message(template, contact):
    """Replace placeholders in message template with contact data"""
    message = template
    
    # Replace all placeholders with contact data
    for key, value in contact.items():
        placeholder = '{' + key + '}'
        message = message.replace(placeholder, str(value))
    
    return message

@app.route('/api/start-campaign', methods=['POST'])
def start_campaign():
    """Start a new WhatsApp campaign"""
    try:
        # Get form data
        campaign_name = request.form.get('campaign_name')
        message_template = request.form.get('message_template')
        rate_limit = int(request.form.get('rate_limit', 2))
        api_key = request.form.get('api_key')
        
        # Validate required fields
        if not all([campaign_name, message_template, api_key]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Handle file upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        
        # Parse Excel file
        contacts, error = parse_excel_file(file_path)
        if error:
            os.remove(file_path)  # Clean up
            return jsonify({'error': error}), 400
        
        if not contacts:
            os.remove(file_path)  # Clean up
            return jsonify({'error': 'No valid contacts found'}), 400
        
        # Create campaign
        campaign_id = str(uuid.uuid4())
        
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Insert campaign
        cursor.execute('''
            INSERT INTO campaigns (id, name, message_template, total_contacts, rate_limit, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (campaign_id, campaign_name, message_template, len(contacts), rate_limit))
        
        # Insert messages
        for contact in contacts:
            personalized_message = personalize_message(message_template, contact)
            cursor.execute('''
                INSERT INTO messages (campaign_id, phone_number, name, message_content)
                VALUES (?, ?, ?, ?)
            ''', (campaign_id, contact['phone'], contact['name'], personalized_message))
        
        conn.commit()
        conn.close()
        
        # Clean up uploaded file
        os.remove(file_path)
        
        # Start Celery task to process messages
        from celery_worker import process_campaign_task
        process_campaign_task.delay(campaign_id, api_key, rate_limit)
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'total_contacts': len(contacts)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/campaign-status/<campaign_id>', methods=['GET'])
def get_campaign_status(campaign_id):
    """Get campaign status and statistics"""
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Get campaign info
        cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
        campaign = cursor.fetchone()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Get message statistics
        cursor.execute('''
            SELECT 
                status,
                COUNT(*) as count
            FROM messages 
            WHERE campaign_id = ?
            GROUP BY status
        ''', (campaign_id,))
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = row[1]
        
        conn.close()
        
        return jsonify({
            'campaign': {
                'id': campaign[0],
                'name': campaign[1],
                'status': campaign[5],
                'total_contacts': campaign[3],
                'created_at': campaign[6]
            },
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    """Get all campaigns"""
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # First, check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'campaigns' not in tables:
            conn.close()
            return jsonify({'campaigns': []})
        
        cursor.execute('''
            SELECT c.id, c.name, c.message_template, c.total_contacts, c.rate_limit, c.status, c.created_at,
                   COUNT(m.id) as total_messages,
                   SUM(CASE WHEN m.status = 'sent' THEN 1 ELSE 0 END) as sent_messages,
                   SUM(CASE WHEN m.status = 'delivered' THEN 1 ELSE 0 END) as delivered_messages,
                   SUM(CASE WHEN m.status = 'failed' THEN 1 ELSE 0 END) as failed_messages
            FROM campaigns c
            LEFT JOIN messages m ON c.id = m.campaign_id
            GROUP BY c.id, c.name, c.message_template, c.total_contacts, c.rate_limit, c.status, c.created_at
            ORDER BY c.created_at DESC
        ''')
        
        campaigns = []
        for row in cursor.fetchall():
            campaigns.append({
                'id': row[0],
                'name': row[1],
                'status': row[5],
                'total_contacts': row[3],
                'created_at': row[6],
                'total_messages': row[7] or 0,
                'sent_messages': row[8] or 0,
                'delivered_messages': row[9] or 0,
                'failed_messages': row[10] or 0
            })
        
        conn.close()
        return jsonify({'campaigns': campaigns})
    
    except Exception as e:
        print(f"Error in get_campaigns: {str(e)}")
        return jsonify({'campaigns': [], 'error': str(e)}), 200  # Return 200 with empty array instead of 500

# WhatsApp Reply Collection Routes
@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages (replies to our campaigns)"""
    try:
        # Import reply handling functions
        from reply_handler import store_reply, detect_reply_sentiment, is_opt_out_message, generate_auto_response
        
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
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        offset = (page - 1) * per_page
        
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Build query with filters
        where_conditions = []
        params = []
        
        if campaign_id:
            where_conditions.append("r.campaign_id = ?")
            params.append(campaign_id)
        
        if sentiment:
            where_conditions.append("r.sentiment = ?")
            params.append(sentiment)
        
        if start_date:
            where_conditions.append("r.received_at >= ?")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("r.received_at <= ?")
            params.append(end_date + ' 23:59:59')  # Include end of day
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM replies r {where_clause}"
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

@app.route('/api/replies/download', methods=['GET'])
def download_replies():
    """Download filtered replies as Excel file"""
    try:
        import pandas as pd
        from io import BytesIO
        from datetime import datetime
        
        # Get query parameters for filtering
        campaign_id = request.args.get('campaign_id')
        sentiment = request.args.get('sentiment')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Build query with filters
        where_conditions = []
        params = []
        
        if campaign_id:
            where_conditions.append("r.campaign_id = ?")
            params.append(campaign_id)
        
        if sentiment:
            where_conditions.append("r.sentiment = ?")
            params.append(sentiment)
        
        if start_date:
            where_conditions.append("r.received_at >= ?")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("r.received_at <= ?")
            params.append(end_date + ' 23:59:59')  # Include end of day
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get filtered replies
        query = f"""
            SELECT 
                r.sender_name as "Contact Name",
                r.phone_number as "Phone Number",
                r.message_content as "Reply Message",
                r.received_at as "Reply Date & Time",
                c.name as "Campaign Name",
                r.sentiment as "Sentiment",
                r.reply_type as "Reply Type",
                CASE WHEN r.is_opt_out = 1 THEN 'Yes' ELSE 'No' END as "Opted Out"
            FROM replies r
            LEFT JOIN campaigns c ON r.campaign_id = c.id
            {where_clause}
            ORDER BY r.received_at DESC
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            conn.close()
            return jsonify({'error': 'No replies found for the specified filters'}), 404
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # Format the date column
        df['Reply Date & Time'] = pd.to_datetime(df['Reply Date & Time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='WhatsApp Replies', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['WhatsApp Replies']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        conn.close()
        
        # Generate filename with timestamp and filters
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_parts = ['whatsapp_replies', timestamp]
        
        if campaign_id:
            # Get campaign name for filename
            conn_temp = sqlite3.connect('whatsapp_campaigns.db')
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("SELECT name FROM campaigns WHERE id = ?", (campaign_id,))
            campaign_result = cursor_temp.fetchone()
            if campaign_result:
                campaign_name = campaign_result[0].replace(' ', '_').replace('/', '_')
                filename_parts.append(f'campaign_{campaign_name}')
            conn_temp.close()
        
        if sentiment:
            filename_parts.append(f'sentiment_{sentiment}')
        
        filename = '_'.join(filename_parts) + '.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    # Initialize reply database
    from reply_handler import setup_replies_database
    setup_replies_database()
    app.run(debug=True, port=5000)
