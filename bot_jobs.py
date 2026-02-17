#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت أخبار الوظائف - المنطقة الشرقية
يعمل يومياً الساعة 06:00 و 18:00 (UTC)
"""

import feedparser
import requests
import json
import os
import time
from datetime import datetime
from dateutil import parser as date_parser

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8281406621:AAGpJOnC1Ua1I4t49h8kWea-7pND8zTSBhg')
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'
SENT_NEWS_FILE = 'sent_jobs.json'

JOBS_FEEDS = [
    {
        'name': 'وظائف الشرقية',
        'url': 'https://news.google.com/rss/search?q=وظائف+OR+توظيف+OR+فرص+عمل+(الدمام+OR+الخبر+OR+الجبيل+OR+الأحساء+OR+الشرقية)+when:2d&hl=ar&gl=SA&ceid=SA:ar',
    },
    {
        'name': 'Jobs Dammam',
        'url': 'https://news.google.com/rss/search?q=jobs+OR+hiring+OR+employment+(Dammam+OR+Khobar+OR+Dhahran+OR+Eastern)+when:2d&hl=en&gl=SA&ceid=SA:en',
    },
    {
        'name': 'وظائف المنطقة الشرقية',
        'url': 'https://news.google.com/rss/search?q=إعلان+وظيفي+OR+شواغر+(المنطقة+الشرقية+OR+الدمام+OR+الخبر)+when:2d&hl=ar&gl=SA&ceid=SA:ar',
    }
]

EASTERN_KEYWORDS = ['المنطقة الشرقية', 'الشرقية', 'الدمام', 'dammam', 'الخبر', 'khobar', 'الظهران', 'dhahran', 'الجبيل', 'jubail', 'الأحساء', 'القطيف', 'حفر الباطن', 'eastern province']

def load_sent():
    if os.path.exists(SENT_NEWS_FILE):
        try:
            with open(SENT_NEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_sent(data):
    with open(SENT_NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_rss(url, name):
    try:
        feed = feedparser.parse(url)
        news = []
        for entry in feed.entries[:20]:
            news.append({
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'summary': entry.get('summary', entry.get('description', '')),
                'published': entry.get('published', ''),
                'source': name,
                'id': entry.get('id', entry.get('link', ''))
            })
        return news
    except:
        return []

def is_eastern(news):
    text = f"{news.get('title', '')} {news.get('summary', '')}".lower()
    return any(k.lower() in text for k in EASTERN_KEYWORDS)

def is_jobs(news):
    text = f"{news.get('title', '')} {news.get('summary', '')}".lower()
    keywords = ['وظيفة', 'وظائف', 'توظيف', 'تعيين', 'فرص عمل', 'شواغر', 'إعلان وظيفي', 'job', 'jobs', 'hiring', 'employment', 'career', 'vacancy']
    return any(k in text for k in keywords)

def send_message(chat_id, message):
    try:
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
        response = requests.post(f'{TELEGRAM_API}/sendMessage', json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    print(f"\n💼 بوت أخبار الوظائف - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    sent = load_sent()
    chat_id = -1003882183490
    
    all_news = []
    for feed in JOBS_FEEDS:
        news = fetch_rss(feed['url'], feed['name'])
        all_news.extend(news)
        print(f"✅ {feed['name']}: {len(news)} خبر")
    
    # فلترة
    jobs_news = [n for n in all_news if is_eastern(n) and is_jobs(n)]
    new_news = [n for n in jobs_news if n['id'] not in sent]
    
    print(f"💼 أخبار وظائف جديدة: {len(new_news)}")
    
    if new_news:
        message = "💼 *وظائف المنطقة الشرقية*\n" + "━" * 30 + "\n\n"
        for news in new_news[:6]:
            message += f"• {news['title']}\n"
            message += f"  📌 {news['source']}\n\n"
            sent[news['id']] = {'title': news['title'], 'sent_at': datetime.now().isoformat()}
        
        if send_message(chat_id, message):
            print(f"✅ تم إرسال {len(new_news[:6])} وظيفة")
            save_sent(sent)
        else:
            print("❌ فشل الإرسال")
    else:
        print("ℹ️ لا توجد وظائف جديدة")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
