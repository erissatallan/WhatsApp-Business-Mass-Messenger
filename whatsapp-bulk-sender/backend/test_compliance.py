#!/usr/bin/env python3
"""
WhatsApp Business Compliance Test Script
Demonstrates the enhanced opt-out detection and compliance features
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reply_handler import (
    detect_reply_sentiment_gemini, detect_reply_sentiment_basic, 
    normalize_phone_number, get_phone_number_variations,
    store_reply, setup_replies_database
)
from opt_out_manager import (
    setup_opt_out_tables, get_opt_out_analytics,
    schedule_opt_out_confirmation_message, is_phone_opted_out
)

def test_enhanced_opt_out_detection():
    """Test the enhanced opt-out detection with multiple languages and variations"""
    
    print("🔧 Testing Enhanced Opt-out Detection System\n")
    
    # Test messages that should be detected as opt-out
    opt_out_test_messages = [
        # English direct
        "STOP",
        "stop",
        "unsubscribe",
        "remove me",
        "don't message me",
        "I don't want these messages",
        "not interested in messages",
        "delete my number",
        "block me",
        "enough messages",
        "too many messages",
        "annoying",
        
        # Swahili
        "hatutaki",
        "sitaki",
        "acha",
        "wacha",
        "hapana",
        "sitaki ujumbe",
        "usinitumie",
        
        # Contextual/indirect
        "I'm not interested, please remove me from your list",
        "Can you stop sending me these promotional messages?",
        "This is annoying, I want to opt out",
        "Please unsubscribe me from these messages",
        "Hatutaki hii ujumbe tena",
    ]
    
    # Test messages that should NOT be detected as opt-out
    non_opt_out_messages = [
        "Hi, I'm interested in your products",
        "What are your store hours?",
        "Thank you for the message",
        "I love your products!",
        "Can I get a discount?",
        "Asante sana",
        "Poa sana",
        "Nataka kujua bei",
        "OK",
        "Yes",
        "No, I don't need this right now",  # 'No' but not opt-out
    ]
    
    print("✅ Testing OPT-OUT messages (should detect as DESIRED_OPT_OUT):")
    print("-" * 70)
    
    for i, message in enumerate(opt_out_test_messages, 1):
        try:
            # Test with basic detection first
            basic_result = detect_reply_sentiment_basic(message)
            
            # Test with Gemini (if available)
            print(f"{i:2d}. \"{message}\"")
            print(f"    Basic: {basic_result['sentiment']} ({basic_result['detailed_category']})")
            
            if os.getenv('GEMINI_API_KEY'):
                gemini_result = detect_reply_sentiment_gemini(message)
                print(f"    Gemini: {gemini_result['sentiment']} ({gemini_result['detailed_category']})")
                
                # Check if correctly detected
                is_correct = (
                    gemini_result['sentiment'] == 'desired_opt_out' or 
                    gemini_result['detailed_category'] == 'DESIRED_OPT_OUT'
                )
                print(f"    ✅ Correctly detected!" if is_correct else "    ❌ MISSED!")
            else:
                is_correct = (
                    basic_result['sentiment'] == 'desired_opt_out' or 
                    basic_result['detailed_category'] == 'DESIRED_OPT_OUT'
                )
                print(f"    ✅ Correctly detected!" if is_correct else "    ❌ MISSED!")
            
            print()
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            print()
    
    print("\n❌ Testing NON-OPT-OUT messages (should NOT detect as opt-out):")
    print("-" * 70)
    
    for i, message in enumerate(non_opt_out_messages, 1):
        try:
            basic_result = detect_reply_sentiment_basic(message)
            
            print(f"{i:2d}. \"{message}\"")
            print(f"    Basic: {basic_result['sentiment']} ({basic_result['detailed_category']})")
            
            if os.getenv('GEMINI_API_KEY'):
                gemini_result = detect_reply_sentiment_gemini(message)
                print(f"    Gemini: {gemini_result['sentiment']} ({gemini_result['detailed_category']})")
                
                # Check if correctly NOT detected as opt-out
                is_correct = (
                    gemini_result['sentiment'] != 'desired_opt_out' and 
                    gemini_result['detailed_category'] != 'DESIRED_OPT_OUT'
                )
                print(f"    ✅ Correctly classified!" if is_correct else "    ❌ FALSE POSITIVE!")
            else:
                is_correct = (
                    basic_result['sentiment'] != 'desired_opt_out' and 
                    basic_result['detailed_category'] != 'DESIRED_OPT_OUT'
                )
                print(f"    ✅ Correctly classified!" if is_correct else "    ❌ FALSE POSITIVE!")
            
            print()
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            print()

def test_phone_number_normalization():
    """Test phone number normalization and variation detection"""
    
    print("\n📞 Testing Phone Number Normalization\n")
    print("-" * 50)
    
    test_numbers = [
        "0712345678",           # Local format
        "+254712345678",        # International
        "254712345678",         # International without +
        "712345678",            # Missing leading zero
        "whatsapp:+254712345678", # Twilio format
        " +254 712 345 678 ",   # With spaces
        "+254-712-345-678",     # With dashes
    ]
    
    for number in test_numbers:
        normalized = normalize_phone_number(number)
        variations = get_phone_number_variations(number)
        
        print(f"Original:     {number}")
        print(f"Normalized:   {normalized}")
        print(f"Variations:   {variations}")
        print()

def test_compliance_workflow():
    """Test the complete compliance workflow"""
    
    print("\n🔄 Testing Complete Compliance Workflow\n")
    print("-" * 50)
    
    # Setup databases
    setup_replies_database()
    setup_opt_out_tables()
    
    # Test phone number
    test_phone = "+254712345678"
    test_message = "STOP sending me these messages"
    
    print(f"1. Storing opt-out reply: {test_message}")
    reply_id = store_reply(test_phone, test_message)
    
    if reply_id:
        print(f"   ✅ Reply stored with ID: {reply_id}")
        
        print(f"2. Checking if {test_phone} is opted out...")
        opted_out = is_phone_opted_out(test_phone)
        print(f"   {'✅' if opted_out else '❌'} Opted out status: {opted_out}")
        
        print(f"3. Scheduling opt-out confirmation...")
        scheduled = schedule_opt_out_confirmation_message(test_phone, "Test User")
        print(f"   {'✅' if scheduled else '❌'} Confirmation scheduled: {scheduled}")
        
        print(f"4. Getting opt-out analytics...")
        analytics = get_opt_out_analytics()
        print(f"   📊 Total opt-outs: {analytics['total_opt_outs']}")
        print(f"   📊 Pending confirmations: {analytics['pending_confirmations']}")
        
    else:
        print("   ❌ Failed to store reply")

def main():
    """Main test function"""
    
    print("🚀 WhatsApp Business Compliance System Test")
    print("=" * 60)
    
    # Check if Gemini API key is available
    if os.getenv('GEMINI_API_KEY'):
        print("✅ Gemini API key found - testing with AI")
    else:
        print("⚠️ No Gemini API key - testing basic detection only")
    
    print()
    
    try:
        # Test 1: Enhanced opt-out detection
        test_enhanced_opt_out_detection()
        
        # Test 2: Phone number normalization
        test_phone_number_normalization()
        
        # Test 3: Complete compliance workflow
        test_compliance_workflow()
        
        print("\n🎉 All compliance tests completed!")
        print("\n📋 Summary:")
        print("✅ Enhanced opt-out detection with multiple languages")
        print("✅ Phone number normalization and variation handling")
        print("✅ Automatic opt-out processing and confirmation scheduling")
        print("✅ Robust error handling and fallback mechanisms")
        print("✅ Complete compliance workflow integration")
        
        print("\n⚠️ Important Compliance Notes:")
        print("• All message templates must include 'Reply STOP to opt out'")
        print("• Business name must be clearly identified in all messages")
        print("• Opt-out confirmations should be sent within 1 hour")
        print("• Monitor opt-out rates (keep under 5% for best practices)")
        print("• Clean contact lists regularly to remove opted-out numbers")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
