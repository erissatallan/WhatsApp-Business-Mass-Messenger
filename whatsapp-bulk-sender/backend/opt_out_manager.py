#!/usr/bin/env python3
"""
Opt-out Management System for WhatsApp Business Compliance
Handles opt-out confirmations, scheduling, and contact list management
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


def setup_opt_out_tables():
    """Create database tables for opt-out management"""
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    # Opt-out queue for scheduled confirmations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opt_out_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            sender_name TEXT,
            message TEXT,
            scheduled_time TIMESTAMP,
            sent BOOLEAN DEFAULT FALSE,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Master opt-out list
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opt_out_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            sender_name TEXT,
            opted_out_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            source TEXT DEFAULT 'reply'
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_optout_queue_scheduled ON opt_out_queue(scheduled_time, sent)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_optout_list_phone ON opt_out_list(phone_number)')
    
    conn.commit()
    conn.close()


def get_pending_opt_out_confirmations() -> List[Dict]:
    """Get all pending opt-out confirmations ready to be sent"""
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    # Get confirmations that are scheduled and not yet sent
    cursor.execute('''
        SELECT id, phone_number, sender_name, message, scheduled_time, created_at
        FROM opt_out_queue 
        WHERE sent = FALSE AND scheduled_time <= ?
        ORDER BY scheduled_time ASC
    ''', (datetime.now().isoformat(),))
    
    confirmations = []
    for row in cursor.fetchall():
        confirmations.append({
            'id': row[0],
            'phone_number': row[1],
            'sender_name': row[2],
            'message': row[3],
            'scheduled_time': row[4],
            'created_at': row[5]
        })
    
    conn.close()
    return confirmations


def mark_opt_out_confirmation_sent(confirmation_id: int) -> bool:
    """Mark an opt-out confirmation as sent"""
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE opt_out_queue 
            SET sent = TRUE, sent_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), confirmation_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error marking confirmation as sent: {e}")
        return False


def get_opt_out_analytics() -> Dict:
    """Get analytics about opt-outs"""
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    # Total opt-outs
    cursor.execute('SELECT COUNT(*) FROM opt_out_list')
    total_opt_outs = cursor.fetchone()[0]
    
    # Opt-outs in last 24 hours
    cursor.execute('''
        SELECT COUNT(*) FROM opt_out_list 
        WHERE opted_out_at >= datetime('now', '-24 hours')
    ''')
    recent_opt_outs = cursor.fetchone()[0]
    
    # Pending confirmations
    cursor.execute('SELECT COUNT(*) FROM opt_out_queue WHERE sent = FALSE')
    pending_confirmations = cursor.fetchone()[0]
    
    # Opt-out rate per campaign
    cursor.execute('''
        SELECT c.name, COUNT(DISTINCT r.phone_number) as opt_outs,
               c.total_contacts,
               ROUND(COUNT(DISTINCT r.phone_number) * 100.0 / c.total_contacts, 2) as opt_out_rate
        FROM campaigns c
        LEFT JOIN replies r ON c.id = r.campaign_id AND r.is_opt_out = TRUE
        WHERE c.total_contacts > 0
        GROUP BY c.id, c.name, c.total_contacts
        ORDER BY opt_out_rate DESC
    ''')
    
    campaign_rates = []
    for row in cursor.fetchall():
        campaign_rates.append({
            'campaign': row[0],
            'opt_outs': row[1],
            'total_contacts': row[2],
            'opt_out_rate': row[3]
        })
    
    conn.close()
    
    return {
        'total_opt_outs': total_opt_outs,
        'recent_opt_outs_24h': recent_opt_outs,
        'pending_confirmations': pending_confirmations,
        'campaign_opt_out_rates': campaign_rates
    }


def is_phone_opted_out(phone_number: str) -> bool:
    """Check if a phone number has opted out"""
    from reply_handler import get_phone_number_variations
    
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    # Check all variations of the phone number
    variations = get_phone_number_variations(phone_number)
    
    for variation in variations:
        cursor.execute('SELECT id FROM opt_out_list WHERE phone_number = ?', (variation,))
        if cursor.fetchone():
            conn.close()
            return True
    
    conn.close()
    return False


def remove_opted_out_contacts_from_campaign(campaign_id: int) -> int:
    """Remove opted-out contacts from a campaign and return count removed"""
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    # Get all opt-out phone numbers
    cursor.execute('SELECT phone_number FROM opt_out_list')
    opted_out_numbers = [row[0] for row in cursor.fetchall()]
    
    removed_count = 0
    
    # Remove messages for opted-out numbers from the campaign
    for phone_number in opted_out_numbers:
        from reply_handler import get_phone_number_variations
        variations = get_phone_number_variations(phone_number)
        
        for variation in variations:
            cursor.execute('''
                DELETE FROM messages 
                WHERE campaign_id = ? AND phone_number = ?
            ''', (campaign_id, variation))
            removed_count += cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return removed_count


def schedule_opt_out_confirmation_message(phone_number: str, sender_name: str = "", 
                                        schedule_type: str = "now", hours_delay: int = 0) -> bool:
    """Schedule an opt-out confirmation message"""
    try:
        setup_opt_out_tables()
        
        # Generate compliant opt-out message
        from reply_handler import get_compliant_opt_out_message
        message = get_compliant_opt_out_message(sender_name)
        
        # Calculate scheduled time
        if schedule_type == "now":
            scheduled_time = datetime.now()
        elif schedule_type == "after_hours":
            scheduled_time = datetime.now() + timedelta(hours=hours_delay)
        else:
            scheduled_time = datetime.now()  # Default to now
        
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO opt_out_queue (phone_number, sender_name, message, scheduled_time)
            VALUES (?, ?, ?, ?)
        ''', (phone_number, sender_name, message, scheduled_time.isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"📅 Opt-out confirmation scheduled for {phone_number} at {scheduled_time}")
        return True
        
    except Exception as e:
        print(f"❌ Error scheduling opt-out confirmation: {e}")
        return False


def get_opt_out_queue_status() -> List[Dict]:
    """Get status of all items in opt-out queue"""
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, phone_number, sender_name, scheduled_time, sent, sent_at, created_at
        FROM opt_out_queue
        ORDER BY created_at DESC
    ''')
    
    queue_items = []
    for row in cursor.fetchall():
        queue_items.append({
            'id': row[0],
            'phone_number': row[1],
            'sender_name': row[2],
            'scheduled_time': row[3],
            'sent': bool(row[4]),
            'sent_at': row[5],
            'created_at': row[6],
            'status': 'Sent' if row[4] else 'Pending'
        })
    
    conn.close()
    return queue_items


if __name__ == "__main__":
    print("🔧 Setting up Opt-out Management System...")
    setup_opt_out_tables()
    print("✅ Opt-out tables created successfully!")
    
    # Show analytics
    analytics = get_opt_out_analytics()
    print(f"\n📊 Current Opt-out Status:")
    print(f"   Total opt-outs: {analytics['total_opt_outs']}")
    print(f"   Recent (24h): {analytics['recent_opt_outs_24h']}")
    print(f"   Pending confirmations: {analytics['pending_confirmations']}")
