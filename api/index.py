import telebot
import requests
import base64
from flask import Flask, request

TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
REPO = "Metaimperiya/kyiv-base"

# Твой токен целиком (проверяем, выжил он или нет)
GH_TOKEN = "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"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'CRM Система в сети!', 200

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    try:
        bot.send_message(message.chat.id, "🔍 Тестирую твой токен...")
        
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        headers = {
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "KYIV-BOT"
        }
        
        res = requests.get(url, headers=headers)
        
        if res.status_code == 401:
            bot.reply_to(message, "⛔️ РЕЗУЛЬТАТ: Токен АННУЛИРОВАН. GitHub его удалил, потому что увидел в коде. Нужно создавать новый и РЕЗАТЬ его на части.")
            return
        elif res.status_code == 403:
            bot.reply_to(message, "⚠️ РЕЗУЛЬТАТ: Токен живой, но ты НЕ ДАЛ ПРАВА (Contents: Read and Write). Иди в настройки токена.")
            return
        elif res.status_code != 200:
            bot.reply_to(message, f"❌ РЕЗУЛЬТАТ: Неизвестная ошибка {res.status_code}")
            return

        # Если дошли сюда, значит токен работает!
        bot.reply_to(message, "✅ ТОКЕН РАБОТАЕТ! Сейчас попробую записать номер...")
        
        data = res.json()
        content = base64.b64decode(data['content']).decode('utf-8')
        
        new_card = f'<div class="card"><h3>Новый клиент</h3><span class="phone">{message.text}</span><a href="tel:{message.text}" class="btn-call">Позвонить</a></div>'
        updated = content.replace('<div id="feed">', f'<div id="feed">\n{new_card}')
        
        payload = {
            "message": "Test write",
            "content": base64.b64encode(updated.encode('utf-8')).decode('utf-8'),
            "sha": data['sha']
        }
        
        put_res = requests.put(url, json=payload, headers=headers)
        if put_res.status_code in [200, 201]:
            bot.reply_to(message, "🚀 ВСЁ ОК! Номер залетел на сайт. Значит, GitHub его не забанил (пока).")
        else:
            bot.reply_to(message, f"❌ Ошибка при записи: {put_res.status_code}")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка кода: {str(e)}")

if __name__ == "__main__":
    app.run()
