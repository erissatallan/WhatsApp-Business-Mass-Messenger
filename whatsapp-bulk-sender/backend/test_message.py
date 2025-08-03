#!/usr/bin/env python3
"""
Quick test to send a sample WhatsApp message via Twilio
Run this after setting up your Twilio WhatsApp sandbox
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

def test_send_message():
    """Test sending a WhatsApp message via Twilio"""
    print("🧪 Testing WhatsApp Message Sending...")
    print("=" * 50)
    
    # Get credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_WHATSAPP_FROM')
    
    if not all([account_sid, auth_token, from_number]):
        print("❌ Missing Twilio credentials in .env file")
        return False
    
    # Test phone number (you can change this to your actual number)
    # Make sure this number has joined your Twilio WhatsApp sandbox!
    test_phone = input("Enter your phone number (format: +1234567890): ").strip()
    
    if not test_phone.startswith('+'):
        print("❌ Phone number must start with + (e.g., +1234567890)")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body="🎉 Test message from Mwihaki Intimates WhatsApp Bulk Sender!\n\nYour Twilio integration is working perfectly!",
            from_=from_number,
            to=f'whatsapp:{test_phone}'
        )
        
        print(f"✅ Message sent successfully!")
        print(f"📧 Message SID: {message.sid}")
        print(f"📱 Status: {message.status}")
        print(f"📞 To: {test_phone}")
        print()
        print("🎉 Your Twilio WhatsApp integration is working!")
        print("You can now use the full bulk messaging system.")
        
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ Message sending failed: {error_str}")
        print()
        
        if "not a valid WhatsApp number" in error_str:
            print("🔧 Troubleshooting:")
            print("1. Make sure your phone number has joined the Twilio WhatsApp Sandbox")
            print("2. Go to Twilio Console > Messaging > Try it out > Send a WhatsApp message")
            print("3. Send the join code from your phone to the sandbox number")
            print("4. Wait for confirmation before testing")
            
        elif "Permission denied" in error_str or "Forbidden" in error_str:
            print("🔧 Troubleshooting:")
            print("1. Verify your Account SID and Auth Token are correct")
            print("2. Check that your Twilio account is active and verified")
            print("3. Ensure WhatsApp messaging is enabled in your account")
            
        else:
            print("🔧 Troubleshooting:")
            print("1. Check your internet connection")
            print("2. Verify the phone number format (+1234567890)")
            print("3. Ensure the recipient has joined your WhatsApp sandbox")
            
        return False

if __name__ == "__main__":
    print("📱 Twilio WhatsApp Message Test")
    print("Make sure the recipient has joined your Twilio WhatsApp sandbox first!")
    print()
    
    proceed = input("Do you want to send a test message? (y/N): ").strip().lower()
    if proceed in ['y', 'yes']:
        test_send_message()
    else:
        print("Test cancelled. Run this script when you're ready to test messaging.")
