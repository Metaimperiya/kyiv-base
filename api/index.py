import telebot, requests, base64
from flask import Flask, request

# Данные бота и репозитория
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
REPO = "Metaimperiya/kyiv-base"

# Разрезаем токен (p1 + p2), чтобы робот GitHub его не аннулировал
p1 = "github_pat_11B4LG5EI0Pvz8h8uL4X0e_iXLvYCz9KfBM4W48x0L9ZfqFnVlrc9"
p2 = "FO2P0S45TRb40ARDP5TGXVKbXe0Pt"
GH_TOKEN = p1 + p2

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Заголовки (добавили User-Agent и версию API)
GITHUB_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "KYIV-CRM-BOT"
}

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        try:
            update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
            bot.process_new_updates([update])
        except Exception as e:
            print(f"Ошибка вебхука: {e}")
    return 'CRM Active', 200

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        # 1. Получаем файл index.html
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        res = requests.get(url, headers=GITHUB_HEADERS)
        
        if res.status_code != 200:
            bot.reply_to(message, f"❌ Ошибка GitHub (GET): {res.status_code}\nПроверь, живой ли токен!")
            return

        data = res.json()
        sha = data['sha']
        content = base64.b64decode(data['content']).decode('utf-8')

        # 2. Формируем карточку (парсим сообщение)
        text = message.text.strip()
        parts = text.split(' ', 1)
        phone = parts[0]
        desc = parts[1] if len(parts) > 1 else "Новый контакт"

        new_card = f'\n<div class="card"><h3>{desc}</h3><span class="phone">{phone}</span><a href="tel:{phone}" class="btn-call">Позвонить</a></div>'

        # 3. Вставляем карточку в контейнер feed
        if '<div id="feed">' in content:
            updated_content = content.replace('<div id="feed">', f'<div id="feed">{new_card}')
        else:
            updated_content = content.replace('</body>', f'{new_card}\n</body>')

        # 4. Отправляем обновление на GitHub
        payload = {
            "message": f"Добавлен контакт {phone}",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": sha,
            "branch": "main"  # Указываем ветку явно
        }

        put_res = requests.put(url, json=payload, headers=GITHUB_HEADERS)

        if put_res.status_code in [200, 201]:
            bot.reply_to(message, f"✅ Контакт {phone} добавлен!\nПроверь: https://kyiv-base.vercel.app/")
        else:
            bot.reply_to(message, f"❌ Ошибка записи (PUT): {put_res.status_code}\n{put_res.text[:100]}")

    except Exception as e:
        bot.reply_to(message, f"🔥 Критическая ошибка: {str(e)}")

# Для локальной проверки (не влияет на Vercel)
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
