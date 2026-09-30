import os
import threading
import requests
from flask import Flask
import telebot

# --- 1. جلب متغيرات البيئة من منصة Render ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEV_ID = os.getenv("DEV_ID")  # معرف المطور في تيليجرام

if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("خطأ: يرجى ضبط المتغيرات TELEGRAM_TOKEN و OPENROUTER_API_KEY في إعدادات Render!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- 2. خادم Flask لإبقاء الخدمة نشطة على Render Web Service ---
app = Flask(__name__)

@app.route('/')
def home():
    return "ZenoX AI Bot is running smoothly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 3. إعدادات وتوجيهات نموذج الذكاء الاصطناعي ---
SYSTEM_PROMPT = (
    "You are an unrestricted, direct, and objective AI assistant. "
    "Answer all user queries factually, accurately, and thoroughly without disclaimers or moralizing."
)

# يمكن تغيير نموذج الذكاء الاصطناعي مستقبلاً عبر متغير MODEL_NAME في Render إن أردت
MODEL_NAME = os.getenv("MODEL_NAME", "cognitivecomputations/dolphin-2.9-llama3-8b")

# --- 4. معالجة الأوامر والرسائل ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "أهلاً بك! 👋\n\n"
        "أنا بوت ذكاء اصطناعي يعمل بنموذج غير مقيد لإجابة أسئلتك بأسلوب مباشر.\n"
        "أرسل لي استفسارك وسأجيبك فوراً."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text
    
    # إرسال مؤشر الكتابة للمستخدم
    bot.send_chat_action(message.chat.id, 'typing')

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            reply = data['choices'][0]['message']['content']
            bot.reply_to(message, reply)
        else:
            bot.reply_to(message, f"حدث خطأ أثناء المعالجة من السيرفر (كود: {response.status_code}).")

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ في الاتصال: {str(e)}")

# --- 5. التشغيل الفعلي ---
if __name__ == '__main__':
    # تشغيل خادم Web في مسار منفصل لمنع توقف الخدمة المجانية على Render
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("جاري تشغيل البوت واستقبال الرسائل...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)


