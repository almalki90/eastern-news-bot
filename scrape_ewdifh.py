#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Scraper لموقع أي وظيفة (ewdifh.com)
استخراج ذكي للوظائف مع فلترة المنطقة الشرقية
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# إعدادات
EWDIFH_URL = "https://www.ewdifh.com/category/all-jobs"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

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

def fetch_jobs_page(page=1):
    """
    جلب صفحة الوظائف من موقع أي وظيفة
    """
    try:
        url = f"{EWDIFH_URL}?page={page}" if page > 1 else EWDIFH_URL
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ خطأ في جلب الصفحة {page}: {e}")
        return None

def parse_jobs(html):
    """
    استخراج الوظائف من HTML
    """
    jobs = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # البحث عن روابط الوظائف
        job_links = soup.find_all('a', href=re.compile(r'https://www\.ewdifh\.com/jobs/\d+'))
        
        print(f"  🔍 وجدت {len(job_links)} رابط وظيفة")
        
        for link in job_links:
            try:
                job_url = link.get('href')
                
                # استخراج العنوان
                title_elem = link.find('h3') or link.find('h2') or link
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                # تجنب التكرار (نفس الرابط قد يظهر مرتين)
                if not any(j['link'] == job_url for j in jobs):
                    jobs.append({
                        'title': title,
                        'link': job_url,
                        'source': 'موقع أي وظيفة',
                        'id': job_url,
                        'published': datetime.now().isoformat()
                    })
            except Exception as e:
                continue
        
        # إزالة التكرار بناءً على الرابط
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
    """
    جلب تفاصيل الوظيفة من صفحتها الخاصة
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(job_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # استخراج المحتوى
        content_div = soup.find('div', class_=['post-content', 'entry-content', 'content'])
        if content_div:
            # أخذ أول 500 حرف من المحتوى
            content = content_div.get_text(strip=True)[:500]
            return content
        
        return ""
    except:
        return ""

def is_eastern_province(job):
    """
    التحقق من أن الوظيفة في المنطقة الشرقية
    """
    text = f"{job.get('title', '')} {job.get('summary', '')}".lower()
    return any(k.lower() in text for k in EASTERN_KEYWORDS)

def scrape_ewdifh_jobs(max_pages=2):
    """
    استخراج الوظائف من موقع أي وظيفة
    """
    print("\n🔍 بدء استخراج الوظائف من موقع أي وظيفة...")
    print("=" * 60)
    
    all_jobs = []
    
    for page in range(1, max_pages + 1):
        print(f"\n📄 صفحة {page}...")
        html = fetch_jobs_page(page)
        
        if not html:
            print(f"  ⚠️ فشل جلب الصفحة {page}")
            continue
        
        jobs = parse_jobs(html)
        print(f"  ✅ استخرجت {len(jobs)} وظيفة")
        
        all_jobs.extend(jobs)
    
    print(f"\n📊 إجمالي الوظائف المستخرجة: {len(all_jobs)}")
    
    # جلب تفاصيل أول 20 وظيفة لتحسين الفلترة
    print("\n📝 جلب تفاصيل الوظائف لتحسين الفلترة...")
    for i, job in enumerate(all_jobs[:20], 1):
        print(f"  {i}/20: {job['title'][:50]}...")
        job['summary'] = fetch_job_details(job['link'])
    
    # فلترة المنطقة الشرقية
    eastern_jobs = [j for j in all_jobs if is_eastern_province(j)]
    excluded_jobs = [j for j in all_jobs if not is_eastern_province(j)]
    
    print(f"\n✅ وظائف المنطقة الشرقية: {len(eastern_jobs)}")
    print(f"❌ مستبعد (خارج المنطقة): {len(excluded_jobs)}")
    
    if excluded_jobs and len(excluded_jobs) <= 5:
        print("\n⚠️ أمثلة على الوظائف المستبعدة:")
        for job in excluded_jobs[:3]:
            print(f"  • {job['title'][:80]}")
    
    print("=" * 60)
    
    return eastern_jobs

def save_jobs_json(jobs, filename='scraped_jobs.json'):
    """
    حفظ الوظائف في ملف JSON
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 تم حفظ {len(jobs)} وظيفة في {filename}")

if __name__ == '__main__':
    # اختبار السكريبت
    jobs = scrape_ewdifh_jobs(max_pages=2)
    
    if jobs:
        save_jobs_json(jobs)
        
        print("\n📋 عينة من الوظائف المستخرجة:")
        for i, job in enumerate(jobs[:5], 1):
            print(f"\n{i}. {job['title']}")
            print(f"   🔗 {job['link']}")
    else:
        print("\n⚠️ لم يتم استخراج أي وظائف")
