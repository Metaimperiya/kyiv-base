import telebot
import requests
import base64
import os
from flask import Flask, request

# Токен бота оставляем здесь, его GitHub не трогает
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
# Токен гитхаба теперь тянем из настроек Vercel (безопасно)
GH_TOKEN = os.getenv("GH_TOKEN")
REPO = "Metaimperiya/kyiv-base"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Бот работает!', 200

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    try:
        parts = message.text.split(' ', 1)
        phone = parts[0]
        desc = parts[1] if len(parts) > 1 else "Новый контакт"
        
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        headers = {"Authorization": f"token {GH_TOKEN}"}
        res = requests.get(url, headers=headers).json()
        
        content = base64.b64decode(res['content']).decode('utf-8')
        new_card = f'<div class="card"><h3>{desc}</h3><span class="phone">{phone}</span><a href="tel:{phone}" class="btn-call">Позвонить</a></div>'
        updated_content = content.replace('<div id="feed">', '<div id="feed">' + new_card)
        
        payload = {
            "message": "add contact",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": res['sha']
        }
        r = requests.put(url, json=payload, headers=headers)
        if r.status_code == 201 or r.status_code == 200:
            bot.reply_to(message, "✅ Записал на сайт!")
        else:
            bot.reply_to(message, f"❌ Ошибка GitHub: {r.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка кода: {str(e)}")
