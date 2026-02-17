#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت أخبار الطقس - المنطقة الشرقية
يعمل يومياً الساعة 00:00 و 12:00 (UTC)
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
SENT_NEWS_FILE = 'sent_weather.json'

WEATHER_FEEDS = [
    {
        'name': 'طقس الشرقية',
        'url': 'https://news.google.com/rss/search?q=طقس+OR+حالة+الجو+OR+الأرصاد+(الدمام+OR+الخبر+OR+المنطقة+الشرقية)+when:1d&hl=ar&gl=SA&ceid=SA:ar',
    },
    {
        'name': 'طقس العرب',
        'url': 'https://news.google.com/rss/search?q=site:arabiaweather.com+(الدمام+OR+الخبر+OR+الشرقية)+when:1d&hl=ar&gl=SA&ceid=SA:ar',
    },
    {
        'name': 'المركز الوطني للأرصاد',
        'url': 'https://news.google.com/rss/search?q=site:ncm.gov.sa+(الدمام+OR+الشرقية)+when:1d&hl=ar&gl=SA&ceid=SA:ar',
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
        for entry in feed.entries[:15]:
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

def is_weather(news):
    text = f"{news.get('title', '')} {news.get('summary', '')}".lower()
    keywords = ['طقس', 'أمطار', 'حرارة', 'أرصاد', 'ضباب', 'غبار', 'رياح', 'عاصفة', 'سحب', 'رطوبة', 'weather']
    return any(k in text for k in keywords)

def send_message(chat_id, message):
    try:
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
        response = requests.post(f'{TELEGRAM_API}/sendMessage', json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    print(f"\n🌤️ بوت أخبار الطقس - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    sent = load_sent()
    chat_id = -1003882183490
    
    all_news = []
    for feed in WEATHER_FEEDS:
        news = fetch_rss(feed['url'], feed['name'])
        all_news.extend(news)
        print(f"✅ {feed['name']}: {len(news)} خبر")
    
    # فلترة
    weather_news = [n for n in all_news if is_eastern(n) and is_weather(n)]
    new_news = [n for n in weather_news if n['id'] not in sent]
    
    print(f"🌤️ أخبار طقس جديدة: {len(new_news)}")
    
    if new_news:
        message = "🌤️ *طقس المنطقة الشرقية*\n" + "━" * 30 + "\n\n"
        for news in new_news[:5]:
            message += f"• {news['title']}\n"
            message += f"  📌 {news['source']}\n\n"
            sent[news['id']] = {'title': news['title'], 'sent_at': datetime.now().isoformat()}
        
        if send_message(chat_id, message):
            print(f"✅ تم إرسال {len(new_news[:5])} خبر طقس")
            save_sent(sent)
        else:
            print("❌ فشل الإرسال")
    else:
        print("ℹ️ لا توجد أخبار طقس جديدة")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
