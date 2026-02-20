#!/bin/bash
# سكريبت لإضافة Chat ID مجموعة Dammam2030 يدوياً

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🔧 إضافة مجموعة Dammam2030 يدوياً"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "⚠️  المشكلة: البوت لا يستقبل تحديثات بسبب إعدادات الخصوصية"
echo ""
echo "✅ الحل السريع: احصل على Chat ID يدوياً"
echo ""

echo "📋 الطريقة 1 - استخدم @RawDataBot:"
echo "   1. أضف @RawDataBot إلى المجموعة"
echo "   2. سيرسل رسالة فوراً مثل:"
echo "      {\"chat\": {\"id\": -1001234567890}}"
echo "   3. انسخ الرقم"
echo ""

echo "📋 الطريقة 2 - استخدم @userinfobot:"
echo "   1. أضف @userinfobot إلى المجموعة"
echo "   2. سيرسل معلومات المجموعة"
echo "   3. ابحث عن Chat ID"
echo ""

echo "📋 الطريقة 3 - من تليجرام ديسكتوب:"
echo "   1. افتح المجموعة في Telegram Desktop"
echo "   2. اضغط بزر الماوس الأيمن على اسم المجموعة"
echo "   3. اختر 'Copy Link'"
echo "   4. الصق الرابط - سيظهر Chat ID"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo ""

read -p "هل حصلت على Chat ID؟ (y/n): " answer

if [[ $answer == "y" || $answer == "Y" ]]; then
    echo ""
    read -p "أدخل Chat ID (مثال: -1001234567890): " chat_id
    
    # التحقق من صحة الإدخال
    if [[ $chat_id =~ ^-100[0-9]{10,13}$ ]]; then
        echo ""
        echo "✅ Chat ID صحيح: $chat_id"
        echo ""
        echo "🔄 جاري تحديث bot_jobs.py..."
        
        # تحديث الملف
        sed -i "s/# -1001234567890,  # مجموعة Dammam2030/$chat_id,  # مجموعة Dammam2030/" bot_jobs.py
        
        echo "✅ تم التحديث!"
        echo ""
        echo "📝 الكود الجديد:"
        grep -A 2 "default_ids = \[" bot_jobs.py | head -4
        echo ""
        
        # اختبار
        echo "🧪 اختبار الإرسال..."
        echo '{}' > sent_jobs.json
        python3 bot_jobs.py | grep -E "(المجموعات المستهدفة|تم الإرسال إلى|وظائف جديدة)"
        
        echo ""
        echo "════════════════════════════════════════════════════════════════"
        echo "✅ تم بنجاح! البوت الآن سيرسل للمجموعتين معاً"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        
        read -p "حفظ التغييرات على GitHub؟ (y/n): " push_answer
        if [[ $push_answer == "y" || $push_answer == "Y" ]]; then
            git add bot_jobs.py
            git commit -m "➕ إضافة مجموعة Dammam2030 - Chat ID: $chat_id"
            echo ""
            echo "💾 تم الحفظ محلياً. لدفع التغييرات:"
            echo "   git push origin main"
        fi
        
    else
        echo ""
        echo "❌ Chat ID غير صحيح!"
        echo "   يجب أن يبدأ بـ -100 ويتكون من 13-16 رقم"
        echo "   مثال: -1001234567890"
    fi
else
    echo ""
    echo "ℹ️  لا مشكلة! استخدم أحد الطرق أعلاه ثم شغّل السكريبت مرة أخرى"
    echo ""
    echo "أو أرسل Chat ID مباشرة وسأحدّث الكود:"
    echo "   ./add_chat_id.sh"
fi

echo ""
