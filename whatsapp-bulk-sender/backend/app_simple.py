# app_simple.py - Simplified Flask Application for testing
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
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    """Get all campaigns"""
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, 
                   COUNT(m.id) as total_messages,
                   SUM(CASE WHEN m.status = 'sent' THEN 1 ELSE 0 END) as sent_messages,
                   SUM(CASE WHEN m.status = 'failed' THEN 1 ELSE 0 END) as failed_messages
            FROM campaigns c
            LEFT JOIN messages m ON c.id = m.campaign_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        ''')
        
        campaigns = []
        for row in cursor.fetchall():
            campaigns.append({
                'id': row[0],
                'name': row[1],
                'message_template': row[2],
                'total_contacts': row[3],
                'rate_limit': row[4],
                'status': row[5],
                'created_at': row[6],
                'started_at': row[7],
                'completed_at': row[8],
                'total_messages': row[9] or 0,
                'sent_messages': row[10] or 0,
                'failed_messages': row[11] or 0
            })
        
        conn.close()
        return jsonify({'campaigns': campaigns})
    except Exception as e:
        print(f"Error in get_campaigns: {str(e)}")
        return jsonify({'campaigns': [], 'error': str(e)}), 200

@app.route('/api/start-campaign', methods=['POST'])
def start_campaign():
    """Start a new WhatsApp campaign"""
    try:
        # Get form data
        campaign_name = request.form.get('campaign_name')
        message_template = request.form.get('message_template')
        rate_limit = int(request.form.get('rate_limit', 2))
        
        # Get uploaded file
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        
        # Read Excel file
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400
        
        # Validate required columns
        required_columns = ['phone', 'name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing required columns: {missing_columns}'}), 400
        
        # Generate campaign ID
        campaign_id = str(uuid.uuid4())
        
        # Initialize database
        init_db()
        
        # Store campaign
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO campaigns (id, name, message_template, total_contacts, rate_limit, status, started_at)
            VALUES (?, ?, ?, ?, ?, 'running', ?)
        ''', (campaign_id, campaign_name, message_template, len(df), rate_limit, datetime.now().isoformat()))
        
        # Store messages
        for _, row in df.iterrows():
            # Personalize message
            personalized_message = message_template
            for column in df.columns:
                if pd.notna(row[column]):
                    personalized_message = personalized_message.replace(f'{{{column}}}', str(row[column]))
            
            cursor.execute('''
                INSERT INTO messages (campaign_id, phone_number, name, message_content, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (campaign_id, str(row['phone']), str(row['name']), personalized_message))
        
        conn.commit()
        conn.close()
        
        # Clean up uploaded file
        os.remove(file_path)
        
        # Start sending messages asynchronously (simplified version)
        print(f"Campaign {campaign_id} created with {len(df)} contacts")
        
        return jsonify({
            'message': 'Campaign started successfully!',
            'campaign_id': campaign_id,
            'total_contacts': len(df)
        })
        
    except Exception as e:
        print(f"Error starting campaign: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'WhatsApp Bulk Sender API is running'})

if __name__ == '__main__':
    init_db()
    print("🚀 Starting simplified WhatsApp Bulk Sender API...")
    print("✅ Health check: http://localhost:5000/health")
    print("📊 Campaigns API: http://localhost:5000/api/campaigns")
    app.run(debug=True, port=5000)
