#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت الأخبار العامة - المنطقة الشرقية
(مشاريع، ترسيات، مناقصات)
يعمل يومياً الساعة 03:00 و 15:00 (UTC)
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
SENT_NEWS_FILE = 'sent_general.json'

GENERAL_FEEDS = [
    {
        'name': 'Google News - الشرقية',
        'url': 'https://news.google.com/rss/search?q=المنطقة+الشرقية+OR+الدمام+OR+الخبر+when:3d&hl=ar&gl=SA&ceid=SA:ar',
    },
    {
        'name': 'الشرق الأوسط',
        'url': 'https://aawsat.com/feed',
    }
]

EASTERN_KEYWORDS = ['المنطقة الشرقية', 'الشرقية', 'الدمام', 'الخبر', 'الظهران', 'الجبيل', 'الأحساء', 'القطيف', 'حفر الباطن']

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

def is_protocol(news):
    text = f"{news.get('title', '')} {news.get('summary', '')}".lower()
    keywords = ['استقبل', 'يستقبل', 'ودع', 'رعى', 'كرم', 'هنأ', 'التقى', 'زار']
    return any(k in text for k in keywords)

def is_valuable(news):
    text = f"{news.get('title', '')} {news.get('summary', '')}".lower()
    keywords = ['مشروع', 'ترسية', 'مناقصة', 'عقد', 'استثمار', 'مليار', 'مليون', 'تطوير', 'بناء', 'إنشاء']
    return any(k in text for k in keywords)

def send_message(chat_id, message):
    try:
        payload = {'chat_id': chat_id, 'text': message, 'disable_web_page_preview': True}
        response = requests.post(f'{TELEGRAM_API}/sendMessage', json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    print(f"\n📰 بوت الأخبار العامة - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    sent = load_sent()
    chat_id = -1003882183490
    
    all_news = []
    for feed in GENERAL_FEEDS:
        news = fetch_rss(feed['url'], feed['name'])
        all_news.extend(news)
        print(f"✅ {feed['name']}: {len(news)} خبر")
    
    # فلترة
    eastern_news = [n for n in all_news if is_eastern(n)]
    valuable_news = [n for n in eastern_news if not is_protocol(n) and is_valuable(n)]
    new_news = [n for n in valuable_news if n['id'] not in sent]
    
    print(f"📰 أخبار عامة جديدة: {len(new_news)}")
    
    sent_count = 0
    for news in new_news[:4]:
        icon = "🏗️" if 'مشروع' in news['title'] else "📋" if 'ترسية' in news['title'] else "💰" if 'مليار' in news['title'] or 'مليون' in news['title'] else "📰"
        message = f"{icon} {news['title']}\n\n📌 {news['source']}"
        
        if send_message(chat_id, message):
            sent[news['id']] = {'title': news['title'], 'sent_at': datetime.now().isoformat()}
            sent_count += 1
            print(f"✅ تم إرسال: {news['title'][:50]}...")
            time.sleep(2)
    
    if sent_count > 0:
        save_sent(sent)
        print(f"✅ تم إرسال {sent_count} خبر")
    else:
        print("ℹ️ لا توجد أخبار جديدة")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
