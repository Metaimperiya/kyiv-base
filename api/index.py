import telebot, requests, base64, os
from flask import Flask, request
from datetime import datetime

# --- НАСТРОЙКИ ---
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
REPO = "Metaimperiya/kyiv-base"
GH_TOKEN = os.getenv("GH_TOKEN") # Берется из Environment Variables в Vercel

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        try:
            update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
            bot.process_new_updates([update])
        except Exception as e:
            print(f"Ошибка: {e}")
    return 'CRM OK', 200

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        # 1. Путь к твоему сайту на GitHub
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        headers = {
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # 2. Получаем текущее содержимое сайта
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            bot.reply_to(message, f"❌ Ошибка GitHub: {res.status_code}. Проверь файл index.html в корне!")
            return

        data = res.json()
        sha = data['sha']
        content = base64.b64decode(data['content']).decode('utf-8')

        # 3. Создаем карточку клиента
        text = message.text.strip()
        time_now = datetime.now().strftime("%H:%M")
        
        # HTML-код карточки, который добавится на сайт
        card = f"""
        <div class="card">
            <h3>Новая заявка</h3>
            <span class="phone">{text}</span>
            <a href="tel:{text}" class="btn-call">📞 ПОЗВОНИТЬ</a>
            <div class="time">{time_now}</div>
        </div>"""

        # 4. Вставляем новую карточку в блок <div id="feed">
        if '<div id="feed">' in content:
            updated_html = content.replace('<div id="feed">', f'<div id="feed">{card}')
        else:
            updated_html = content.replace('</body>', f'{card}</body>')

        # 5. Отправляем обновленный файл обратно на GitHub
        payload = {
            "message": f"Добавлен номер {text}",
            "content": base64.b64encode(updated_html.encode('utf-8')).decode('utf-8'),
            "sha": sha
        }
        
        put_res = requests.put(url, json=payload, headers=headers)
        
        if put_res.status_code in [200, 201]:
            bot.reply_to(message, f"✅ Номер {text} добавлен на сайт!")
        else:
            bot.reply_to(message, f"❌ Ошибка сохранения: {put_res.status_code}")

    except Exception as e:
        bot.reply_to(message, f"🔥 Ошибка в коде: {str(e)}")

if __name__ == "__main__":
    app.run()
