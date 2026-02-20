#!/usr/bin/env python3
"""
احصل على معلومات المجموعة من رابط الدعوة
"""
import os
import requests
import json

BOT_TOKEN = os.getenv('BOT_TOKEN', '8281406621:AAFfRHTc0sTFk9EBf3eSW2kQAV4-WqdLd2s')
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_updates():
    """الحصول على آخر التحديثات"""
    response = requests.get(f"{API_URL}/getUpdates", params={'offset': -1})
    if response.status_code == 200:
        return response.json()
    return None

def get_me():
    """الحصول على معلومات البوت"""
    response = requests.get(f"{API_URL}/getMe")
    if response.status_code == 200:
        return response.json()
    return None

def main():
    print("=" * 70)
    print("🤖 معلومات البوت")
    print("=" * 70)
    
    # معلومات البوت
    bot_info = get_me()
    if bot_info and bot_info.get('ok'):
        bot = bot_info['result']
        print(f"📱 الاسم: {bot.get('first_name', 'غير معروف')}")
        print(f"👤 Username: @{bot.get('username', 'غير معروف')}")
        print(f"🆔 Bot ID: {bot.get('id', 'غير معروف')}")
    
    print("\n" + "=" * 70)
    print("💬 آخر التحديثات")
    print("=" * 70)
    
    # الحصول على التحديثات
    updates = get_updates()
    if updates and updates.get('ok') and updates.get('result'):
        for update in updates['result'][-10:]:  # آخر 10 تحديثات
            print(f"\n📩 Update ID: {update.get('update_id')}")
            
            # رسالة عادية
            if 'message' in update:
                msg = update['message']
                chat = msg.get('chat', {})
                print(f"   💬 Chat Type: {chat.get('type')}")
                print(f"   🆔 Chat ID: {chat.get('id')}")
                print(f"   📝 Chat Title: {chat.get('title', 'N/A')}")
                print(f"   👤 From: {msg.get('from', {}).get('first_name', 'غير معروف')}")
                print(f"   📄 Text: {msg.get('text', 'N/A')[:50]}")
            
            # عضو جديد
            elif 'my_chat_member' in update:
                member = update['my_chat_member']
                chat = member.get('chat', {})
                print(f"   💬 Chat Type: {chat.get('type')}")
                print(f"   🆔 Chat ID: {chat.get('id')}")
                print(f"   📝 Chat Title: {chat.get('title', 'N/A')}")
                print(f"   ✅ Status: {member.get('new_chat_member', {}).get('status')}")
    else:
        print("⚠️ لم يتم العثور على تحديثات حديثة")
        print("\n💡 الخطوات التالية:")
        print("   1. تأكد من إضافة البوت @Abukalidbot إلى المجموعة")
        print("   2. اجعل البوت مشرفًا (Admin)")
        print("   3. أرسل رسالة في المجموعة (مثلاً: /start)")
        print("   4. شغّل هذا السكريبت مرة أخرى")
        print("\n🔧 أو استخدم @RawDataBot:")
        print("   1. أضف @RawDataBot للمجموعة")
        print("   2. سيرسل رسالة فورية بمعلومات المجموعة")
        print("   3. ابحث عن \"id\": -1001234567890")

if __name__ == "__main__":
    main()
