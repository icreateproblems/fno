"""
Test Telegram alerts - verifies bot setup and sends test message
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.alerts import alert_manager

def test_telegram_setup():
    """Test Telegram bot configuration."""
    print("="*60)
    print("TELEGRAM BOT TEST")
    print("="*60)
    
    # Check environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    print(f"\n1. Checking configuration...")
    
    if not bot_token:
        print("   ❌ TELEGRAM_BOT_TOKEN not found in .env")
        print("   📝 Add: TELEGRAM_BOT_TOKEN=your_bot_token")
        print("   📖 See: docs/TELEGRAM_SETUP.md")
        return False
    
    if not chat_id:
        print("   ❌ TELEGRAM_CHAT_ID not found in .env")
        print("   📝 Add: TELEGRAM_CHAT_ID=your_chat_id")
        print("   📖 See: docs/TELEGRAM_SETUP.md")
        return False
    
    print(f"   ✅ Bot token configured: {bot_token[:20]}...")
    print(f"   ✅ Chat ID configured: {chat_id}")
    
    # Test connection
    print(f"\n2. Testing bot connection...")
    
    import requests
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()["result"]
            print(f"   ✅ Bot connected: @{bot_info['username']}")
            print(f"   ✅ Bot name: {bot_info['first_name']}")
        else:
            print(f"   ❌ Bot connection failed: {response.status_code}")
            print(f"   💡 Check your TELEGRAM_BOT_TOKEN")
            return False
    
    except Exception as e:
        print(f"   ❌ Connection error: {str(e)}")
        return False
    
    # Send test alerts (all severity levels)
    print(f"\n3. Sending test alerts...")
    
    test_cases = [
        ("INFO", "🎉 News Bot is online!", {"Version": "2.0", "Status": "Ready"}),
        ("WARNING", "⚠️ Test warning alert", {"Issue": "None", "Action": "Testing"}),
        ("ERROR", "❌ Test error alert", {"Error": "Simulated", "Recovery": "Automatic"}),
        ("CRITICAL", "🚨 Test critical alert", {"Severity": "High", "Action": "Test only"}),
    ]
    
    success_count = 0
    
    for severity, message, metadata in test_cases:
        try:
            result = alert_manager.send_alert(message, severity, metadata)
            if result:
                print(f"   ✅ {severity} alert sent")
                success_count += 1
            else:
                print(f"   ❌ {severity} alert failed")
        except Exception as e:
            print(f"   ❌ {severity} alert error: {str(e)}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"TEST RESULTS")
    print(f"{'='*60}")
    print(f"Alerts sent: {success_count}/4")
    
    if success_count == 4:
        print(f"\n✅ SUCCESS! Check your Telegram for 4 test messages.")
        print(f"📱 You'll receive alerts for:")
        print(f"   • Every post (success/skip)")
        print(f"   • Content safety violations")
        print(f"   • API failures")
        print(f"   • System health issues")
        print(f"   • Daily summaries")
        print(f"\n🎯 Your bot is ready for production!")
        return True
    else:
        print(f"\n⚠️  Some tests failed. Check configuration.")
        print(f"📖 See docs/TELEGRAM_SETUP.md for help")
        return False


if __name__ == "__main__":
    success = test_telegram_setup()
    sys.exit(0 if success else 1)
