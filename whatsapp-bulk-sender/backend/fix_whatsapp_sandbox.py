#!/usr/bin/env python3
"""
Twilio WhatsApp Sandbox Setup Helper
This script helps you find your correct WhatsApp sandbox number and setup instructions
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

def get_whatsapp_sandbox_info():
    """Get WhatsApp sandbox information from Twilio"""
    print("🔍 Checking your Twilio WhatsApp Sandbox Configuration...")
    print("=" * 60)
    
    # Get credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not all([account_sid, auth_token]):
        print("❌ Missing Twilio credentials in .env file")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        # Get account info
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Connected to Twilio account: {account.friendly_name}")
        print(f"✅ Account status: {account.status}")
        print()
        
        # Try to get WhatsApp senders
        print("📱 Checking WhatsApp configuration...")
        
        try:
            # Get messaging services (includes WhatsApp sandbox)
            messaging_services = client.messaging.services.list()
            
            if messaging_services:
                print(f"✅ Found {len(messaging_services)} messaging service(s)")
                for service in messaging_services:
                    print(f"   Service: {service.friendly_name} (SID: {service.sid})")
            else:
                print("⚠️  No messaging services found")
            
        except Exception as e:
            print(f"ℹ️  Messaging services: {str(e)}")
        
        # Try to get phone numbers
        try:
            phone_numbers = client.incoming_phone_numbers.list()
            whatsapp_numbers = [num for num in phone_numbers if 'whatsapp' in num.capabilities]
            
            if whatsapp_numbers:
                print(f"📞 WhatsApp-enabled numbers:")
                for num in whatsapp_numbers:
                    print(f"   {num.phone_number} ({num.friendly_name})")
            else:
                print("⚠️  No WhatsApp-enabled phone numbers found")
                
        except Exception as e:
            print(f"ℹ️  Phone numbers check: {str(e)}")
        
        print()
        print("🔧 SOLUTION STEPS:")
        print("=" * 60)
        print("1. Go to your Twilio Console: https://console.twilio.com")
        print("2. Navigate to: Messaging → Try it out → Send a WhatsApp message")
        print("3. You'll see your WhatsApp Sandbox settings with:")
        print("   - Your sandbox phone number (e.g., whatsapp:+14155238886)")
        print("   - Instructions to join the sandbox")
        print("4. Send the join code from your phone to activate the sandbox")
        print("5. Update your .env file with the correct sandbox number")
        print()
        print("📝 COMMON SANDBOX NUMBERS:")
        print("   - US Sandbox: whatsapp:+14155238886")
        print("   - Your current: whatsapp:+17629944238")
        print()
        print("⚠️  Your current number (+17629944238) might not be the correct sandbox number!")
        print("   Check the Twilio Console for your actual sandbox number.")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        
        if "credentials" in str(e).lower():
            print("\n🔧 Check your credentials:")
            print("1. Verify Account SID and Auth Token in .env file")
            print("2. Make sure they're copied correctly from Twilio Console")
        
        return False

def suggest_env_fix():
    """Suggest .env file fixes"""
    print("\n📄 Recommended .env file updates:")
    print("=" * 60)
    print("# Replace TWILIO_WHATSAPP_FROM with your actual sandbox number")
    print("# Common values:")
    print("TWILIO_WHATSAPP_FROM=whatsapp:+14155238886  # US Sandbox (most common)")
    print("# Or check your Twilio Console for the exact number")
    print()
    print("# Your current setting:")
    current_from = os.getenv('TWILIO_WHATSAPP_FROM', 'Not set')
    print(f"# TWILIO_WHATSAPP_FROM={current_from}")

if __name__ == "__main__":
    print("🚀 Twilio WhatsApp Sandbox Setup Helper")
    print("This will help you fix the 'Channel not found' error")
    print()
    
    success = get_whatsapp_sandbox_info()
    suggest_env_fix()
    
    if success:
        print("\n✅ Next steps:")
        print("1. Update your .env file with the correct sandbox number")
        print("2. Restart your Celery worker")
        print("3. Test again with a small campaign")
    else:
        print("\n❌ Please fix the connection issues first")
