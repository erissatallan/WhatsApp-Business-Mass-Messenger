#!/usr/bin/env python3
"""
Test script to check database structure and fix opt-out display issues
"""

import sqlite3
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def check_database_structure():
    """Check the current database structure"""
    try:
        conn = sqlite3.connect('backend/whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute("PRAGMA table_info(replies)")
        columns = cursor.fetchall()
        
        print("📊 Database Structure - replies table:")
        print("-" * 50)
        for i, col in enumerate(columns):
            print(f"{i:2d}: {col[1]:20s} {col[2]:10s} {'NOT NULL' if col[3] else ''}")
        
        # Check some sample data
        cursor.execute("SELECT * FROM replies ORDER BY received_at DESC LIMIT 3")
        rows = cursor.fetchall()
        
        print(f"\n📋 Sample Data ({len(rows)} rows):")
        print("-" * 50)
        for row in rows:
            print(f"ID: {row[0]}, Phone: {row[1]}, Message: {row[3][:30]}...")
            print(f"    Sentiment: {row[10]}, Confidence: {row[11]}, Opt-out: {row[12]}, Attention: {row[13]}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")

def test_ai_detection():
    """Test the enhanced AI detection"""
    try:
        from backend.reply_handler import detect_reply_sentiment_gemini
        
        test_messages = [
            "Ami soksin",  # Dholuo - "Can I get socks"
            "Anyalo yudo sokisi",  # Dholuo - "Can I get socks"
            "Nĩngĩheo sokisi",  # Gikuyu - "Can I get socks"
            "I need to know the prices",  # English question without ?
            "stop",  # Opt-out
            "Thank you very much!",  # Positive feedback
        ]
        
        print("🤖 Testing Enhanced AI Detection:")
        print("-" * 50)
        
        for message in test_messages:
            result = detect_reply_sentiment_gemini(message)
            print(f"Message: '{message}'")
            print(f"Result: {result['sentiment']} (confidence: {result['confidence']:.2f})")
            print(f"Attention: {result.get('requires_attention', False)}")
            print()
            
    except Exception as e:
        print(f"❌ Error testing AI detection: {str(e)}")

if __name__ == "__main__":
    print("🔍 Testing WhatsApp System Improvements")
    print("=" * 60)
    
    check_database_structure()
    print()
    test_ai_detection()
