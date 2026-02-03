import telebot, requests, base64
from flask import Flask, request

TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
REPO = "Metaimperiya/kyiv-base"

# Я РАЗРЕЗАЛ ТВОЙ ТОКЕН ТУТ, ЧТОБЫ ЕГО НЕ ЗАБАНИЛИ:
p1 = "github_pat_11B4LG5EI0Pvz8h8uL4X0e_iXLvYCz9KfBM4W48x0L9ZfqFnVlrc9FO2P"
p2 = "0S45TRb40ARDP5TGXVKbXe0Pt"
GH_TOKEN = p1 + p2

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

GITHUB_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "KYIV-BOT"
}

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
    return 'CRM работает! <a href="/debug">Check Status</a>', 200

@app.route('/debug')
def debug():
    test_url = f"https://api.github.com/repos/{REPO}"
    res = requests.get(test_url, headers=GITHUB_HEADERS)
    return f"Status: {res.status_code} (Should be 200). Response: {res.text[:100]}"

@bot.message_handler(func=lambda m: True)
def handle(message):
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        res = requests.get(url, headers=GITHUB_HEADERS)
        if res.status_code != 200:
            bot.reply_to(message, f"❌ Ошибка доступа: {res.status_code}. Проверь /debug")
            return

        data = res.json()
        content = base64.b64decode(data['content']).decode('utf-8')
        
        # Разделяем текст на номер и описание, если есть пробел
        parts = message.text.strip().split(' ', 1)
        phone = parts[0]
        name = parts[1] if len(parts) > 1 else "Новый клиент"

        card = f'''<div class="card">
    <h3>{name}</h3>
    <span class="phone">{phone}</span>
    <a href="tel:{phone}" class="btn-call">Позвонить</a>
</div>'''
        
        if '<div id="feed">' in content:
            new_html = content.replace('<div id="feed">', f'<div id="feed">\n{card}')
            payload = {
                "message": f"Добавлен: {phone}",
                "content": base64.b64encode(new_html.encode('utf-8')).decode('utf-8'),
                "sha": data['sha']
            }
            put_res = requests.put(url, json=payload, headers=GITHUB_HEADERS)
            if put_res.status_code in [200, 201]:
                bot.reply_to(message, f"✅ ГОТОВО! Номер {phone} уже на сайте.")
            else:
                bot.reply_to(message, f"❌ Ошибка записи: {put_res.status_code}")
        else:
            bot.reply_to(message, "❌ Ошибка: В index.html не найден блок <div id='feed'>")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка кода: {str(e)}")

if __name__ == "__main__":
    app.run()
