import os
import time
import threading
import requests
from flask import Flask
import telebot

# --- 1. جلب متغيرات البيئة من Render ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("خطأ: يرجى ضبط المتغير TELEGRAM_TOKEN في إعدادات Render!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "ZenoX Uncensored AI Horde Bot is running smoothly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# مفتاح الشبكة المجاني العام
HORDE_API_KEY = "0000000000"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "أهلاً بك! 👋\n\n"
        "أنا بوت ذكاء اصطناعي يعتمد على شبكة AI Horde المفرغة بالكامل من القيود.\n"
        "أرسل لي استفسارك وسأجيبك مباشرة."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text
    bot.send_chat_action(message.chat.id, 'typing')

    headers = {
        "apikey": HORDE_API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "ZenoXBot:1.0:telegram"
    }

    # تحديد النماذج المفرغة من القيود المتاحة على الشبكة
    payload = {
        "prompt": f"User: {user_text}\nAssistant:",
        "params": {
            "max_context_length": 2048,
            "max_length": 512,
            "temperature": 0.7
        },
        "models": ["Dolphin 2.5 Mixtral 8x7b", "Psyfighter v2", "Aphrodite/koboldai/llama-3-8b-instruct"]
    }

    try:
        # 1. إرسال الطلب لشبكة AI Horde
        req = requests.post("https://aihorde.net/api/v2/generate/async", json=payload, headers=headers, timeout=30)
        
        if req.status_code != 202:
            bot.reply_to(message, f"خطأ من شبكة AI Horde (كود: {req.status_code})")
            return

        task_id = req.json().get("id")
        
        # 2. الانتظار في طابور التوليد المجاني
        max_retries = 35  # بحد أقصى 70 ثانية
        for _ in range(max_retries):
            time.sleep(2)
            check_req = requests.get(f"https://aihorde.net/api/v2/generate/status/{task_id}", headers=headers, timeout=10)
            
            if check_req.status_code == 200:
                data = check_req.json()
                if data.get("done"):
                    generations = data.get("generations", [])
                    if generations:
                        reply_text = generations[0].get("text", "").strip()
                        bot.reply_to(message, reply_text if reply_text else "لم يتم توليد نص.")
                    else:
                        bot.reply_to(message, "لم يتم الحصول على رد من النموذج.")
                    return

        bot.reply_to(message, "استغرق الطلب وقتاً أطول من المتوقع في طابور الشبكة. يرجى المحاولة مرة أخرى.")

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء الاتصال: {str(e)}")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    print("جاري تشغيل بوت AI Horde المفرغ...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

