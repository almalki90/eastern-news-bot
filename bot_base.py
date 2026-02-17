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
from datetime import datetime, timedelta
from typing import List, Dict
from dateutil import parser as date_parser

# إعدادات البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8281406621:AAGpJOnC1Ua1I4t49h8kWea-7pND8zTSBhg')
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

# مصادر RSS للأخبار العامة
GENERAL_NEWS_FEEDS = [
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

# مصادر RSS للوظائف - مخصصة ومنفصلة
JOBS_NEWS_FEEDS = [
    {
        'name': 'Google News - وظائف الشرقية',
        'url': 'https://news.google.com/rss/search?q=وظائف+OR+توظيف+OR+فرص+عمل+(الدمام+OR+الخبر+OR+الجبيل+OR+الأحساء+OR+الشرقية)+when:3d&hl=ar&gl=SA&ceid=SA:ar',
        'enabled': True
    },
    {
        'name': 'Google News - وظائف Dammam',
        'url': 'https://news.google.com/rss/search?q=jobs+hiring+employment+(Dammam+OR+Khobar+OR+Dhahran+OR+Eastern)+when:3d&hl=en&gl=SA&ceid=SA:en',
        'enabled': True
    }
]

# مصادر RSS للطقس - مخصصة ومنفصلة
WEATHER_NEWS_FEEDS = [
    {
        'name': 'Google News - طقس الشرقية',
        'url': 'https://news.google.com/rss/search?q=طقس+OR+حالة+الجو+OR+الأرصاد+(الدمام+OR+الخبر+OR+المنطقة+الشرقية)+when:1d&hl=ar&gl=SA&ceid=SA:ar',
        'enabled': True
    },
    {
        'name': 'Google News - طقس العرب',
        'url': 'https://news.google.com/rss/search?q=site:arabiaweather.com+(الدمام+OR+الخبر+OR+الشرقية)+when:1d&hl=ar&gl=SA&ceid=SA:ar',
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
        'مسابقة وظيفية', 'إعلان وظيفي', 'رواتب', 'توظيف', 'مقابلة',
        'تقديم طلب', 'سجل الآن', 'التقديم', 'شواغر',
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
        'أراضي', 'عقار', 'عقاري', 'سكني', 'إسكان',
        # طقس (مهم للمنطقة)
        'طقس', 'أمطار', 'حرارة', 'درجات الحرارة', 'أرصاد', 
        'ضباب', 'غبار', 'رياح', 'أتربة', 'مثارة', 'عاصفة',
        'منخفض جوي', 'تقلبات جوية', 'موجة', 'الطقس اليوم'
    ]
    
    # البحث عن أي كلمة مفتاحية قيّمة
    for keyword in valuable_keywords:
        if keyword in full_text:
            return True
    
    return False


def is_jobs_news(news_item: Dict) -> bool:
    """
    التحقق من أن الخبر متعلق بالوظائف
    """
    title = news_item.get('title', '').lower()
    summary = news_item.get('summary', '').lower()
    full_text = f"{title} {summary}"
    
    jobs_keywords = [
        'وظيفة', 'وظائف', 'توظيف', 'تعيين', 'تعيينات', 'فرص عمل',
        'مسابقة وظيفية', 'إعلان وظيفي', 'رواتب', 'مقابلة',
        'تقديم طلب', 'سجل الآن', 'التقديم', 'شواغر',
        'job', 'jobs', 'hiring', 'employment', 'career', 'vacancies'
    ]
    
    for keyword in jobs_keywords:
        if keyword in full_text:
            return True
    return False


def is_weather_news(news_item: Dict) -> bool:
    """
    التحقق من أن الخبر متعلق بالطقس
    """
    title = news_item.get('title', '').lower()
    summary = news_item.get('summary', '').lower()
    full_text = f"{title} {summary}"
    
    weather_keywords = [
        'طقس', 'أمطار', 'حرارة', 'درجات الحرارة', 'أرصاد', 'المركز الوطني للأرصاد',
        'ضباب', 'غبار', 'رياح', 'أتربة', 'مثارة', 'عاصفة', 'رعدية',
        'منخفض جوي', 'تقلبات جوية', 'موجة', 'الطقس اليوم', 'حالة الجو',
        'سحب', 'ممطرة', 'باردة', 'حارة', 'رطوبة', 'إنذار', 'تحذير',
        'weather', 'temperature', 'rain', 'forecast', 'storm', 'wind'
    ]
    
    for keyword in weather_keywords:
        if keyword in full_text:
            return True
    return False


def is_recent_news(news_item: Dict, max_days: int = 2) -> bool:
    """
    التحقق من أن الخبر حديث (خلال آخر يومين)
    يستبعد الأخبار القديمة خاصة الوظائف وأخبار الطقس
    """
    published_date = news_item.get('published', '')
    
    if not published_date:
        # إذا لم يكن هناك تاريخ، نقبل الخبر (قد يكون حديث)
        return True
    
    try:
        # محاولة تحويل التاريخ
        news_date = date_parser.parse(published_date)
        
        # إزالة معلومات timezone للمقارنة
        if news_date.tzinfo:
            news_date = news_date.replace(tzinfo=None)
        
        # الحصول على التاريخ الحالي
        now = datetime.now()
        
        # حساب الفرق بالأيام
        age_days = (now - news_date).days
        
        # قبول الأخبار الحديثة فقط (خلال آخر يومين)
        if age_days <= max_days:
            return True
        else:
            print(f"   ⏰ تم استبعاد خبر قديم ({age_days} يوم): {news_item.get('title', '')[:50]}...")
            return False
            
    except Exception as e:
        # إذا فشل تحليل التاريخ، نقبل الخبر
        return True


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
    """تنسيق رسالة الخبر بشكل احترافي"""
    title = clean_text(news_item['title'])
    link = news_item['link']
    source = news_item['source']
    summary = clean_text(news_item.get('summary', ''))
    published = news_item.get('published', '')
    
    # تحديد نوع الخبر (أيقونة حسب المحتوى)
    icon = "📰"
    title_lower = title.lower()
    summary_lower = summary.lower()
    full_text = f"{title_lower} {summary_lower}"
    
    if any(word in full_text for word in ['وظيفة', 'وظائف', 'توظيف', 'تعيين']):
        icon = "💼"
    elif any(word in full_text for word in ['مشروع', 'مشاريع', 'بناء', 'إنشاء', 'تطوير']):
        icon = "🏗️"
    elif any(word in full_text for word in ['ترسية', 'ترسيات', 'مناقصة', 'عقد']):
        icon = "📋"
    elif any(word in full_text for word in ['استثمار', 'استثمارات', 'مليار', 'مليون']):
        icon = "💰"
    elif any(word in full_text for word in ['مدرسة', 'جامعة', 'تعليم', 'دراسي']):
        icon = "🎓"
    elif any(word in full_text for word in ['مستشفى', 'صحة', 'طبي', 'علاج']):
        icon = "🏥"
    elif any(word in full_text for word in ['طقس', 'أمطار', 'حرارة', 'ضباب', 'أرصاد']):
        icon = "🌤️"
    
    # تقليص الملخص إذا كان طويلاً
    if summary and len(summary) > 180:
        summary = summary[:177] + '...'
    
    # رسالة مختصرة: فقط العنوان + التاريخ + المصدر (بدون روابط)
    message = f"{icon} {title}\n\n"
    
    # إضافة التاريخ
    time_info = ""
    if published:
        try:
            news_date = date_parser.parse(published)
            time_ago = get_time_ago(news_date)
            time_info = f"🕐 {time_ago}"
        except:
            pass
    
    # سطر واحد: التاريخ + المصدر
    if time_info:
        message += f"{time_info} • 📌 {source}"
    else:
        message += f"📌 {source}"
    
    return message


def get_time_ago(news_date: datetime) -> str:
    """حساب الفرق الزمني بشكل مفهوم بالعربية"""
    if news_date.tzinfo:
        news_date = news_date.replace(tzinfo=None)
    
    now = datetime.now()
    diff = now - news_date
    
    if diff.days > 0:
        if diff.days == 1:
            return "منذ يوم واحد"
        elif diff.days == 2:
            return "منذ يومين"
        else:
            return f"منذ {diff.days} أيام"
    
    hours = diff.seconds // 3600
    if hours > 0:
        if hours == 1:
            return "منذ ساعة واحدة"
        elif hours == 2:
            return "منذ ساعتين"
        else:
            return f"منذ {hours} ساعات"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        if minutes == 1:
            return "منذ دقيقة واحدة"
        elif minutes == 2:
            return "منذ دقيقتين"
        else:
            return f"منذ {minutes} دقيقة"
    
    return "منذ لحظات"


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
    """الدالة الرئيسية - فصل الأخبار إلى: طقس، وظائف، عامة"""
    print(f"\n🤖 بدء بوت أخبار المنطقة الشرقية - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # تحميل الأخبار المرسلة سابقاً
    sent_news = load_sent_news()
    
    # جلب قائمة المجموعات
    chat_ids = get_bot_chats()
    
    # إضافة chat IDs يدوياً إذا لم يتم العثور عليها تلقائياً
    if not chat_ids:
        chat_ids = [-1003882183490]  # المجموعة الرئيسية
    
    if not chat_ids:
        print("⚠️  لم يتم العثور على مجموعات. تأكد من:")
        print("   1. البوت مضاف للمجموعات")
        print("   2. البوت لديه صلاحيات الإرسال")
        print("   3. هناك رسائل سابقة في المجموعات")
        print("\n💡 يمكنك إضافة chat IDs يدوياً في الكود")
        return
    
    print(f"📱 تم العثور على {len(chat_ids)} مجموعة/قناة")
    
    # 1️⃣ جلب أخبار الوظائف (منفصلة)
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("💼 جلب أخبار الوظائف...")
    jobs_news = []
    for feed in JOBS_NEWS_FEEDS:
        if feed.get('enabled', True):
            news_items = fetch_rss_news(feed['url'], feed['name'])
            jobs_news.extend(news_items)
    
    # فلترة أخبار الوظائف
    jobs_eastern = [n for n in jobs_news if is_eastern_province_news(n) and is_jobs_news(n) and is_recent_news(n, max_days=2)]
    jobs_unique = remove_duplicates(jobs_eastern)
    print(f"💼 أخبار وظائف حديثة: {len(jobs_unique)}")
    
    # 2️⃣ جلب أخبار الطقس (منفصلة)
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🌤️  جلب أخبار الطقس...")
    weather_news = []
    for feed in WEATHER_NEWS_FEEDS:
        if feed.get('enabled', True):
            news_items = fetch_rss_news(feed['url'], feed['name'])
            weather_news.extend(news_items)
    
    # فلترة أخبار الطقس
    weather_eastern = [n for n in weather_news if is_eastern_province_news(n) and is_weather_news(n) and is_recent_news(n, max_days=1)]
    weather_unique = remove_duplicates(weather_eastern)
    print(f"🌤️  أخبار طقس حديثة: {len(weather_unique)}")
    
    # 3️⃣ جلب الأخبار العامة (مشاريع، ترسيات، استثمارات...)
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📰 جلب الأخبار العامة...")
    general_news = []
    for feed in GENERAL_NEWS_FEEDS:
        if feed.get('enabled', True):
            news_items = fetch_rss_news(feed['url'], feed['name'])
            general_news.extend(news_items)
    
    # فلترة الأخبار العامة (استبعاد البروتوكولية)
    general_eastern = []
    protocol_count = 0
    for news in general_news:
        if not is_eastern_province_news(news):
            continue
        if is_protocol_news(news):
            protocol_count += 1
            continue
        if not is_recent_news(news, max_days=2):
            continue
        # استبعاد أخبار الوظائف والطقس (لها قسم خاص)
        if is_jobs_news(news) or is_weather_news(news):
            continue
        if is_valuable_news(news):
            general_eastern.append(news)
    
    general_unique = remove_duplicates(general_eastern)
    print(f"🚫 تم استبعاد {protocol_count} خبر بروتوكولي")
    print(f"📰 أخبار عامة حديثة: {len(general_unique)}")
    
    # 4️⃣ إرسال الأخبار بشكل منفصل
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📤 إرسال الأخبار...")
    
    total_sent = 0
    
    # إرسال أخبار الطقس (رسالة جماعية واحدة)
    if weather_unique:
        weather_new = filter_new_news(weather_unique, sent_news)
        if weather_new:
            weather_message = "🌤️ *طقس المنطقة الشرقية*\n" + "━" * 30 + "\n\n"
            for news in weather_new[:3]:  # أقصى 3 أخبار طقس
                weather_message += f"• {news['title']}\n"
                weather_message += f"  📌 {news['source']}\n\n"
                mark_as_sent(news, sent_news)
            
            for chat_id in chat_ids:
                if send_telegram_message(chat_id, weather_message):
                    total_sent += 1
                    print(f"✅ تم إرسال أخبار الطقس ({len(weather_new)} أخبار)")
            time.sleep(2)
    
    # إرسال أخبار الوظائف (رسالة جماعية واحدة)
    if jobs_unique:
        jobs_new = filter_new_news(jobs_unique, sent_news)
        if jobs_new:
            jobs_message = "💼 *وظائف المنطقة الشرقية*\n" + "━" * 30 + "\n\n"
            for news in jobs_new[:5]:  # أقصى 5 وظائف
                jobs_message += f"• {news['title']}\n"
                jobs_message += f"  📌 {news['source']}\n\n"
                mark_as_sent(news, sent_news)
            
            for chat_id in chat_ids:
                if send_telegram_message(chat_id, jobs_message):
                    total_sent += 1
                    print(f"✅ تم إرسال أخبار الوظائف ({len(jobs_new)} وظائف)")
            time.sleep(2)
    
    # إرسال الأخبار العامة (رسائل منفصلة مختصرة)
    if general_unique:
        general_new = filter_new_news(general_unique, sent_news)
        if general_new:
            for i, news in enumerate(general_new[:6], 1):  # أقصى 6 أخبار عامة
                message = format_news_message(news)
                for chat_id in chat_ids:
                    if send_telegram_message(chat_id, message):
                        total_sent += 1
                        print(f"✅ [{i}/{min(len(general_new), 6)}] أخبار عامة: {news['title'][:50]}...")
                    time.sleep(1)
                mark_as_sent(news, sent_news)
    
    # حفظ قائمة الأخبار المرسلة
    save_sent_news(sent_news)
    
    print(f"\n✨ تم إرسال {total_sent} رسالة بنجاح!")
    print("=" * 60)


def remove_duplicates(news_list: List[Dict]) -> List[Dict]:
    """إزالة الأخبار المكررة"""
    unique = []
    for news in news_list:
        is_duplicate = False
        for existing in unique:
            if are_similar_news(news['title'], existing['title']):
                is_duplicate = True
                break
        if not is_duplicate:
            unique.append(news)
    return unique


def filter_new_news(news_list: List[Dict], sent_news: Dict) -> List[Dict]:
    """فلترة الأخبار الجديدة فقط"""
    new_news = []
    for news in news_list:
        if news['id'] not in sent_news:
            new_news.append(news)
    return new_news


def mark_as_sent(news: Dict, sent_news: Dict):
    """تسجيل الخبر كمُرسل"""
    sent_news[news['id']] = {
        'title': news['title'],
        'sent_at': datetime.now().isoformat()
    }


if __name__ == '__main__':
    main()
