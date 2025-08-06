import sqlite3

def debug_campaign_ids():
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        print("=== Debugging Campaign ID Relationships ===")
        
        # Check campaign IDs
        print("\n1. Campaign IDs:")
        cursor.execute("SELECT id, name FROM campaigns")
        campaigns = cursor.fetchall()
        for campaign in campaigns:
            print(f"  Campaign: {campaign[1]} -> ID: {campaign[0]}")
        
        # Check reply campaign IDs
        print("\n2. Reply campaign IDs:")
        cursor.execute("SELECT DISTINCT campaign_id FROM replies")
        reply_campaigns = cursor.fetchall()
        for reply_campaign in reply_campaigns:
            print(f"  Reply campaign_id: {reply_campaign[0]}")
        
        # Check if there's a mismatch
        print("\n3. Checking for matches:")
        cursor.execute("SELECT campaign_id, COUNT(*) FROM replies GROUP BY campaign_id")
        reply_counts = cursor.fetchall()
        for reply_count in reply_counts:
            campaign_id = reply_count[0]
            count = reply_count[1]
            
            cursor.execute("SELECT name FROM campaigns WHERE id = ?", (campaign_id,))
            campaign_name = cursor.fetchone()
            
            if campaign_name:
                print(f"  ✅ Campaign '{campaign_name[0]}' ({campaign_id}) has {count} replies")
            else:
                print(f"  ❌ Orphaned replies: campaign_id '{campaign_id}' has {count} replies but no matching campaign")
        
        # Check the schema
        print("\n4. Table schemas:")
        cursor.execute("PRAGMA table_info(campaigns)")
        campaigns_schema = cursor.fetchall()
        print("  Campaigns table:")
        for col in campaigns_schema:
            print(f"    {col[1]} ({col[2]})")
        
        cursor.execute("PRAGMA table_info(replies)")
        replies_schema = cursor.fetchall()
        print("  Replies table:")
        for col in replies_schema:
            print(f"    {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_campaign_ids()
