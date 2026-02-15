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
from datetime import datetime
from typing import List, Dict

# إعدادات البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8281406621:AAGpJOnC1Ua1I4t49h8kWea-7pND8zTSBhg')
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

# مصادر RSS للأخبار السعودية والعربية
RSS_FEEDS = [
    {
        'name': 'عرب نيوز - السعودية',
        'url': 'https://www.arabnews.com/rss/saudi-arabia',
        'enabled': True
    },
    {
        'name': 'عرب نيوز - آخر الأخبار',
        'url': 'https://www.arabnews.com/rss',
        'enabled': True
    },
    {
        'name': 'الشرق الأوسط',
        'url': 'https://aawsat.com/feed',
        'enabled': True
    },
    {
        'name': 'BBC Arabic',
        'url': 'https://feeds.bbci.co.uk/arabic/rss.xml',
        'enabled': True
    },
    {
        'name': 'الجزيرة',
        'url': 'https://www.aljazeera.net/xml/rss/all.xml',
        'enabled': True
    }
]

# ملف لحفظ آخر الأخبار المرسلة
SENT_NEWS_FILE = 'sent_news.json'


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


def fetch_rss_news(feed_url: str, feed_name: str, max_items: int = 5) -> List[Dict]:
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


def format_news_message(news_item: Dict) -> str:
    """تنسيق رسالة الخبر"""
    title = news_item['title']
    link = news_item['link']
    source = news_item['source']
    summary = news_item.get('summary', '')
    
    # تقليص الملخص إذا كان طويلاً
    if summary and len(summary) > 300:
        summary = summary[:297] + '...'
    
    message = f"📰 *{title}*\n\n"
    if summary:
        message += f"{summary}\n\n"
    message += f"🔗 [اقرأ المزيد]({link})\n"
    message += f"📌 المصدر: {source}"
    
    return message


def send_telegram_message(chat_id: int, message: str) -> bool:
    """إرسال رسالة لمجموعة/قناة في تليجرام"""
    try:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
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
            print(f"❌ فشل الإرسال لـ {chat_id}: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ خطأ في الإرسال: {e}")
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
    
    # فلترة الأخبار الجديدة فقط
    new_news = []
    for news in all_news:
        news_id = news['id']
        if news_id not in sent_news:
            new_news.append(news)
            sent_news[news_id] = {
                'title': news['title'],
                'sent_at': datetime.now().isoformat()
            }
    
    print(f"🆕 أخبار جديدة: {len(new_news)}")
    
    # إرسال الأخبار الجديدة
    sent_count = 0
    for news in new_news:
        message = format_news_message(news)
        
        for chat_id in chat_ids:
            if send_telegram_message(chat_id, message):
                sent_count += 1
                print(f"✅ تم إرسال: {news['title'][:50]}... إلى {chat_id}")
            else:
                print(f"❌ فشل إرسال: {news['title'][:50]}... إلى {chat_id}")
    
    # حفظ قائمة الأخبار المرسلة
    save_sent_news(sent_news)
    
    print(f"\n✨ تم إرسال {sent_count} رسالة بنجاح!")
    print("=" * 60)


if __name__ == '__main__':
    main()
