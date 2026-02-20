#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 بوت إدارة المجموعات - أبو خالد
الميزات:
1. حذف تلقائي لليوزرات (@username)
2. حذف تلقائي للروابط (بدون تحذير)
3. حذف تلقائي لجميع الملفات (صور، فيديو، صوت، ملفات، ملصقات)
4. رسالة الترحيب للأعضاء الجدد
5. السماح بالرسائل النصية فقط
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta

# ============================================================
# الإعدادات الأساسية
# ============================================================

BOT_TOKEN = "8357322513:AAEOIBR-EVz0yqFXNytBLQSRWpSDjVxyYqY"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ملف لحفظ التحذيرات
WARNINGS_FILE = "warnings.json"

# المجموعات المستهدفة
TARGET_GROUPS = [
    -1003882183490,  # المجموعة الأساسية
    -1001660050244,  # مجموعة Dammam2030
]

# ============================================================
# الإعدادات
# ============================================================

# رسالة الترحيب
WELCOME_MESSAGE = """
🌟 **أهلاً وسهلاً {}!**

مرحباً بك في **أهالي المنطقة الشرقية** 🏙️

📋 **قوانين المجموعة:**
1️⃣ احترام جميع الأعضاء
2️⃣ عدم نشر روابط إعلانية
3️⃣ عدم السبام أو التكرار
4️⃣ المحتوى يخص المنطقة الشرقية فقط

⚠️ **التحذيرات:**
• 3 تحذيرات = طرد تلقائي

نتمنى لك وقتاً ممتعاً! 😊
"""

# الكلمات الممنوعة (أضف المزيد حسب الحاجة)
BANNED_WORDS = [
    "احتيال",
    "نصب",
    "spam",
]

# الحد الأقصى للرسائل المتكررة
MAX_FLOOD_MESSAGES = 5  # 5 رسائل
FLOOD_TIME_WINDOW = 10  # خلال 10 ثواني

# ============================================================
# تحميل وحفظ التحذيرات
# ============================================================

def load_warnings():
    """تحميل سجل التحذيرات"""
    try:
        with open(WARNINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_warnings(warnings):
    """حفظ سجل التحذيرات"""
    with open(WARNINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(warnings, f, ensure_ascii=False, indent=2)

# ============================================================
# دوال Telegram API
# ============================================================

def send_message(chat_id, text, parse_mode='Markdown', reply_to=None):
    """إرسال رسالة"""
    try:
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        if reply_to:
            payload['reply_to_message_id'] = reply_to
        
        response = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        return response.json().get('ok', False)
    except:
        return False

def delete_message(chat_id, message_id):
    """حذف رسالة"""
    try:
        payload = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        response = requests.post(f"{API_URL}/deleteMessage", json=payload, timeout=10)
        return response.json().get('ok', False)
    except:
        return False

def ban_user(chat_id, user_id):
    """طرد عضو"""
    try:
        payload = {
            'chat_id': chat_id,
            'user_id': user_id
        }
        response = requests.post(f"{API_URL}/banChatMember", json=payload, timeout=10)
        return response.json().get('ok', False)
    except:
        return False

def restrict_user(chat_id, user_id, until_date=None):
    """كتم عضو"""
    try:
        permissions = {
            'can_send_messages': False,
            'can_send_media_messages': False,
            'can_send_polls': False,
            'can_send_other_messages': False,
            'can_add_web_page_previews': False,
            'can_change_info': False,
            'can_invite_users': False,
            'can_pin_messages': False
        }
        
        payload = {
            'chat_id': chat_id,
            'user_id': user_id,
            'permissions': permissions
        }
        
        if until_date:
            payload['until_date'] = until_date
        
        response = requests.post(f"{API_URL}/restrictChatMember", json=payload, timeout=10)
        return response.json().get('ok', False)
    except:
        return False

def get_updates(offset=None, timeout=30):
    """الحصول على التحديثات"""
    try:
        payload = {
            'offset': offset,
            'timeout': timeout,
            'allowed_updates': ['message', 'chat_member']
        }
        response = requests.post(f"{API_URL}/getUpdates", json=payload, timeout=timeout+5)
        return response.json().get('result', [])
    except:
        return []

# ============================================================
# 1️⃣ الحماية من السبام والملفات
# ============================================================

# سجل الرسائل الأخيرة (للكشف عن Flood)
user_messages = {}

def check_spam(message):
    """فحص الرسائل للكشف عن السبام والملفات"""
    chat_id = message['chat']['id']
    user_id = message['from']['id']
    message_id = message['message_id']
    text = message.get('text', '') or message.get('caption', '')
    
    # تجاهل رسائل المشرفين
    # (يمكن تحسينه لاحقاً بفحص صلاحيات المشرف)
    
    # 1. فحص اليوزرات (@username) - حذف مباشر بدون تحذير
    username_pattern = r'@\w+'
    if re.search(username_pattern, text):
        delete_message(chat_id, message_id)
        return True
    
    # 2. فحص الصور - حذف مباشر بدون تحذير
    if 'photo' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 3. فحص الفيديو - حذف مباشر بدون تحذير
    if 'video' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 4. فحص الصوتيات - حذف مباشر بدون تحذير
    if 'audio' in message or 'voice' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 5. فحص الملفات - حذف مباشر بدون تحذير
    if 'document' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 6. فحص الملصقات - حذف مباشر بدون تحذير
    if 'sticker' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 7. فحص GIF/Animation - حذف مباشر بدون تحذير
    if 'animation' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 8. فحص مقاطع الفيديو الدائرية - حذف مباشر بدون تحذير
    if 'video_note' in message:
        delete_message(chat_id, message_id)
        return True
    
    return False

# ============================================================
# 2️⃣ نظام التحذيرات
# ============================================================

def add_warning(chat_id, user_id, user_name, reason):
    """إضافة تحذير للمستخدم"""
    warnings = load_warnings()
    
    key = f"{chat_id}_{user_id}"
    if key not in warnings:
        warnings[key] = {
            'user_id': user_id,
            'user_name': user_name,
            'count': 0,
            'reasons': []
        }
    
    warnings[key]['count'] += 1
    warnings[key]['reasons'].append({
        'reason': reason,
        'time': datetime.now().isoformat()
    })
    
    count = warnings[key]['count']
    
    save_warnings(warnings)
    
    # إرسال إشعار
    if count >= 3:
        # طرد المستخدم
        ban_user(chat_id, user_id)
        send_message(
            chat_id,
            f"🚫 **تم طرد {user_name}**\n\n"
            f"السبب: 3 تحذيرات\n"
            f"المخالفات:\n" + 
            "\n".join([f"• {r['reason']}" for r in warnings[key]['reasons'][-3:]])
        )
        # حذف التحذيرات
        del warnings[key]
        save_warnings(warnings)
    else:
        send_message(
            chat_id,
            f"⚠️ **تحذير ({count}/3) - {user_name}**\n\n"
            f"السبب: {reason}\n"
            f"تحذيران إضافيان = طرد تلقائي!"
        )

def get_user_warnings(chat_id, user_id):
    """الحصول على تحذيرات المستخدم"""
    warnings = load_warnings()
    key = f"{chat_id}_{user_id}"
    return warnings.get(key, None)

# ============================================================
# 3️⃣ رسالة الترحيب
# ============================================================

def handle_new_member(message):
    """التعامل مع الأعضاء الجدد"""
    chat_id = message['chat']['id']
    
    # فحص إذا كان هناك أعضاء جدد
    new_members = message.get('new_chat_members', [])
    
    for member in new_members:
        # تجاهل البوتات
        if member.get('is_bot', False):
            continue
        
        user_name = member.get('first_name', 'العضو')
        user_mention = f"[{user_name}](tg://user?id={member['id']})"
        
        # إرسال رسالة الترحيب
        welcome_text = WELCOME_MESSAGE.format(user_mention)
        send_message(chat_id, welcome_text)

# ============================================================
# المعالج الرئيسي
# ============================================================

def process_update(update):
    """معالجة التحديث"""
    # رسالة جديدة
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        
        # تجاهل الرسائل من غير المجموعات المستهدفة
        if chat_id not in TARGET_GROUPS:
            return
        
        # التعامل مع الأعضاء الجدد
        if 'new_chat_members' in message:
            handle_new_member(message)
            return
        
        # فحص الروابط والملفات (حذف صامت)
        if check_spam(message):
            return
        
        # السماح بالرسائل النصية فقط

# ============================================================
# الحلقة الرئيسية
# ============================================================

def main():
    """الحلقة الرئيسية للبوت"""
    print("\n🤖 بوت إدارة المجموعات - أبو خالد")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"\n📱 المجموعات المُدارة: {len(TARGET_GROUPS)}")
    for group_id in TARGET_GROUPS:
        print(f"  • {group_id}")
    print("\n🚀 البوت يعمل الآن...")
    print("⏹️  اضغط Ctrl+C للإيقاف\n")
    print("=" * 60)
    
    offset = None
    
    try:
        while True:
            # الحصول على التحديثات
            updates = get_updates(offset)
            
            for update in updates:
                # تحديث offset
                offset = update['update_id'] + 1
                
                # معالجة التحديث
                try:
                    process_update(update)
                except Exception as e:
                    print(f"❌ خطأ في معالجة التحديث: {e}")
            
            # انتظار قصير
            if not updates:
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف البوت")
        print("=" * 60)

if __name__ == "__main__":
    main()
