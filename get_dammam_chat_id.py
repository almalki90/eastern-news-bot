#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت للحصول على Chat ID لمجموعة Dammam2030
"""

import requests
import json
import os
import time

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8281406621:AAGpJOnC1Ua1I4t49h8kWea-7pND8zTSBhg')
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

def get_updates(offset=None):
    """الحصول على التحديثات من تليجرام"""
    url = f'{TELEGRAM_API}/getUpdates'
    params = {'timeout': 30, 'limit': 100}
    if offset:
        params['offset'] = offset
    
    try:
        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None

def extract_chat_ids(updates):
    """استخراج Chat IDs من التحديثات"""
    chat_ids = {}
    
    if not updates or not updates.get('result'):
        return chat_ids
    
    for update in updates['result']:
        # رسالة في مجموعة
        if 'message' in update:
            msg = update['message']
            chat = msg.get('chat', {})
            chat_id = chat.get('id')
            chat_title = chat.get('title', 'مجموعة غير معروفة')
            chat_type = chat.get('type')
            
            if chat_type in ['group', 'supergroup'] and chat_id:
                chat_ids[chat_id] = {
                    'title': chat_title,
                    'type': chat_type,
                    'username': chat.get('username', 'غير متوفر')
                }
        
        # البوت تمت إضافته إلى مجموعة
        if 'my_chat_member' in update:
            member = update['my_chat_member']
            chat = member.get('chat', {})
            chat_id = chat.get('id')
            chat_title = chat.get('title', 'مجموعة غير معروفة')
            chat_type = chat.get('type')
            
            if chat_type in ['group', 'supergroup'] and chat_id:
                chat_ids[chat_id] = {
                    'title': chat_title,
                    'type': chat_type,
                    'username': chat.get('username', 'غير متوفر'),
                    'event': 'تمت إضافة البوت'
                }
    
    return chat_ids

def main():
    print("=" * 60)
    print("🔍 البحث عن Chat ID لمجموعة Dammam2030")
    print("=" * 60)
    print()
    print("معلومات البوت:")
    print("  الاسم: ابو خالد")
    print("  Username: @Abukalidbot")
    print("  الرابط: https://t.me/Abukalidbot")
    print()
    print("=" * 60)
    print()
    
    # الحصول على التحديثات
    print("⏳ جاري الحصول على التحديثات من تليجرام...")
    updates = get_updates(offset=-100)
    
    if not updates:
        print("❌ فشل الحصول على التحديثات")
        print()
        print("=" * 60)
        print("📋 خطوات الحل:")
        print("=" * 60)
        print()
        print("الطريقة 1️⃣ - استخدام @RawDataBot (الأسهل):")
        print("  1. افتح مجموعة Dammam2030")
        print("  2. أضف البوت @RawDataBot إلى المجموعة")
        print("  3. سيرسل البوت رسالة فوراً تحتوي على:")
        print("     \"chat\": {")
        print("       \"id\": -1001234567890  👈 هذا هو Chat ID")
        print("     }")
        print()
        print("الطريقة 2️⃣ - من رابط الويب:")
        print("  1. افتح المجموعة على: https://web.telegram.org/k/")
        print("  2. انظر إلى رابط URL في المتصفح")
        print("  3. ابحث عن رقم بعد # (مثال: #-1001234567890)")
        print()
        return
    
    # استخراج Chat IDs
    chat_ids = extract_chat_ids(updates)
    
    if not chat_ids:
        print("⚠️ لم يتم العثور على أي مجموعات")
        print()
        print("=" * 60)
        print("📋 خطوات للحصول على Chat ID:")
        print("=" * 60)
        print()
        print("الطريقة 1️⃣ - استخدام @RawDataBot (الأسهل والأسرع):")
        print("  1. افتح مجموعة Dammam2030: https://t.me/+bO-zbBfKSaY1MjRk")
        print("  2. أضف @RawDataBot إلى المجموعة")
        print("  3. سيرسل البوت رسالة تحتوي على JSON")
        print("  4. ابحث عن \"chat\" → \"id\" (مثل: -1001234567890)")
        print()
        print("الطريقة 2️⃣ - إرسال رسالة:")
        print("  1. تأكد من أن @Abukalidbot مضاف كمشرف في المجموعة")
        print("  2. أرسل أي رسالة في المجموعة (مثل: /start أو مرحبا)")
        print("  3. انتظر 5 ثوان")
        print("  4. شغل هذا السكريبت مرة أخرى:")
        print("     python3 get_dammam_chat_id.py")
        print()
        print("الطريقة 3️⃣ - من رابط الويب:")
        print("  1. افتح المجموعة على: https://web.telegram.org/k/")
        print("  2. ستجد رقم في URL بعد # (مثل: #-1001234567890)")
        print()
        return
    
    # عرض النتائج
    print("✅ تم العثور على المجموعات التالية:")
    print()
    
    for chat_id, info in chat_ids.items():
        print(f"📱 المجموعة: {info['title']}")
        print(f"   🆔 Chat ID: {chat_id}")
        print(f"   📂 النوع: {info['type']}")
        if 'username' in info and info['username'] != 'غير متوفر':
            print(f"   👤 Username: @{info['username']}")
        if 'event' in info:
            print(f"   ⚡ حدث: {info['event']}")
        print()
    
    print("=" * 60)
    print()
    
    # البحث عن مجموعة Dammam
    dammam_found = False
    for chat_id, info in chat_ids.items():
        title_lower = info['title'].lower()
        if 'dammam' in title_lower or 'الدمام' in title_lower or '2030' in title_lower:
            print(f"🎯 وجدنا مجموعة Dammam!")
            print(f"   الاسم: {info['title']}")
            print(f"   Chat ID: {chat_id}")
            print()
            print("✅ استخدم هذا Chat ID في تحديث bot_jobs.py")
            dammam_found = True
            break
    
    if not dammam_found:
        print("💡 إذا لم تجد مجموعة Dammam2030 في القائمة أعلاه:")
        print("   استخدم @RawDataBot للحصول على Chat ID مباشرة")
        print("   أو أرسل رسالة في المجموعة وشغل السكريبت مرة أخرى")
        print()

if __name__ == '__main__':
    main()
