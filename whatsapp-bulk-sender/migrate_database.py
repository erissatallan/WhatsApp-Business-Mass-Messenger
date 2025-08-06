#!/usr/bin/env python3
"""
Database migration script to fix the replies table structure
"""

import sqlite3
import os

def migrate_database():
    """Fix the database structure to match expected schema"""
    try:
        # Backup the database first
        if os.path.exists('backend/whatsapp_campaigns.db'):
            import shutil
            shutil.copy('backend/whatsapp_campaigns.db', 'backend/whatsapp_campaigns_backup.db')
            print("✅ Database backed up to whatsapp_campaigns_backup.db")
        
        conn = sqlite3.connect('backend/whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Check current structure
        cursor.execute("PRAGMA table_info(replies)")
        current_columns = {col[1]: col for col in cursor.fetchall()}
        
        print("📊 Current database structure:")
        for i, (name, col) in enumerate(current_columns.items()):
            print(f"  {i}: {name}")
        
        # Check if we have the correct structure
        expected_order = [
            'id', 'phone_number', 'sender_name', 'message_content', 'received_at',
            'campaign_id', 'original_message_id', 'reply_type', 'media_url', 'media_type',
            'sentiment', 'confidence_score', 'is_opt_out', 'requires_attention', 'created_at'
        ]
        
        # Add missing columns if they don't exist
        if 'confidence_score' not in current_columns:
            print("⚠️ Adding missing confidence_score column...")
            cursor.execute("ALTER TABLE replies ADD COLUMN confidence_score REAL DEFAULT 0.0")
        
        if 'requires_attention' not in current_columns:
            print("⚠️ Adding missing requires_attention column...")
            cursor.execute("ALTER TABLE replies ADD COLUMN requires_attention BOOLEAN DEFAULT FALSE")
        
        # Since SQLite doesn't support reordering columns easily, let's create a new table
        # with the correct structure and migrate data
        
        print("🔄 Creating new table with correct structure...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS replies_new (
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
                confidence_score REAL DEFAULT 0.0,
                is_opt_out BOOLEAN DEFAULT FALSE,
                requires_attention BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Migrate data from old table to new table
        print("📋 Migrating data...")
        cursor.execute('''
            INSERT INTO replies_new (
                id, phone_number, sender_name, message_content, received_at,
                campaign_id, original_message_id, reply_type, media_url, media_type,
                sentiment, confidence_score, is_opt_out, requires_attention, created_at
            )
            SELECT 
                id, phone_number, sender_name, message_content, received_at,
                campaign_id, original_message_id, reply_type, media_url, media_type,
                sentiment,
                CASE WHEN typeof(confidence_score) = 'real' THEN confidence_score ELSE 0.0 END,
                CASE WHEN is_opt_out = 1 OR is_opt_out = 'true' THEN 1 ELSE 0 END,
                CASE WHEN typeof(requires_attention) = 'integer' THEN requires_attention ELSE 0 END,
                COALESCE(created_at, received_at)
            FROM replies
        ''')
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE replies")
        cursor.execute("ALTER TABLE replies_new RENAME TO replies")
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_replies_phone ON replies(phone_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_replies_received_at ON replies(received_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_replies_sentiment ON replies(sentiment)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_replies_opt_out ON replies(is_opt_out)")
        
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed successfully!")
        
        # Verify the new structure
        conn = sqlite3.connect('backend/whatsapp_campaigns.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(replies)")
        new_columns = cursor.fetchall()
        
        print("\n📊 New database structure:")
        for i, col in enumerate(new_columns):
            print(f"  {i:2d}: {col[1]:20s} {col[2]:10s}")
        
        # Show sample data
        cursor.execute("SELECT id, phone_number, sentiment, confidence_score, is_opt_out, requires_attention FROM replies LIMIT 3")
        sample_rows = cursor.fetchall()
        
        print(f"\n📋 Sample data ({len(sample_rows)} rows):")
        for row in sample_rows:
            print(f"  ID: {row[0]}, Phone: {row[1]}, Sentiment: {row[2]}, Confidence: {row[3]}, Opt-out: {row[4]}, Attention: {row[5]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Database Migration Tool")
    print("=" * 50)
    
    if migrate_database():
        print("\n🎉 Migration completed! The opt-out display issue should now be fixed.")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
