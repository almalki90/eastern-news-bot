#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تليجرام لأخبار المنطقة الشرقية - السعودية
يجلب الأخبار من RSS feeds ويرسلها تلقائياً للمجموعات
"""

import feedparser
import requests
import json
import os
import time
import re
from datetime import datetime
from typing import List, Dict

# إعدادات البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8281406621:AAGpJOnC1Ua1I4t49h8kWea-7pND8zTSBhg')
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

# مصادر RSS للأخبار السعودية المحلية
RSS_FEEDS = [
    # Google News - أخبار المنطقة الشرقية (بحث مخصص)
    {
        'name': 'Google News - المنطقة الشرقية',
        'url': 'https://news.google.com/rss/search?q=المنطقة+الشرقية+OR+الدمام+OR+الخبر+OR+الظهران+when:7d&hl=ar&gl=SA&ceid=SA:ar',
        'enabled': True
    },
    {
        'name': 'Google News - الدمام الخبر',
        'url': 'https://news.google.com/rss/search?q=الدمام+OR+الخبر+OR+القطيف+when:7d&hl=ar&gl=SA&ceid=SA:ar',
        'enabled': True
    },
    {
        'name': 'Google News - الأحساء الجبيل',
        'url': 'https://news.google.com/rss/search?q=الأحساء+OR+الجبيل+OR+حفر+الباطن+when:7d&hl=ar&gl=SA&ceid=SA:ar',
        'enabled': True
    },
    # مصادر عربية عامة (للفلترة)
    {
        'name': 'عرب نيوز - السعودية',
        'url': 'https://www.arabnews.com/rss/saudi-arabia',
        'enabled': True
    },
    {
        'name': 'الشرق الأوسط',
        'url': 'https://aawsat.com/feed',
        'enabled': True
    }
]

# ملف لحفظ آخر الأخبار المرسلة
SENT_NEWS_FILE = 'sent_news.json'

# كلمات مفتاحية للمنطقة الشرقية - يجب أن يحتوي الخبر على واحدة منها على الأقل
EASTERN_PROVINCE_KEYWORDS = [
    # المنطقة الشرقية
    'المنطقة الشرقية', 'الشرقية',
    # المدن الرئيسية
    'الدمام', 'dammam',
    'الخبر', 'khobar', 'al khobar',
    'الظهران', 'dhahran',
    'الجبيل', 'jubail',
    'الأحساء', 'الاحساء', 'al-ahsa', 'al ahsa', 'ahsa',
    'الهفوف', 'hofuf',
    'حفر الباطن', 'hafr al-batin', 'hafar albatin',
    'القطيف', 'qatif',
    'النعيرية', 'nairiyah',
    'رأس الخير', 'ras al khair',
    'الخفجي', 'khafji',
    # معالم مشهورة
    'كورنيش الدمام', 'كورنيش الخبر',
    'جامعة الدمام', 'جامعة الملك فهد للبترول',
    'أرامكو', 'aramco',
    'الملك فهد', 'king fahd',
    # أحياء ومناطق
    'الراكة', 'العزيزية', 'الفيصلية', 'الشاطئ'
]


def load_sent_news() -> Dict:
    """تحميل قائمة الأخبار المرسلة سابقاً"""
    if os.path.exists(SENT_NEWS_FILE):
        try:
            with open(SENT_NEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_sent_news(sent_news: Dict):
    """حفظ قائمة الأخبار المرسلة"""
    with open(SENT_NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sent_news, f, ensure_ascii=False, indent=2)


def get_bot_chats() -> List[int]:
    """
    الحصول على قائمة المجموعات/القنوات التي البوت فيها كمشرف
    """
    try:
        # جلب التحديثات الأخيرة
        response = requests.get(f'{TELEGRAM_API}/getUpdates', timeout=10)
        updates = response.json()
        
        chat_ids = set()
        if updates.get('ok'):
            for update in updates.get('result', []):
                # جلب chat_id من الرسائل
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    chat_type = update['message']['chat']['type']
                    # فقط المجموعات والقنوات (ليس الرسائل الخاصة)
                    if chat_type in ['group', 'supergroup', 'channel']:
                        chat_ids.add(chat_id)
                        
        return list(chat_ids)
    except Exception as e:
        print(f"❌ خطأ في جلب المجموعات: {e}")
        return []


def is_protocol_news(news_item: Dict) -> bool:
    """
    التحقق من أن الخبر بروتوكولي (استقبال، زيارات، تهنئة...)
    نريد استبعاد هذه الأخبار
    """
    title = news_item.get('title', '').lower()
    summary = news_item.get('summary', '').lower()
    full_text = f"{title} {summary}"
    
    # كلمات مفتاحية للأخبار البروتوكولية
    protocol_keywords = [
        'استقبل', 'يستقبل', 'استقبال', 'ودع', 'يودع', 'وداع',
        'رعى', 'يرعى', 'رعاية', 'افتتح حفل', 'حضر حفل',
        'كرم', 'يكرم', 'تكريم', 'هنأ', 'يهنئ', 'تهنئة',
        'التقى', 'يلتقي', 'لقاء', 'زار', 'يزور', 'زيارة',
        'اطلع على', 'يطلع على', 'تفقد', 'يتفقد'
    ]
    
    # إذا وُجدت أي كلمة بروتوكولية
    for keyword in protocol_keywords:
        if keyword in full_text:
            return True
    
    return False


def is_valuable_news(news_item: Dict) -> bool:
    """
    التحقق من أن الخبر قيّم (وظائف، مشاريع، ترسيات، مناقصات...)
    """
    title = news_item.get('title', '').lower()
    summary = news_item.get('summary', '').lower()
    full_text = f"{title} {summary}"
    
    # كلمات مفتاحية للأخبار المهمة
    valuable_keywords = [
        # وظائف
        'وظيفة', 'وظائف', 'توظيف', 'تعيين', 'تعيينات', 'فرص عمل',
        'مسابقة وظيفية', 'إعلان وظيفي', 'رواتب',
        # مشاريع
        'مشروع', 'مشاريع', 'تنفيذ مشروع', 'إطلاق مشروع', 'مشروع تطوير',
        'بناء', 'إنشاء', 'تشييد', 'تطوير', 'توسعة',
        # ترسيات ومناقصات
        'ترسية', 'ترسيات', 'مناقصة', 'مناقصات', 'عقد', 'عقود',
        'مشتريات', 'طرح', 'مزايدة', 'منافسة',
        # استثمار واقتصاد
        'استثمار', 'استثمارات', 'مليار', 'مليون', 'ريال',
        'اقتصاد', 'اقتصادي', 'تجاري', 'صناعي',
        # خدمات عامة
        'خدمة', 'خدمات', 'تشغيل', 'صيانة', 'نظافة', 'أمن',
        'نقل', 'طرق', 'جسر', 'كهرباء', 'مياه', 'صرف صحي',
        # تعليم وصحة
        'مدرسة', 'مستشفى', 'مركز صحي', 'جامعة', 'معهد',
        'تعليم', 'صحة', 'طبي', 'دراسي',
        # عقارات
        'أراضي', 'عقار', 'عقاري', 'سكني', 'إسكان'
    ]
    
    # البحث عن أي كلمة مفتاحية قيّمة
    for keyword in valuable_keywords:
        if keyword in full_text:
            return True
    
    return False


def is_eastern_province_news(news_item: Dict) -> bool:
    """
    التحقق من أن الخبر يتعلق بالمنطقة الشرقية
    يبحث عن الكلمات المفتاحية في العنوان والملخص
    """
    title = news_item.get('title', '').lower()
    summary = news_item.get('summary', '').lower()
    
    # دمج العنوان والملخص للبحث
    full_text = f"{title} {summary}"
    
    # البحث عن أي كلمة مفتاحية
    for keyword in EASTERN_PROVINCE_KEYWORDS:
        if keyword.lower() in full_text:
            return True
    
    return False


def fetch_rss_news(feed_url: str, feed_name: str, max_items: int = 20) -> List[Dict]:
    """جلب الأخبار من RSS feed"""
    try:
        print(f"📡 جلب أخبار من: {feed_name}")
        feed = feedparser.parse(feed_url)
        
        news_items = []
        for entry in feed.entries[:max_items]:
            news_item = {
                'title': entry.get('title', 'بدون عنوان'),
                'link': entry.get('link', ''),
                'summary': entry.get('summary', entry.get('description', '')),
                'published': entry.get('published', ''),
                'source': feed_name,
                'id': entry.get('id', entry.get('link', ''))
            }
            news_items.append(news_item)
        
        print(f"✅ تم جلب {len(news_items)} خبر من {feed_name}")
        return news_items
    except Exception as e:
        print(f"❌ خطأ في جلب {feed_name}: {e}")
        return []


def clean_text(text: str) -> str:
    """تنظيف النص من HTML والأحرف الزائدة"""
    if not text:
        return ""
    
    # إزالة HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # إزالة مسافات زائدة ومحارف خاصة
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def shorten_url(url: str) -> str:
    """اختصار الرابط لعرض أفضل"""
    try:
        # استخراج اسم الموقع فقط
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain
    except:
        return url[:30] + '...'


def are_similar_news(title1: str, title2: str) -> bool:
    """
    التحقق من تشابه الأخبار لمنع التكرار
    يقارن أول 50 حرف من العنوانين
    """
    # تنظيف العناوين
    t1 = clean_text(title1).lower()[:50]
    t2 = clean_text(title2).lower()[:50]
    
    # حساب نسبة التشابه
    if len(t1) < 10 or len(t2) < 10:
        return False
    
    # إذا كان أحدهما يحتوي على الآخر
    if t1 in t2 or t2 in t1:
        return True
    
    # حساب الكلمات المشتركة
    words1 = set(t1.split())
    words2 = set(t2.split())
    common = words1.intersection(words2)
    
    # إذا كان 70% من الكلمات مشتركة
    similarity = len(common) / max(len(words1), len(words2))
    return similarity > 0.7


def format_news_message(news_item: Dict) -> str:
    """تنسيق رسالة الخبر - نبذة قصيرة مع المصدر"""
    title = clean_text(news_item['title'])
    link = news_item['link']
    source = news_item['source']
    summary = clean_text(news_item.get('summary', ''))
    
    # تقليص الملخص إذا كان طويلاً
    if summary and len(summary) > 200:
        summary = summary[:197] + '...'
    
    # رسالة بسيطة وواضحة
    message = f"📰 {title}\n\n"
    
    if summary and summary != title:
        message += f"{summary}\n\n"
    
    message += f"📌 {source}"
    
    # إضافة رابط مختصر اختياري (معلق - يمكن تفعيله لاحقاً)
    # short_domain = shorten_url(link)
    # message += f" | 🔗 {short_domain}"
    
    return message


def send_telegram_message(chat_id: int, message: str, retry_count: int = 3) -> bool:
    """إرسال رسالة لمجموعة/قناة في تليجرام مع retry"""
    for attempt in range(retry_count):
        try:
            payload = {
                'chat_id': chat_id,
                'text': message,
                'disable_web_page_preview': False
            }
            
            response = requests.post(
                f'{TELEGRAM_API}/sendMessage',
                json=payload,
                timeout=10
            )
            
            result = response.json()
            if result.get('ok'):
                return True
            else:
                error_desc = result.get('description', '')
                
                # إذا كان الخطأ "Too Many Requests"، انتظر وأعد المحاولة
                if 'Too Many Requests' in error_desc:
                    retry_after = result.get('parameters', {}).get('retry_after', 5)
                    print(f"⏳ تليجرام يطلب الانتظار {retry_after} ثانية...")
                    time.sleep(retry_after + 1)
                    continue
                else:
                    print(f"❌ فشل الإرسال لـ {chat_id}: {error_desc}")
                    return False
        except Exception as e:
            print(f"❌ خطأ في الإرسال (محاولة {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
            return False
    
    return False


def main():
    """الدالة الرئيسية"""
    print(f"\n🤖 بدء بوت أخبار المنطقة الشرقية - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # تحميل الأخبار المرسلة سابقاً
    sent_news = load_sent_news()
    
    # جلب قائمة المجموعات
    chat_ids = get_bot_chats()
    
    # إضافة chat IDs يدوياً إذا لم يتم العثور عليها تلقائياً
    # يمكنك إضافة IDs المجموعات هنا:
    # chat_ids = [-1001234567890, -1009876543210]
    
    if not chat_ids:
        print("⚠️  لم يتم العثور على مجموعات. تأكد من:")
        print("   1. البوت مضاف للمجموعات")
        print("   2. البوت لديه صلاحيات الإرسال")
        print("   3. هناك رسائل سابقة في المجموعات")
        print("\n💡 يمكنك إضافة chat IDs يدوياً في الكود")
        return
    
    print(f"📱 تم العثور على {len(chat_ids)} مجموعة/قناة")
    
    # جلب الأخبار من كل المصادر
    all_news = []
    for feed in RSS_FEEDS:
        if not feed.get('enabled', True):
            continue
        news_items = fetch_rss_news(feed['url'], feed['name'])
        all_news.extend(news_items)
    
    print(f"\n📊 إجمالي الأخبار: {len(all_news)}")
    
    # فلترة الأخبار المتعلقة بالمنطقة الشرقية فقط
    eastern_news = []
    for news in all_news:
        if is_eastern_province_news(news):
            eastern_news.append(news)
    
    print(f"🏙️  أخبار المنطقة الشرقية: {len(eastern_news)}")
    
    # استبعاد الأخبار البروتوكولية والتركيز على الأخبار القيّمة
    valuable_news = []
    protocol_count = 0
    for news in eastern_news:
        # استبعاد الأخبار البروتوكولية
        if is_protocol_news(news):
            protocol_count += 1
            continue
        
        # قبول الأخبار القيّمة فقط
        if is_valuable_news(news):
            valuable_news.append(news)
    
    print(f"🚫 تم استبعاد {protocol_count} خبر بروتوكولي")
    print(f"✅ أخبار قيّمة (وظائف، مشاريع، ترسيات...): {len(valuable_news)}")
    
    # استخدام الأخبار القيّمة بدلاً من كل أخبار المنطقة
    eastern_news = valuable_news
    
    # إزالة الأخبار المكررة
    unique_news = []
    for news in eastern_news:
        is_duplicate = False
        for existing in unique_news:
            if are_similar_news(news['title'], existing['title']):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_news.append(news)
    
    print(f"🔄 بعد إزالة التكرار: {len(unique_news)}")
    
    # فلترة الأخبار الجديدة فقط
    new_news = []
    for news in unique_news:
        news_id = news['id']
        if news_id not in sent_news:
            new_news.append(news)
            sent_news[news_id] = {
                'title': news['title'],
                'sent_at': datetime.now().isoformat()
            }
    
    print(f"🆕 أخبار جديدة: {len(new_news)}")
    
    # تحديد عدد الأخبار للإرسال (حد أقصى 8 لتجنب الحظر)
    max_news_to_send = 8
    if len(new_news) > max_news_to_send:
        print(f"⚠️  سيتم إرسال أول {max_news_to_send} خبر فقط (من {len(new_news)})")
        news_to_send = new_news[:max_news_to_send]
    else:
        news_to_send = new_news
    
    # إرسال الأخبار الجديدة
    sent_count = 0
    for i, news in enumerate(news_to_send, 1):
        message = format_news_message(news)
        
        for chat_id in chat_ids:
            if send_telegram_message(chat_id, message):
                sent_count += 1
                print(f"✅ [{i}/{len(news_to_send)}] تم إرسال: {news['title'][:50]}...")
            else:
                print(f"❌ [{i}/{len(news_to_send)}] فشل إرسال: {news['title'][:50]}...")
            
            # انتظار قصير بين كل رسالة لتجنب rate limiting
            time.sleep(1)
    
    # حفظ قائمة الأخبار المرسلة
    save_sent_news(sent_news)
    
    print(f"\n✨ تم إرسال {sent_count} رسالة بنجاح!")
    print("=" * 60)


if __name__ == '__main__':
    main()
