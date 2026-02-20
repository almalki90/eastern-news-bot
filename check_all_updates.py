#!/usr/bin/env python3
import os
import requests
import json

BOT_TOKEN = os.getenv('BOT_TOKEN', '8281406621:AAFfRHTc0sTFk9EBf3eSW2kQAV4-WqdLd2s')
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# الحصول على جميع التحديثات (آخر 100 تحديث)
response = requests.get(f"{API_URL}/getUpdates", params={'limit': 100})

if response.status_code == 200:
    data = response.json()
    
    print("=" * 70)
    print("📊 إحصائيات التحديثات")
    print("=" * 70)
    
    if data.get('ok') and data.get('result'):
        updates = data['result']
        print(f"✅ عدد التحديثات: {len(updates)}")
        print()
        
        # عرض آخر 10 تحديثات
        print("=" * 70)
        print("📩 آخر 10 تحديثات")
        print("=" * 70)
        
        for update in updates[-10:]:
            print(f"\n🔹 Update ID: {update.get('update_id')}")
            
            # رسالة عادية
            if 'message' in update:
                msg = update['message']
                chat = msg.get('chat', {})
                print(f"   📱 النوع: رسالة")
                print(f"   💬 Chat Type: {chat.get('type')}")
                print(f"   🆔 Chat ID: {chat.get('id')}")
                print(f"   📝 Chat Title: {chat.get('title', 'N/A')}")
                if 'text' in msg:
                    print(f"   📄 Text: {msg.get('text', '')[:50]}")
            
            # عضو جديد في المجموعة
            elif 'my_chat_member' in update:
                member = update['my_chat_member']
                chat = member.get('chat', {})
                new_status = member.get('new_chat_member', {}).get('status')
                old_status = member.get('old_chat_member', {}).get('status')
                
                print(f"   📱 النوع: تحديث عضوية")
                print(f"   💬 Chat Type: {chat.get('type')}")
                print(f"   🆔 Chat ID: {chat.get('id')}")
                print(f"   📝 Chat Title: {chat.get('title', 'N/A')}")
                print(f"   📊 Status: {old_status} → {new_status}")
                
                # هذا هو Chat ID المطلوب!
                if chat.get('type') in ['group', 'supergroup']:
                    print(f"\n   🎯 وجدنا المجموعة!")
                    print(f"   🆔 Chat ID: {chat.get('id')}")
                    print(f"   📝 الاسم: {chat.get('title')}")
            
            # أنواع أخرى
            else:
                print(f"   📱 النوع: {list(update.keys())}")
        
        # البحث عن مجموعات
        print("\n" + "=" * 70)
        print("🔍 البحث عن مجموعات في التحديثات")
        print("=" * 70)
        
        groups_found = []
        for update in updates:
            chat = None
            
            if 'message' in update:
                chat = update['message'].get('chat')
            elif 'my_chat_member' in update:
                chat = update['my_chat_member'].get('chat')
            
            if chat and chat.get('type') in ['group', 'supergroup']:
                group_info = {
                    'id': chat.get('id'),
                    'title': chat.get('title'),
                    'type': chat.get('type')
                }
                if group_info not in groups_found:
                    groups_found.append(group_info)
        
        if groups_found:
            print(f"\n✅ وجدنا {len(groups_found)} مجموعة:\n")
            for i, group in enumerate(groups_found, 1):
                print(f"{i}. 📝 {group['title']}")
                print(f"   🆔 Chat ID: {group['id']}")
                print(f"   📱 Type: {group['type']}")
                print()
        else:
            print("\n⚠️ لم يتم العثور على أي مجموعات في التحديثات")
            print("\n💡 السبب المحتمل:")
            print("   - إعداد Group Privacy مفعّل")
            print("   - البوت لم يستقبل أي رسائل من المجموعة")
            print("   - لم يتم إرسال رسالة تذكر البوت (@Abukalidbot)")
    else:
        print("⚠️ لا توجد تحديثات")
        print("\n💡 جرب:")
        print("   1. أرسل رسالة في المجموعة تذكر البوت: @Abukalidbot")
        print("   2. أو أرسل أمر: /start")
        print("   3. أو استخدم @RawDataBot (الأسرع)")
else:
    print(f"❌ خطأ في الاتصال: {response.status_code}")

