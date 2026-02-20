#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تفاعلي للحصول على Chat ID
يراقب التحديثات الجديدة بشكل مباشر
"""

import requests
import json
import time

BOT_TOKEN = "8281406621:AAGpJOnC1Ua1I4t49h8kWea-7pND8zTSBhg"
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

def get_updates_continuously():
    """مراقبة التحديثات بشكل مستمر"""
    print("\n" + "=" * 80)
    print("🔍 سكريبت مراقبة التحديثات (Live)")
    print("=" * 80)
    
    # معلومات البوت
    try:
        response = requests.get(f'{TELEGRAM_API}/getMe', timeout=10)
        bot = response.json().get('result', {})
        print(f"\n🤖 البوت: {bot.get('first_name')} (@{bot.get('username')})")
    except:
        print("\n❌ خطأ في الاتصال بالبوت")
        return
    
    print("\n⏳ في انتظار الرسائل...")
    print("💡 أرسل أي رسالة في المجموعة الآن (مثل: /start أو مرحبا)")
    print("   البوت سيكتشف المجموعة تلقائياً!")
    print("\nاضغط Ctrl+C للإيقاف\n")
    
    last_update_id = 0
    found_chats = set()
    
    try:
        while True:
            try:
                # جلب التحديثات الجديدة
                params = {}
                if last_update_id > 0:
                    params['offset'] = last_update_id + 1
                
                response = requests.get(f'{TELEGRAM_API}/getUpdates', params=params, timeout=10)
                data = response.json()
                
                if data.get('ok') and data.get('result'):
                    updates = data.get('result', [])
                    
                    for update in updates:
                        last_update_id = update.get('update_id', 0)
                        
                        # البحث في الرسائل العادية
                        if 'message' in update:
                            chat = update['message'].get('chat', {})
                            process_chat(chat, found_chats)
                        
                        # البحث في تحديثات العضوية
                        if 'my_chat_member' in update:
                            chat = update['my_chat_member'].get('chat', {})
                            process_chat(chat, found_chats)
                        
                        # البحث في رسائل القنوات
                        if 'channel_post' in update:
                            chat = update['channel_post'].get('chat', {})
                            process_chat(chat, found_chats)
                
                time.sleep(2)  # انتظار ثانيتين
                
            except KeyboardInterrupt:
                print("\n\n⏹️ تم إيقاف المراقبة")
                break
            except Exception as e:
                print(f"⚠️ خطأ: {e}")
                time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n\n⏹️ تم إيقاف المراقبة")
    
    if not found_chats:
        print("\n❌ لم يتم العثور على أي مجموعات")
        print("\n💡 تأكد من:")
        print("   1. البوت موجود في المجموعة")
        print("   2. البوت مسؤول (Admin)")
        print("   3. أرسلت رسالة في المجموعة")
        print("   4. البوت لديه صلاحية قراءة الرسائل\n")

def process_chat(chat, found_chats):
    """معالجة معلومات المجموعة"""
    chat_id = chat.get('id')
    chat_title = chat.get('title', chat.get('first_name', 'Unknown'))
    chat_type = chat.get('type')
    chat_username = chat.get('username', '')
    
    if chat_id and chat_id not in found_chats:
        found_chats.add(chat_id)
        
        print("\n" + "=" * 80)
        print(f"✅ تم اكتشاف مجموعة/قناة جديدة!")
        print("=" * 80)
        print(f"\n📱 الاسم: {chat_title}")
        print(f"🆔 Chat ID: {chat_id}")
        print(f"📝 النوع: {chat_type}")
        if chat_username:
            print(f"🔗 Username: @{chat_username}")
            print(f"🔗 الرابط: https://t.me/{chat_username}")
        
        # تحديث الكود تلقائياً
        print(f"\n💾 لإضافة هذه المجموعة للبوت، استخدم:")
        print(f"\ndefault_ids = [")
        print(f"    -1003882183490,  # المجموعة الأساسية")
        print(f"    {chat_id},  # {chat_title}")
        print(f"]")
        print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    try:
        get_updates_continuously()
    except KeyboardInterrupt:
        print("\n\n⏹️ تم إيقاف البرنامج")
