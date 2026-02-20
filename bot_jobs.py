#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت أخبار الوظائف - موقع أي وظيفة فقط
يستخرج الوظائف مباشرة من ewdifh.com
يعمل يومياً الساعة 06:00 و 18:00 (UTC)
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

# إعدادات البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8281406621:AAGpJOnC1Ua1I4t49h8kWea-7pND8zTSBhg')
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'
SENT_NEWS_FILE = 'sent_jobs.json'

# إعدادات موقع أي وظيفة
EWDIFH_URL = "https://www.ewdifh.com/category/all-jobs"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# كلمات مفتاحية للمنطقة الشرقية
EASTERN_KEYWORDS = [
    # المنطقة والمدن الرئيسية
    'المنطقة الشرقية', 'الشرقية', 'eastern province', 'eastern region',
    'الدمام', 'dammam', 'الخبر', 'khobar', 'al khobar', 'الظهران', 'dhahran',
    'الجبيل', 'jubail', 'الأحساء', 'al ahsa', 'ahsa', 'hofuf',
    'القطيف', 'qatif', 'al qatif', 'حفر الباطن', 'hafr al batin',
    # أحياء ومعالم
    'الراكة', 'الفيصلية', 'العزيزية', 'النزهة', 'الشاطئ',
    'أرامكو', 'aramco', 'saudi aramco',
    'سابك', 'sabic',
    'مطار الملك فهد', 'king fahd airport',
    'جامعة الدمام', 'جامعة الإمام عبدالرحمن', 'iau',
    'جامعة الملك فهد', 'kfupm',
    # محافظات
    'رأس تنورة', 'ras tanura',
    'النعيرية', 'الخفجي', 'khafji',
    'بقيق', 'buqayq',
    'الجبيل الصناعية', 'jubail industrial'
]

def load_sent():
    """تحميل الوظائف المرسلة سابقاً"""
    if os.path.exists(SENT_NEWS_FILE):
        try:
            with open(SENT_NEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_sent(data):
    """حفظ الوظائف المرسلة"""
    with open(SENT_NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_jobs_page(page=1):
    """جلب صفحة الوظائف من موقع أي وظيفة"""
    try:
        url = f"{EWDIFH_URL}?page={page}" if page > 1 else EWDIFH_URL
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ خطأ في جلب الصفحة {page}: {e}")
        return None

def parse_jobs(html):
    """استخراج الوظائف من HTML"""
    jobs = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # البحث عن روابط الوظائف
        job_links = soup.find_all('a', href=re.compile(r'https://www\.ewdifh\.com/jobs/\d+'))
        
        for link in job_links:
            try:
                job_url = link.get('href')
                
                # استخراج العنوان
                title_elem = link.find('h3') or link.find('h2') or link
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                # تجنب التكرار
                if title and not any(j['link'] == job_url for j in jobs):
                    jobs.append({
                        'title': title,
                        'link': job_url,
                        'source': 'موقع أي وظيفة',
                        'id': job_url,
                        'summary': '',
                        'published': datetime.now().isoformat()
                    })
            except:
                continue
        
        # إزالة التكرار
        unique_jobs = []
        seen_urls = set()
        for job in jobs:
            if job['link'] not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job['link'])
        
        return unique_jobs
        
    except Exception as e:
        print(f"❌ خطأ في تحليل HTML: {e}")
        return []

def fetch_job_details(job_url):
    """جلب تفاصيل الوظيفة"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(job_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # استخراج المحتوى
        content_div = soup.find('div', class_=['post-content', 'entry-content', 'content'])
        if content_div:
            content = content_div.get_text(strip=True)[:500]
            return content
        
        return ""
    except:
        return ""

def is_eastern_province(job):
    """التحقق من أن الوظيفة في المنطقة الشرقية"""
    text = f"{job.get('title', '')} {job.get('summary', '')}".lower()
    return any(k.lower() in text for k in EASTERN_KEYWORDS)

def get_chat_ids():
    """الحصول على معرفات المجموعات من متغيرات البيئة أو القيم الافتراضية"""
    # محاولة الحصول على IDs من متغيرات البيئة
    chat_ids_str = os.environ.get('CHAT_IDS', '')
    
    if chat_ids_str:
        # تحويل النص إلى قائمة أرقام
        try:
            return [int(id.strip()) for id in chat_ids_str.split(',') if id.strip()]
        except:
            pass
    
    # القيم الافتراضية
    default_ids = [
        -1003882183490,  # المجموعة الأساسية
        # -1001234567890,  # مجموعة Dammam2030 (سيتم تحديثه بعد الحصول على ID)
    ]
    return default_ids

def send_message(chat_id, message):
    """إرسال رسالة إلى تليجرام"""
    try:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        response = requests.post(f'{TELEGRAM_API}/sendMessage', json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def send_to_all_chats(message, chat_ids):
    """إرسال رسالة إلى جميع المجموعات"""
    success_count = 0
    failed_chats = []
    
    for chat_id in chat_ids:
        if send_message(chat_id, message):
            success_count += 1
            print(f"  ✅ تم الإرسال إلى {chat_id}")
        else:
            failed_chats.append(chat_id)
            print(f"  ❌ فشل الإرسال إلى {chat_id}")
    
    return success_count, failed_chats

def main():
    print(f"\n💼 بوت وظائف المنطقة الشرقية - موقع أي وظيفة")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    sent = load_sent()
    chat_ids = get_chat_ids()
    
    print(f"\n📱 المجموعات المستهدفة: {len(chat_ids)}")
    for chat_id in chat_ids:
        print(f"  • {chat_id}")
    
    # جلب الوظائف من صفحتين (حوالي 40 وظيفة)
    all_jobs = []
    for page in range(1, 3):
        print(f"\n📄 جلب صفحة {page}...")
        html = fetch_jobs_page(page)
        
        if html:
            jobs = parse_jobs(html)
            all_jobs.extend(jobs)
            print(f"  ✅ استخرجت {len(jobs)} وظيفة")
        else:
            print(f"  ⚠️ فشل جلب الصفحة {page}")
    
    print(f"\n📊 إجمالي الوظائف: {len(all_jobs)}")
    
    # جلب تفاصيل أول 20 وظيفة
    print("\n📝 جلب تفاصيل الوظائف للفلترة...")
    for i, job in enumerate(all_jobs[:20], 1):
        job['summary'] = fetch_job_details(job['link'])
        if i % 5 == 0:
            print(f"  ⏳ {i}/20...")
    
    # فلترة المنطقة الشرقية
    eastern_jobs = [j for j in all_jobs if is_eastern_province(j)]
    excluded = len(all_jobs) - len(eastern_jobs)
    
    print(f"\n✅ وظائف المنطقة الشرقية: {len(eastern_jobs)}")
    print(f"❌ مستبعد (خارج المنطقة): {excluded}")
    
    # فلترة الوظائف الجديدة
    new_jobs = [j for j in eastern_jobs if j['id'] not in sent]
    
    print(f"\n💼 وظائف جديدة: {len(new_jobs)}")
    
    if new_jobs:
        # إرسال أول 6 وظائف
        message = "💼 *وظائف المنطقة الشرقية - أي وظيفة*\n" + "━" * 30 + "\n\n"
        
        for job in new_jobs[:6]:
            message += f"• {job['title']}\n"
            message += f"  🔗 [التفاصيل]({job['link']})\n\n"
            sent[job['id']] = {
                'title': job['title'],
                'sent_at': datetime.now().isoformat()
            }
        
        # إرسال إلى جميع المجموعات
        print(f"\n📤 إرسال {len(new_jobs[:6])} وظيفة إلى المجموعات...")
        success_count, failed_chats = send_to_all_chats(message, chat_ids)
        
        if success_count > 0:
            print(f"\n✅ تم الإرسال بنجاح إلى {success_count}/{len(chat_ids)} مجموعة")
            save_sent(sent)
        else:
            print(f"\n❌ فشل الإرسال إلى جميع المجموعات")
        
        if failed_chats:
            print(f"⚠️ فشل الإرسال إلى: {failed_chats}")
    else:
        print("ℹ️ لا توجد وظائف جديدة")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
