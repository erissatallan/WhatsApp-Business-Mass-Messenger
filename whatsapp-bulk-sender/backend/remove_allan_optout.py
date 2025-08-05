#!/usr/bin/env python3
"""
Remove Allan Erissat from opt-out list to resume testing
"""

import sqlite3
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from reply_handler import get_phone_number_variations
    
    # Connect to database
    conn = sqlite3.connect('whatsapp_campaigns.db')
    cursor = conn.cursor()
    
    # Allan's phone number
    phone_number = '0759469851'
    
    # Get all variations of the phone number
    variations = get_phone_number_variations(phone_number)
    print(f"Phone variations to remove: {variations}")
    
    # Remove from opt-out list
    removed_count = 0
    for variation in variations:
        cursor.execute('DELETE FROM opt_out_list WHERE phone_number = ?', (variation,))
        if cursor.rowcount > 0:
            removed_count += cursor.rowcount
            print(f"✅ Removed {variation} from opt-out list")
    
    # Update any replies marked as opt-out
    for variation in variations:
        cursor.execute('UPDATE replies SET is_opt_out = FALSE WHERE phone_number = ?', (variation,))
    
    updated_replies = cursor.rowcount
    
    # Remove from opt-out queue if present
    for variation in variations:
        cursor.execute('DELETE FROM opt_out_queue WHERE phone_number = ?', (variation,))
    
    removed_queue = cursor.rowcount
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Allan Erissat restoration completed:")
    print(f"   📞 Phone: {phone_number}")
    print(f"   🗑️ Removed {removed_count} opt-out entries")
    print(f"   📝 Updated {updated_replies} reply records")
    print(f"   📋 Removed {removed_queue} queue items")
    print(f"\n✅ Allan can now receive WhatsApp messages again!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Trying basic removal...")
    
    # Fallback approach
    try:
        conn = sqlite3.connect('whatsapp_campaigns.db')
        cursor = conn.cursor()
        
        # Remove any entries containing Allan's number
        cursor.execute('DELETE FROM opt_out_list WHERE phone_number LIKE ?', ('%759469851%',))
        removed1 = cursor.rowcount
        
        cursor.execute('UPDATE replies SET is_opt_out = FALSE WHERE phone_number LIKE ?', ('%759469851%',))
        updated = cursor.rowcount
        
        cursor.execute('DELETE FROM opt_out_queue WHERE phone_number LIKE ?', ('%759469851%',))
        removed2 = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Fallback removal completed:")
        print(f"   - Removed {removed1} opt-out entries")
        print(f"   - Updated {updated} replies")
        print(f"   - Removed {removed2} queue items")
        print(f"\n🎉 Allan Erissat can now receive messages again!")
        
    except Exception as e2:
        print(f"❌ Fallback also failed: {e2}")
