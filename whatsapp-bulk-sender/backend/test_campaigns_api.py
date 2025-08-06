import sqlite3

def test_campaigns_api():
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        print("=== Testing Campaigns API Logic ===")
        
        # First, check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Available tables: {tables}")
        
        if 'campaigns' not in tables:
            print("❌ Campaigns table not found!")
            return
        
        # Test the campaigns query
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
        print("\nCampaign details:")
        for row in cursor.fetchall():
            campaign = {
                'id': row[0],
                'name': row[1],
                'status': row[5],
                'total_contacts': row[3],
                'created_at': row[6],
                'total_messages': row[7] or 0,
                'sent_messages': row[8] or 0,
                'delivered_messages': row[9] or 0,
                'failed_messages': row[10] or 0
            }
            campaigns.append(campaign)
            print(f"  Campaign: {campaign['name']}")
            print(f"    Status: {campaign['status']}")
            print(f"    Total contacts: {campaign['total_contacts']}")
            print(f"    Messages - Total: {campaign['total_messages']}, Sent: {campaign['sent_messages']}, Delivered: {campaign['delivered_messages']}, Failed: {campaign['failed_messages']}")
            print()
        
        print(f"Total campaigns returned: {len(campaigns)}")
        
        # Also check messages table separately
        print("\n=== Messages Table Check ===")
        cursor.execute("SELECT campaign_id, status, COUNT(*) FROM messages GROUP BY campaign_id, status")
        message_stats = cursor.fetchall()
        print("Message statistics by campaign and status:")
        for stat in message_stats:
            print(f"  Campaign {stat[0]}: {stat[1]} = {stat[2]} messages")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_campaigns_api()
