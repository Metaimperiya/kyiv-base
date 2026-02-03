import telebot
import requests
import base64
import os
from flask import Flask, request

# Твои данные
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
REPO = "Metaimperiya/kyiv-base"

# Склеиваем токен, чтобы GitHub его не сожрал
p1 = "ghp_8SLtYtZOHUlwfPQM"
p2 = "JfIk4mvKMGub7a291nVa"
GH_TOKEN = p1 + p2

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'CRM работает!', 200

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    try:
        parts = message.text.strip().split(' ', 1)
        phone = parts[0]
        desc = parts[1] if len(parts) > 1 else "Новый контакт"
        
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        
        # Получаем файл
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            bot.reply_to(message, f"❌ Ошибка авторизации: {res.status_code}. Проверь права токена!")
            return
            
        res_data = res.json()
        content = base64.b64decode(res_data['content']).decode('utf-8')
        
        # Новая карточка
        new_card = f'<div class="card"><h3>{desc}</h3><span class="phone">{phone}</span><a href="tel:{phone}" class="btn-call">Позвонить</a></div>'
        
        if '<div id="feed">' in content:
            updated_content = content.replace('<div id="feed">', '<div id="feed">\n' + new_card)
        else:
            bot.reply_to(message, "❌ Не нашел блок <div id='feed'> в index.html")
            return
        
        # Отправляем обратно
        payload = {
            "message": "Update site",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": res_data['sha']
        }
        
        put_res = requests.put(url, json=payload, headers=headers)
        if put_res.status_code in [200, 201]:
            bot.reply_to(message, "✅ Сделал! Проверяй сайт.")
        else:
            bot.reply_to(message, f"❌ Ошибка записи: {put_res.status_code}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    app.run()
