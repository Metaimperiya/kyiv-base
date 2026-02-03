import telebot
import requests
import base64
import os
from flask import Flask, request
import json

# Твои данные
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
REPO = "Metaimperiya/kyiv-base"

# ТВОЙ ТОКЕН ЦЕЛЫМ КУСКОМ
GH_TOKEN = "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"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def test_github_auth():
    """Проверка авторизации GitHub"""
    try:
        url = f"https://api.github.com/repos/{REPO}"
        headers = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except Exception as e:
        return False

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
        bot.send_message(message.chat.id, "⏳ Записываю в базу на сайт...")
        
        parts = message.text.strip().split(' ', 1)
        phone = parts[0].strip()
        desc = parts[1] if len(parts) > 1 else "Новый контакт"
        
        # Проверяем авторизацию перед действием
        if not test_github_auth():
            bot.reply_to(message, "❌ Ошибка авторизации GitHub (401). Похоже, GitHub заблокировал целый токен из-за безопасности!")
            return
        
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        headers = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "KYIV-BOT"
        }
        
        # Получаем текущий файл
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            bot.reply_to(message, f"❌ Ошибка загрузки файла: {res.status_code}")
            return
            
        res_data = res.json()
        content = base64.b64decode(res_data['content']).decode('utf-8')
        
        # Новая карточка для сайта
        new_card = f'''<div class="card">
    <h3>{desc}</h3>
    <span class="phone">{phone}</span>
    <a href="tel:{phone}" class="btn-call">Позвонить</a>
</div>'''
        
        # Вставляем после тега feed
        if '<div id="feed">' in content:
            updated_content = content.replace('<div id="feed">', f'<div id="feed">\n{new_card}')
        else:
            bot.reply_to(message, "❌ Не нашел блок <div id='feed'> в index.html")
            return
        
        # Пушим обратно
        payload = {
            "message": f"Добавлен контакт: {phone}",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": res_data['sha'],
            "branch": "main"
        }
        
        put_res = requests.put(url, json=payload, headers=headers)
        
        if put_res.status_code in [200, 201]:
            bot.reply_to(message, f"✅ Контакт добавлен!\n📞 {phone}\n🌐 https://kyiv-base.vercel.app/")
        else:
            bot.reply_to(message, f"❌ Ошибка записи {put_res.status_code}: {put_res.text[:100]}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Критическая ошибка: {str(e)}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
