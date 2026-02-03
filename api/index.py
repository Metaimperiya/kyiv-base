import telebot
import requests
import base64
import os
from flask import Flask, request

TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
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
    # Проверка: загрузился ли токен из настроек Vercel
    if not GH_TOKEN:
        bot.reply_to(message, "❌ Ошибка: Переменная GH_TOKEN не найдена в настройках Vercel!")
        return

    try:
        parts = message.text.split(' ', 1)
        phone = parts[0]
        desc = parts[1] if len(parts) > 1 else "Новый контакт"
        
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        headers = {
            "Authorization": f"token {GH_TOKEN.strip()}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Получаем файл
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            bot.reply_to(message, f"❌ Ошибка GitHub ({res.status_code}): {res.text}")
            return
            
        res_data = res.json()
        content = base64.b64decode(res_data['content']).decode('utf-8')
        
        new_card = f'<div class="card"><h3>{desc}</h3><span class="phone">{phone}</span><a href="tel:{phone}" class="btn-call">Позвонить</a></div>'
        updated_content = content.replace('<div id="feed">', '<div id="feed">' + new_card)
        
        payload = {
            "message": "crm update",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": res_data['sha']
        }
        
        put_res = requests.put(url, json=payload, headers=headers)
        if put_res.status_code in [200, 201]:
            bot.reply_to(message, "✅ Записал на сайт!")
        else:
            bot.reply_to(message, f"❌ Не смог обновить: {put_res.status_code}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")
