#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت للحصول على معرف مجموعة Telegram
"""

import requests
import json
import sys

BOT_TOKEN = "8281406621:AAGpJOnC1Ua1I4t49h8kWea-7pND8zTSBhg"
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

def get_updates():
    """جلب آخر التحديثات من البوت"""
    try:
        response = requests.get(f'{TELEGRAM_API}/getUpdates', timeout=10)
        data = response.json()
        
        if data.get('ok'):
            updates = data.get('result', [])
            print(f"\n📊 عدد التحديثات: {len(updates)}\n")
            print("=" * 80)
            
            chats = {}
            for update in updates:
                # التحقق من الرسائل العادية
                if 'message' in update:
                    chat = update['message'].get('chat', {})
                    chat_id = chat.get('id')
                    chat_title = chat.get('title', chat.get('first_name', 'Unknown'))
                    chat_type = chat.get('type')
                    
                    if chat_id and chat_id not in chats:
                        chats[chat_id] = {
                            'title': chat_title,
                            'type': chat_type,
                            'username': chat.get('username', 'N/A')
                        }
                
                # التحقق من تحديثات عضوية المجموعة
                if 'my_chat_member' in update:
                    chat = update['my_chat_member'].get('chat', {})
                    chat_id = chat.get('id')
                    chat_title = chat.get('title', 'Unknown')
                    chat_type = chat.get('type')
                    
                    if chat_id and chat_id not in chats:
                        chats[chat_id] = {
                            'title': chat_title,
                            'type': chat_type,
                            'username': chat.get('username', 'N/A')
                        }
            
            if chats:
                print("\n✅ المجموعات والقنوات المكتشفة:\n")
                for chat_id, info in chats.items():
                    print(f"📱 {info['title']}")
                    print(f"   ID: {chat_id}")
                    print(f"   النوع: {info['type']}")
                    if info['username'] != 'N/A':
                        print(f"   Username: @{info['username']}")
                    print()
            else:
                print("\n⚠️ لم يتم العثور على أي مجموعات في التحديثات")
                print("\n💡 للحصول على ID المجموعة:")
                print("   1. أضف البوت إلى مجموعة Dammam2030")
                print("   2. اجعله مسؤول (Admin)")
                print("   3. أرسل أي رسالة في المجموعة (مثل: /start)")
                print("   4. شغّل هذا السكريبت مرة أخرى\n")
            
            print("=" * 80)
        else:
            print(f"❌ خطأ: {data.get('description')}")
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")

def get_me():
    """معلومات البوت"""
    try:
        response = requests.get(f'{TELEGRAM_API}/getMe', timeout=10)
        data = response.json()
        
        if data.get('ok'):
            bot = data.get('result', {})
            print(f"\n🤖 معلومات البوت:")
            print(f"   الاسم: {bot.get('first_name')}")
            print(f"   Username: @{bot.get('username')}")
            print(f"   ID: {bot.get('id')}\n")
        else:
            print(f"❌ خطأ: {data.get('description')}")
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🔍 سكريبت الحصول على معرفات المجموعات")
    print("=" * 80)
    
    get_me()
    get_updates()
    
    print("\n📝 ملاحظة:")
    print("   - إذا لم تظهر المجموعة، أضف البوت إليها واجعله مسؤول")
    print("   - أرسل رسالة في المجموعة ثم شغّل السكريبت مرة أخرى")
    print("   - يمكنك أيضاً استخدام @RawDataBot في المجموعة\n")
