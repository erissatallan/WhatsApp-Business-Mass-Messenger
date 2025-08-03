#!/usr/bin/env python3
"""
Test script for Twilio WhatsApp integration
Run this to verify your Twilio credentials are working
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

def test_twilio_connection():
    """Test Twilio connection and credentials"""
    print("🧪 Testing Twilio WhatsApp Integration...")
    print("=" * 50)
    
    # Check environment variables
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_from = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
    
    print(f"Account SID: {account_sid[:8]}..." if account_sid else "❌ TWILIO_ACCOUNT_SID not found")
    print(f"Auth Token: {auth_token[:8]}..." if auth_token else "❌ TWILIO_AUTH_TOKEN not found")
    print(f"From Number: {twilio_from}")
    print()
    
    if not account_sid or not auth_token:
        print("❌ Missing Twilio credentials in .env file")
        print("Please update your .env file with:")
        print("TWILIO_ACCOUNT_SID=your_account_sid_here")
        print("TWILIO_AUTH_TOKEN=your_auth_token_here")
        return False
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Test connection by fetching account info
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Connected to Twilio account: {account.friendly_name}")
        print(f"✅ Account status: {account.status}")
        
        # List available WhatsApp senders
        try:
            senders = client.messaging.services.list()
            print(f"✅ Found {len(senders)} messaging services")
        except Exception as e:
            print(f"ℹ️  Messaging services check: {str(e)}")
        
        print()
        print("🎉 Twilio connection successful!")
        print()
        print("📝 Next steps:")
        print("1. Enable WhatsApp Sandbox in your Twilio Console")
        print("2. Follow the sandbox setup instructions")
        print("3. Test sending a message through the main application")
        
        return True
        
    except Exception as e:
        print(f"❌ Twilio connection failed: {str(e)}")
        print()
        print("🔧 Troubleshooting:")
        print("1. Verify your Account SID and Auth Token are correct")
        print("2. Check your internet connection")
        print("3. Ensure your Twilio account is active")
        
        return False

if __name__ == "__main__":
    test_twilio_connection()
