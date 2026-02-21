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

# المجموعات المستهدفة (فارغة = يعمل في جميع المجموعات)
TARGET_GROUPS = []  # فارغ = جميع المجموعات

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

# الكلمات الممنوعة
BANNED_WORDS = [
    # كلمات احتيال
    "سكليف",
    "خطابة",
    "راتب بدون عمل",
    "متاح سهرات",
    "جلسات مساج",
    "مـتاح سـهرات",
    "جلـسـات مـسـاج",
    "عقد ايجار موثق",
    "عقد إيجار موثق",
    
    # عامة
    "احتيال",
    "نصب",
    "spam",
]

# الحد الأقصى للرسائل المتكررة
MAX_FLOOD_MESSAGES = 5  # 5 رسائل
FLOOD_TIME_WINDOW = 10  # خلال 10 ثواني

# قيود الرسائل الطويلة والرموز
MAX_MESSAGE_LENGTH = 160  # أقصى طول للرسالة (عدد الأحرف)
MAX_EMOJI_COUNT = 10  # أقصى عدد للإيموجي/الرموز
MUTE_DURATION = 3 * 60 * 60  # 3 ساعات بالثواني

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

def is_admin(chat_id, user_id):
    """التحقق من أن المستخدم مشرف"""
    try:
        payload = {
            'chat_id': chat_id,
            'user_id': user_id
        }
        response = requests.post(f"{API_URL}/getChatMember", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json().get('result', {})
            status = result.get('status', '')
            # المشرفون: creator (المالك) أو administrator (مشرف)
            return status in ['creator', 'administrator']
        return False
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
    user_name = message.get('from', {}).get('first_name', 'Unknown')
    
    # طباعة الرسالة للتشخيص
    print(f"\n📩 رسالة جديدة من {user_name} (ID: {user_id})")
    print(f"   النص: {text[:100]}...")
    
    # ✅ تجاهل رسائل المشرفين تماماً
    is_user_admin = is_admin(chat_id, user_id)
    print(f"   مشرف؟ {is_user_admin}")
    
    if is_user_admin:
        print(f"   ✅ تم تجاهل رسالة المشرف")
        return False  # المشرفون معفيون من جميع القيود
    
    # 1. فحص أرقام الجوالات السعودية (كشف ذكي مع التلاعب)
    # تحويل الأرقام العربية والإنجليزية إلى صيغة موحدة
    # يكشف: 0598746619، 0٠598746619، 05 98 74 66 19، 0-5-9-8-7-4-6-6-1-9
    text_numbers = text
    # تحويل الأرقام العربية (٠-٩) إلى إنجليزية (0-9)
    arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    text_numbers = text_numbers.translate(arabic_to_english)
    # إزالة جميع الرموز والمسافات، إبقاء الأرقام فقط
    numbers_only = re.sub(r'[^\d]', '', text_numbers)
    
    # البحث عن نمط 05xxxxxxxx (10 أرقام تبدأ بـ 05)
    phone_pattern = r'05\d{8}'
    if re.search(phone_pattern, numbers_only):
        print(f"   🚫 اكتُشف رقم جوال (05...): {numbers_only[:10]}")
        delete_message(chat_id, message_id)
        return True
    
    # 2. فحص أرقام الجوالات مع رمز الدولة (+966 أو 00966)
    # يكشف: +966598746619، +٩٦٦٥٩٨٧٤٦٦١٩، 00966598746619
    phone_pattern_country = r'(966|00966)\d{9}'
    if re.search(phone_pattern_country, numbers_only):
        print(f"   🚫 اكتُشف رقم جوال (+966...)")
        delete_message(chat_id, message_id)
        return True
    
    # 3. فحص الكلمات الممنوعة (مع كشف التلاعب)
    text_lower = text.lower()
    
    # إزالة جميع الرموز والمسافات والتشكيل والحروف الممطوطة
    # يزيل: المسافات، الأرقام، الرموز، التشكيل، التطويل
    text_clean = re.sub(r'[\u064B-\u065F\u0640\s\d\W_]+', '', text_lower)
    
    for word in BANNED_WORDS:
        word_clean = re.sub(r'[\u064B-\u065F\u0640\s\d\W_]+', '', word.lower())
        if word_clean in text_clean:
            print(f"   🚫 اكتُشفت كلمة محظورة: {word} (في النص: {text[:50]}...)")
            delete_message(chat_id, message_id)
            return True
    
    # 4. كشف التكرار المشبوه (حرف يتكرر 3+ مرات متتالية)
    # يكشف: ســـكـــلـــيف، اااااا، 000000
    repeated_pattern = r'(.)\1{3,}'  # أي حرف يتكرر 4 مرات أو أكثر
    if re.search(repeated_pattern, text):
        print(f"   🚫 تكرار مشبوه للأحرف (محاولة تلاعب)")
        delete_message(chat_id, message_id)
        return True
    
    # كشف حرف التطويل (ـ) الزائد (3+ مرات في الرسالة)
    tatweel_count = text.count('\u0640')
    if tatweel_count >= 3:
        print(f"   🚫 تطويل زائد ({tatweel_count} مرات) - محاولة تلاعب")
        delete_message(chat_id, message_id)
        return True
    
    # 5. كشف نسبة الرموز إلى النص (إذا الرموز > 30%)
    # الرموز: أي شيء ليس حرف أو مسافة (أرقام، إيموجي، علامات)
    text_length = len(text)
    if text_length > 0:
        # حساب عدد الأحرف العادية فقط (عربي + مسافة)
        normal_chars = re.findall(r'[\u0621-\u064A\s]', text)
        normal_ratio = len(normal_chars) / text_length
        
        # إذا الأحرف العادية أقل من 70% (أي الرموز أكثر من 30%)
        if normal_ratio < 0.7:
            print(f"   🚫 نسبة رموز عالية ({int((1-normal_ratio)*100)}%) - رسالة مشبوهة")
            delete_message(chat_id, message_id)
            return True
    
    # 6. فحص اليوزرات (@username) - حذف مباشر بدون تحذير
    username_pattern = r'@\w+'
    if re.search(username_pattern, text):
        delete_message(chat_id, message_id)
        return True
    
    # 7. فحص طول الرسالة - حذف + كتم 3 ساعات (صامت)
    if len(text) > MAX_MESSAGE_LENGTH:
        delete_message(chat_id, message_id)
        # كتم لمدة 3 ساعات بدون إرسال رسالة
        mute_until = int(time.time()) + MUTE_DURATION
        restrict_user(chat_id, user_id, mute_until)
        print(f"   🚫 رسالة طويلة ({len(text)} حرف) - تم الحذف والكتم صامتاً")
        return True
    
    # 6. فحص الرموز والإيموجي - حذف + كتم 3 ساعات
    # نمط للإيموجي والرموز الخاصة
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251\u2600-\u26FF\u2700-\u27BF]|[★☆⭐✨💫🌟⚡✅❌⚠️🔥💯👍👎🎯🚀]'
    emojis = re.findall(emoji_pattern, text)
    
    if len(emojis) > MAX_EMOJI_COUNT:
        delete_message(chat_id, message_id)
        # كتم لمدة 3 ساعات بدون إرسال رسالة
        mute_until = int(time.time()) + MUTE_DURATION
        restrict_user(chat_id, user_id, mute_until)
        print(f"   🚫 رموز كثيرة ({len(emojis)} رمز) - تم الحذف والكتم صامتاً")
        return True
    
    # 7. فحص الصور - حذف مباشر بدون تحذير
    if 'photo' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 8. فحص الفيديو - حذف مباشر بدون تحذير
    if 'video' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 9. فحص الصوتيات - حذف مباشر بدون تحذير
    if 'audio' in message or 'voice' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 10. فحص الملفات - حذف مباشر بدون تحذير
    if 'document' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 11. فحص الملصقات - حذف مباشر بدون تحذير
    if 'sticker' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 12. فحص GIF/Animation - حذف مباشر بدون تحذير
    if 'animation' in message:
        delete_message(chat_id, message_id)
        return True
    
    # 13. فحص مقاطع الفيديو الدائرية - حذف مباشر بدون تحذير
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
        
        print(f"\n📥 تحديث جديد من مجموعة: {chat_id}")
        
        # تجاهل الرسائل من غير المجموعات المستهدفة
        if TARGET_GROUPS and chat_id not in TARGET_GROUPS:
            print(f"   ⏭️ تم تجاهل الرسالة (ليست من المجموعات المستهدفة)")
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
