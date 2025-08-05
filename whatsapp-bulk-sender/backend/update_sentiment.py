#!/usr/bin/env python3
"""
Utility script to update sentiment analysis for existing replies using Gemini AI
Run this after implementing the new Gemini-powered sentiment detection
"""

import sqlite3
import sys
import os

# Add the backend directory to the path to import reply_handler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reply_handler import detect_reply_sentiment

def update_all_sentiments():
    """Update sentiment for all existing replies using the new Gemini AI algorithm"""
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # First, check if new columns exist, if not add them
        cursor.execute("PRAGMA table_info(replies)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'confidence_score' not in columns:
            print("Adding confidence_score column...")
            cursor.execute("ALTER TABLE replies ADD COLUMN confidence_score REAL DEFAULT 0.8")
        
        if 'requires_attention' not in columns:
            print("Adding requires_attention column...")
            cursor.execute("ALTER TABLE replies ADD COLUMN requires_attention BOOLEAN DEFAULT FALSE")
        
        # Get all replies
        cursor.execute("SELECT id, message_content, sentiment FROM replies")
        replies = cursor.fetchall()
        
        if not replies:
            print("No replies found in database.")
            return
        
        print(f"Found {len(replies)} replies to analyze with Gemini AI...")
        
        updated_count = 0
        sentiment_changes = {
            'positive': 0,
            'negative': 0,
            'question': 0,
            'neutral': 0
        }
        attention_count = 0
        
        for reply_id, message_content, old_sentiment in replies:
            # Detect new sentiment using Gemini AI
            sentiment_result = detect_reply_sentiment(message_content)
            new_sentiment = sentiment_result['sentiment']
            confidence = sentiment_result['confidence']
            requires_attention = sentiment_result['requires_attention']
            detailed_category = sentiment_result.get('detailed_category', 'UNKNOWN')
            
            if requires_attention:
                attention_count += 1
            
            # Update the sentiment and new fields in database
            cursor.execute(
                """UPDATE replies 
                   SET sentiment = ?, confidence_score = ?, requires_attention = ? 
                   WHERE id = ?""",
                (new_sentiment, confidence, requires_attention, reply_id)
            )
            updated_count += 1
            sentiment_changes[new_sentiment] += 1
            
            status_icon = "🚨" if requires_attention else "✅"
            confidence_icon = "🎯" if confidence > 0.8 else "📊"
            
            print(f"{status_icon} Reply ID {reply_id}: '{message_content[:40]}...'")
            print(f"   {confidence_icon} {old_sentiment} → {new_sentiment} ({detailed_category}) - Confidence: {confidence:.2f}")
            if requires_attention:
                print(f"   ⚠️ Flagged for human attention")
            print()
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Gemini AI Analysis Complete!")
        print(f"📊 Updated {updated_count} out of {len(replies)} replies")
        print(f"🚨 {attention_count} replies flagged for human attention")
        print(f"📈 New sentiment distribution:")
        print(f"   😊 Positive: {sentiment_changes['positive']}")
        print(f"   😞 Negative: {sentiment_changes['negative']}")
        print(f"   ❓ Questions: {sentiment_changes['question']}")
        print(f"   😐 Neutral: {sentiment_changes['neutral']}")
        
    except Exception as e:
        print(f"❌ Error updating sentiments: {str(e)}")
        import traceback
        traceback.print_exc()

def show_current_sentiment_stats():
    """Show current sentiment statistics"""
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Check if new columns exist
        cursor.execute("PRAGMA table_info(replies)")
        columns = [column[1] for column in cursor.fetchall()]
        
        cursor.execute("""
            SELECT sentiment, COUNT(*) as count
            FROM replies
            GROUP BY sentiment
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
        print("📊 Current sentiment distribution:")
        for sentiment, count in results:
            emoji = {'positive': '😊', 'negative': '😞', 'question': '❓', 'neutral': '😐'}.get(sentiment, '❓')
            print(f"   {emoji} {sentiment.title()}: {count}")
        
        # Show attention stats if column exists
        if 'requires_attention' in columns:
            cursor.execute("SELECT COUNT(*) FROM replies WHERE requires_attention = 1")
            attention_count = cursor.fetchone()[0]
            print(f"🚨 Replies requiring attention: {attention_count}")
        
        # Show confidence stats if column exists  
        if 'confidence_score' in columns:
            cursor.execute("SELECT AVG(confidence_score) FROM replies WHERE confidence_score > 0")
            avg_confidence = cursor.fetchone()[0]
            if avg_confidence:
                print(f"🎯 Average confidence score: {avg_confidence:.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")

if __name__ == "__main__":
    print("🤖 WhatsApp Reply Sentiment Updater (Gemini AI)\n")
    
    print("Current sentiment statistics:")
    show_current_sentiment_stats()
    
    print("\nUpdating sentiments with Gemini AI...")
    update_all_sentiments()
    
    print("\nUpdated sentiment statistics:")
    show_current_sentiment_stats()
