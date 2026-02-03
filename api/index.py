import telebot, requests, base64, os
from flask import Flask, request
from datetime import datetime

# --- НАСТРОЙКИ ---
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
REPO = "Metaimperiya/kyiv-base"
GH_TOKEN = os.getenv("GH_TOKEN") 

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/api', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        try:
            update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
            bot.process_new_updates([update])
        except Exception as e:
            print(f"Ошибка вебхука: {e}")
    return 'Бот активен.', 200

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        # ИСПРАВЛЕНО: теперь ищем index.html
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        headers = {
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            bot.reply_to(message, f"❌ Ошибка: файл index.html не найден (Код {res.status_code})")
            return

        data = res.json()
        sha = data['sha']
        content = base64.b64decode(data['content']).decode('utf-8')

        text = message.text.strip()
        time_now = datetime.now().strftime("%H:%M")
        
        new_card = f"""
        <div class="card">
            <h3>Новый контакт</h3>
            <span class="phone">{text}</span>
            <a href="tel:{text}" class="btn-call">📞 ПОЗВОНИТЬ</a>
            <div class="time">{time_now}</div>
        </div>"""

        if '<div id="feed">' in content:
            updated_content = content.replace('<div id="feed">', f'<div id="feed">{new_card}')
        else:
            updated_content = content.replace('</body>', f'{new_card}</body>')

        payload = {
            "message": f"Добавлен контакт {text}",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": sha
        }
        
        put_res = requests.put(url, json=payload, headers=headers)
        
        if put_res.status_code in [200, 201]:
            bot.reply_to(message, f"✅ Контакт добавлен на сайт!")
        else:
            bot.reply_to(message, f"❌ Ошибка записи GitHub: {put_res.status_code}")

    except Exception as e:
        bot.reply_to(message, f"🔥 Ошибка: {str(e)}")

if __name__ == "__main__":
    app.run()
