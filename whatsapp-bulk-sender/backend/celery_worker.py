# celery_worker.py - Celery Worker Configuration
from celery import Celery
import sqlite3
import time
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

# Create Celery instance
celery_app = Celery('whatsapp_sender')
celery_app.config_from_object({
    'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6380/0'),
    'result_backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6380/0'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'worker_prefetch_multiplier': 1,  # Process one task at a time
    'task_acks_late': True,  # Acknowledge task after completion
    'worker_disable_rate_limits': False,
    # Windows-specific settings
    'worker_pool': 'solo',  # Use solo pool for Windows
    'broker_connection_retry_on_startup': True,
})

@celery_app.task(bind=True, max_retries=3)
def process_campaign_task(self, campaign_id, api_key, rate_limit):
    """Process campaign messages with rate limiting and retry logic"""
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    try:
        # Update campaign status to running
        cursor.execute('''
            UPDATE campaigns 
            SET status = 'running', started_at = ?
            WHERE id = ?
        ''', (datetime.now(), campaign_id))
        conn.commit()
        
        # Get pending messages
        cursor.execute('''
            SELECT id, phone_number, message_content, name
            FROM messages 
            WHERE campaign_id = ? AND status = 'pending'
            ORDER BY id
        ''', (campaign_id,))
        
        messages = cursor.fetchall()
        total_messages = len(messages)
        processed = 0
        
        print(f"Processing {total_messages} messages for campaign {campaign_id}")
        
        for message_id, phone, content, name in messages:
            try:
                # Send WhatsApp message
                success, error_msg = send_whatsapp_message(phone, content, api_key)
                
                if success:
                    cursor.execute('''
                        UPDATE messages 
                        SET status = 'sent', sent_at = ?
                        WHERE id = ?
                    ''', (datetime.now(), message_id))
                    print(f"✓ Message sent to {phone} ({name})")
                else:
                    cursor.execute('''
                        UPDATE messages 
                        SET status = 'failed', failed_at = ?, error_message = ?
                        WHERE id = ?
                    ''', (datetime.now(), error_msg, message_id))
                    print(f"✗ Failed to send to {phone} ({name}): {error_msg}")
                
                conn.commit()
                processed += 1
                
                # Update progress
                if processed % 10 == 0:  # Update every 10 messages
                    print(f"Progress: {processed}/{total_messages} messages processed")
                
                # Rate limiting - wait between messages
                time.sleep(rate_limit)
                
            except Exception as e:
                error_msg = str(e)
                cursor.execute('''
                    UPDATE messages 
                    SET status = 'failed', failed_at = ?, error_message = ?
                    WHERE id = ?
                ''', (datetime.now(), error_msg, message_id))
                conn.commit()
                print(f"✗ Exception sending to {phone}: {error_msg}")
        
        # Update campaign to completed
        cursor.execute('''
            UPDATE campaigns 
            SET status = 'completed', completed_at = ?
            WHERE id = ?
        ''', (datetime.now(), campaign_id))
        conn.commit()
        
        print(f"Campaign {campaign_id} completed. Processed {processed}/{total_messages} messages")
        
    except Exception as e:
        print(f"Campaign {campaign_id} failed: {str(e)}")
        cursor.execute('''
            UPDATE campaigns 
            SET status = 'failed'
            WHERE id = ?
        ''', (campaign_id,))
        conn.commit()
        
        # Retry the task if retries are available
        if self.request.retries < self.max_retries:
            print(f"Retrying campaign {campaign_id} in 60 seconds...")
            raise self.retry(countdown=60, exc=e)
        
    finally:
        conn.close()

@celery_app.task(bind=True, max_retries=5)
def send_single_message_task(self, message_id, phone, content, api_key):
    """Send a single WhatsApp message with retry logic"""
    try:
        success, error_msg = send_whatsapp_message(phone, content, api_key)
        
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        if success:
            cursor.execute('''
                UPDATE messages 
                SET status = 'sent', sent_at = ?
                WHERE id = ?
            ''', (datetime.now(), message_id))
        else:
            # If API rate limited, retry with exponential backoff
            if "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                cursor.execute('''
                    UPDATE messages 
                    SET retry_count = retry_count + 1
                    WHERE id = ?
                ''', (message_id,))
                
                if self.request.retries < self.max_retries:
                    # Exponential backoff: 2^retry_count * 60 seconds
                    countdown = (2 ** self.request.retries) * 60
                    print(f"Rate limited. Retrying message {message_id} in {countdown} seconds")
                    raise self.retry(countdown=countdown)
            
            cursor.execute('''
                UPDATE messages 
                SET status = 'failed', failed_at = ?, error_message = ?
                WHERE id = ?
            ''', (datetime.now(), error_msg, message_id))
        
        conn.commit()
        conn.close()
        
        return success
        
    except Exception as e:
        if self.request.retries < self.max_retries:
            print(f"Exception in send_single_message_task: {str(e)}. Retrying...")
            raise self.retry(countdown=60, exc=e)
        else:
            # Final failure
            conn = sqlite3.connect('whatsapp_campaigns.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE messages 
                SET status = 'failed', failed_at = ?, error_message = ?
                WHERE id = ?
            ''', (datetime.now(), str(e), message_id))
            conn.commit()
            conn.close()
            return False

def send_whatsapp_message(phone, message, api_key):
    """Send WhatsApp message via Twilio (temporary) or Business API (future)"""
    
    # OPTION 1: TWILIO WhatsApp API (ACTIVE - for testing without WABA approval)
    try:
        # Initialize Twilio client
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_from = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
        
        if not account_sid or not auth_token:
            return False, "Twilio credentials not configured in .env file"
        
        client = Client(account_sid, auth_token)
        
        # Format phone number for WhatsApp
        if not phone.startswith('whatsapp:'):
            if not phone.startswith('+'):
                phone = '+' + phone
            to_number = f'whatsapp:{phone}'
        else:
            to_number = phone
        
        # Send message via Twilio
        twilio_message = client.messages.create(
            body=message,
            from_=twilio_from,
            to=to_number
        )
        
        print(f"✅ Twilio message sent successfully. SID: {twilio_message.sid}")
        return True, f"Success - Twilio SID: {twilio_message.sid}"
        
    except Exception as e:
        error_msg = f"Twilio error: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg
    
    # OPTION 2: WhatsApp Business API (COMMENTED OUT - activate when WABA is approved)
    """
    # WhatsApp Business API endpoint (replace YOUR_PHONE_NUMBER_ID with actual ID)
    # You'll get this from your WhatsApp Business API setup
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', 'YOUR_PHONE_NUMBER_ID')
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return True, "Success"
        elif response.status_code == 429:
            return False, "Rate limit exceeded"
        elif response.status_code == 401:
            return False, "Invalid API key"
        elif response.status_code == 400:
            response_data = response.json()
            error_msg = response_data.get('error', {}).get('message', 'Bad request')
            return False, f"Bad request: {error_msg}"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
    """

if __name__ == '__main__':
    # Run worker with: celery -A celery_worker worker --loglevel=info
    celery_app.start()
