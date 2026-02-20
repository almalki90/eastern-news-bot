#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت اختبار إرسال رسالة لكشف Chat ID
"""

import requests
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8281406621:AAGpJOnC1Ua1I4t49h8kWea-7pND8zTSBhg')
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Chat IDs المعروفة
KNOWN_CHAT_IDS = [
    -1003882183490,  # المجموعة الأساسية
]

# Chat IDs محتملة لمجموعة Dammam2030
# (سيتم تجربتها واحدة تلو الأخرى)
POSSIBLE_CHAT_IDS = [
    # يمكنك إضافة Chat IDs محتملة هنا للاختبار
]

def send_test_message(chat_id):
    """إرسال رسالة اختبار لمعرفة إذا كان Chat ID صحيح"""
    url = f'{TELEGRAM_API}/sendMessage'
    
    message = f"""
🧪 **رسالة اختبار**

تم إرسال هذه الرسالة للتحقق من Chat ID

Chat ID: `{chat_id}`
الوقت: {requests.utils.default_headers()['User-Agent']}
    """.strip()
    
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            return True, "✅ نجح الإرسال"
        else:
            error = result.get('description', 'خطأ غير معروف')
            return False, f"❌ {error}"
    except Exception as e:
        return False, f"❌ خطأ: {str(e)}"

def get_chat_info(chat_id):
    """الحصول على معلومات المجموعة"""
    url = f'{TELEGRAM_API}/getChat'
    
    try:
        response = requests.post(url, json={'chat_id': chat_id}, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            chat = result['result']
            return {
                'id': chat.get('id'),
                'title': chat.get('title', 'غير متوفر'),
                'type': chat.get('type', 'غير معروف'),
                'username': chat.get('username'),
                'description': chat.get('description')
            }
        return None
    except Exception as e:
        return None

def main():
    print("=" * 70)
    print("🧪 اختبار Chat IDs المعروفة")
    print("=" * 70)
    print()
    
    # اختبار المجموعات المعروفة
    print("📋 المجموعات المعروفة:")
    print()
    
    for chat_id in KNOWN_CHAT_IDS:
        print(f"🔍 اختبار Chat ID: {chat_id}")
        
        # الحصول على معلومات المجموعة
        info = get_chat_info(chat_id)
        if info:
            print(f"   ✅ اسم المجموعة: {info['title']}")
            print(f"   📂 النوع: {info['type']}")
            if info['username']:
                print(f"   👤 Username: @{info['username']}")
        
        # اختبار الإرسال
        success, message = send_test_message(chat_id)
        print(f"   {message}")
        print()
    
    print("=" * 70)
    print()
    print("💡 للحصول على Chat ID لمجموعة Dammam2030:")
    print()
    print("الطريقة الأسهل - استخدام @RawDataBot:")
    print("  1. افتح مجموعة Dammam2030")
    print("  2. أضف @RawDataBot إلى المجموعة")
    print("  3. سيرسل البوت رسالة فوراً مثل:")
    print()
    print('     {')
    print('       "message": {')
    print('         "chat": {')
    print('           "id": -1001234567890,  👈 هذا هو Chat ID')
    print('           "title": "Dammam2030",')
    print('           "type": "supergroup"')
    print('         }')
    print('       }')
    print('     }')
    print()
    print("  4. انسخ الرقم بعد \"id\": (يبدأ بـ -100)")
    print("  5. أخبرني به لتحديث البوت")
    print()
    print("=" * 70)
    print()
    print("🔗 روابط مفيدة:")
    print("  • بوت RawDataBot: https://t.me/RawDataBot")
    print("  • بوت أبو خالد: https://t.me/Abukalidbot")
    print("  • مجموعة Dammam2030: https://t.me/+bO-zbBfKSaY1MjRk")
    print()

if __name__ == '__main__':
    main()
