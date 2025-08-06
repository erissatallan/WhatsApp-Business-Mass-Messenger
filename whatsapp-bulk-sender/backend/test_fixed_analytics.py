import sqlite3

def test_fixed_analytics():
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        print("=== Testing Fixed Analytics Logic ===")
        
        # Simulate the fixed analytics endpoint logic
        campaign_id = None  # Test overall analytics (no campaign filter)
        
        where_clause = "WHERE campaign_id = ?" if campaign_id else ""
        params = [campaign_id] if campaign_id else []
        
        # Get sentiment breakdown
        cursor.execute(f"""
            SELECT sentiment, COUNT(*) as count
            FROM replies {where_clause}
            GROUP BY sentiment
        """, params)
        
        sentiment_data = dict(cursor.fetchall())
        print(f"Raw sentiment data: {sentiment_data}")
        
        # Combine positive sentiments for frontend compatibility
        positive_count = sentiment_data.get('positive', 0) + sentiment_data.get('positive_feedback', 0)
        if positive_count > 0:
            sentiment_data['positive'] = positive_count
        
        print(f"Fixed sentiment data: {sentiment_data}")
        
        # Get reply rate (fixed logic)
        if campaign_id:
            cursor.execute("SELECT total_contacts FROM campaigns WHERE id = ?", (campaign_id,))
            total_sent = cursor.fetchone()
            total_sent = total_sent[0] if total_sent else 0
            
            cursor.execute("SELECT COUNT(DISTINCT phone_number) FROM replies WHERE campaign_id = ?", (campaign_id,))
            total_replies = cursor.fetchone()[0]
            
            reply_rate = (total_replies / total_sent * 100) if total_sent > 0 else 0
        else:
            # Calculate overall reply rate across all campaigns
            cursor.execute("SELECT SUM(total_contacts) FROM campaigns")
            total_sent = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(DISTINCT phone_number) FROM replies")
            total_replies = cursor.fetchone()[0]
            
            reply_rate = (total_replies / total_sent * 100) if total_sent > 0 else 0
        
        print(f"Reply rate calculation: {total_replies} unique replies / {total_sent} total contacts = {reply_rate:.2f}%")
        
        # Get opt-out count
        if campaign_id:
            cursor.execute("SELECT COUNT(*) FROM replies WHERE campaign_id = ? AND is_opt_out = 1", (campaign_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM replies WHERE is_opt_out = 1")
        
        opt_outs = cursor.fetchone()[0]
        print(f"Opt-outs: {opt_outs}")
        
        # Get recent replies
        if campaign_id:
            cursor.execute("SELECT COUNT(*) FROM replies WHERE campaign_id = ? AND received_at >= datetime('now', '-24 hours')", (campaign_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM replies WHERE received_at >= datetime('now', '-24 hours')")
        
        recent_replies = cursor.fetchone()[0]
        print(f"Recent replies (24h): {recent_replies}")
        
        # Final analytics object
        analytics = {
            'sentiment_breakdown': sentiment_data,
            'reply_rate': round(reply_rate, 2),
            'total_opt_outs': opt_outs,
            'recent_replies_24h': recent_replies
        }
        
        print(f"\nFinal analytics object: {analytics}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fixed_analytics()
