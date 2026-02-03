import telebot
import requests
import base64
from flask import Flask, request

# Данные бота
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
GH_TOKEN = "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"
REPO = "Metaimperiya/kyiv-base"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'OK', 200

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    try:
        # Разделяем сообщение на номер и описание
        parts = message.text.split(' ', 1)
        phone = parts[0]
        desc = parts[1] if len(parts) > 1 else "Новий контакт"
        
        # Стучимся в GitHub за файлом
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        headers = {"Authorization": f"token {GH_TOKEN}"}
        res = requests.get(url, headers=headers).json()
        
        # Декодируем и вставляем новую карточку
        content = base64.b64decode(res['content']).decode('utf-8')
        new_card = f'<div class="card"><h3>{desc}</h3><span class="phone">{phone}</span><a href="tel:{phone}" class="btn-call">Зателефонувати</a></div>'
        updated_content = content.replace('<div id="feed">', '<div id="feed">' + new_card)
        
        # Сохраняем обратно
        payload = {
            "message": "crm update",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": res['sha']
        }
        requests.put(url, json=payload, headers=headers)
        bot.reply_to(message, "✅ Готово! Номер на сайті.")
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {e}")

# Нужно для запуска на Vercel
def handler(request):
    return app(request)
