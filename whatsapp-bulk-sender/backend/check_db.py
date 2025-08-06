import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        # Check campaigns
        try:
            cursor.execute('SELECT COUNT(*) FROM campaigns')
            campaigns_count = cursor.fetchone()[0]
            print(f'Campaigns count: {campaigns_count}')
            
            if campaigns_count > 0:
                cursor.execute('SELECT id, name, status, total_contacts FROM campaigns LIMIT 5')
                campaigns = cursor.fetchall()
                print(f'Sample campaigns: {campaigns}')
        except Exception as e:
            print(f'Campaigns table error: {e}')
        
        # Check messages  
        try:
            cursor.execute('SELECT COUNT(*) FROM messages')
            messages_count = cursor.fetchone()[0]
            print(f'Messages count: {messages_count}')
            
            if messages_count > 0:
                cursor.execute('SELECT status, COUNT(*) FROM messages GROUP BY status')
                status_counts = cursor.fetchall()
                print(f'Message status counts: {status_counts}')
        except Exception as e:
            print(f'Messages table error: {e}')
        
        # Check replies
        try:
            cursor.execute('SELECT COUNT(*) FROM replies')
            replies_count = cursor.fetchone()[0]
            print(f'Replies count: {replies_count}')
            
            if replies_count > 0:
                cursor.execute('SELECT sentiment, COUNT(*) FROM replies GROUP BY sentiment')
                sentiment_counts = cursor.fetchall()
                print(f'Reply sentiment counts: {sentiment_counts}')
        except Exception as e:
            print(f'Replies table error: {e}')
        
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_database()
