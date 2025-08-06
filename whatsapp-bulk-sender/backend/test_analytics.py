import sqlite3

def test_analytics():
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        print("=== Testing Analytics Queries ===")
        
        # Test 1: Overall analytics (no campaign filter)
        print("\n1. Overall sentiment breakdown:")
        cursor.execute("SELECT sentiment, COUNT(*) as count FROM replies GROUP BY sentiment")
        sentiment_data = dict(cursor.fetchall())
        print(f"Sentiment data: {sentiment_data}")
        
        # Test 2: Reply rate calculation for overall
        print("\n2. Overall reply rate:")
        cursor.execute("SELECT SUM(total_contacts) FROM campaigns")
        total_sent = cursor.fetchone()[0] or 0
        print(f"Total contacts sent to: {total_sent}")
        
        cursor.execute("SELECT COUNT(DISTINCT phone_number) FROM replies")
        total_replies = cursor.fetchone()[0]
        print(f"Total unique replies: {total_replies}")
        
        reply_rate = (total_replies / total_sent * 100) if total_sent > 0 else 0
        print(f"Calculated reply rate: {reply_rate}%")
        
        # Test 3: Opt-outs
        print("\n3. Opt-outs:")
        cursor.execute("SELECT COUNT(*) FROM replies WHERE is_opt_out = 1")
        opt_outs = cursor.fetchone()[0]
        print(f"Total opt-outs: {opt_outs}")
        
        # Test 4: Recent replies (24h)
        print("\n4. Recent replies (24h):")
        cursor.execute("SELECT COUNT(*) FROM replies WHERE received_at >= datetime('now', '-24 hours')")
        recent_replies = cursor.fetchone()[0]
        print(f"Recent replies: {recent_replies}")
        
        # Test 5: Check received_at format
        print("\n5. Sample received_at values:")
        cursor.execute("SELECT received_at FROM replies LIMIT 5")
        dates = cursor.fetchall()
        print(f"Sample dates: {dates}")
        
        # Test 6: Check campaign analytics for specific campaign
        print("\n6. Campaign-specific analytics:")
        cursor.execute("SELECT id, name FROM campaigns LIMIT 1")
        campaign = cursor.fetchone()
        if campaign:
            campaign_id = campaign[0]
            print(f"Testing campaign: {campaign[1]} (ID: {campaign_id})")
            
            cursor.execute("SELECT sentiment, COUNT(*) FROM replies WHERE campaign_id = ? GROUP BY sentiment", (campaign_id,))
            campaign_sentiment = dict(cursor.fetchall())
            print(f"Campaign sentiment: {campaign_sentiment}")
            
            cursor.execute("SELECT total_contacts FROM campaigns WHERE id = ?", (campaign_id,))
            campaign_total = cursor.fetchone()[0]
            print(f"Campaign total contacts: {campaign_total}")
            
            cursor.execute("SELECT COUNT(DISTINCT phone_number) FROM replies WHERE campaign_id = ?", (campaign_id,))
            campaign_replies = cursor.fetchone()[0]
            print(f"Campaign unique replies: {campaign_replies}")
            
            campaign_rate = (campaign_replies / campaign_total * 100) if campaign_total > 0 else 0
            print(f"Campaign reply rate: {campaign_rate}%")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_analytics()
