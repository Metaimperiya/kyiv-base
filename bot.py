import telebot
import requests
import base64
from datetime import datetime

# ТВОИ ДАННЫЕ
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
GH_TOKEN = "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"
REPO = "Metaimperiya/kyiv-base"

bot = telebot.TeleBot(TOKEN)

def update_github_site(phone, desc):
    url = f"https://api.github.com/repos/{REPO}/contents/index.html"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. Получаем текущий index.html
    r = requests.get(url, headers=headers)
    if r.status_code != 200: return f"Ошибка: {r.status_code}"
    
    data = r.json()
    content = base64.b64decode(data['content']).decode('utf-8')
    sha = data['sha']
    
    # 2. Создаем новую карточку (дизайн под CRM)
    date_str = datetime.now().strftime("%d.%m %H:%M")
    new_card = f"""
        <div class="card">
            <div class="card-meta"><span>📅 {date_str}</span></div>
            <h3>{desc}</h3>
            <span class="phone">{phone}</span>
            <a href="tel:{phone}" class="btn-call">Зателефонувати</a>
        </div>"""
    
    # 3. Вставляем карточку в начало ленты
    if '<div id="feed">' in content:
        new_content = content.replace('<div id="feed">', '<div id="feed">' + new_card)
    else:
        new_content = content + new_card
        
    # 4. Отправляем обновление на GitHub
    payload = {
        "message": f"Добавлен контакт: {phone}",
        "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🚀 СИСТЕМА KYIV-BASE ГОТОВА.\nПришли номер и описание (например: 0930001122 Маникюр)")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    try:
        parts = message.text.split(' ', 1)
        phone = parts[0]
        desc = parts[1] if len(parts) > 1 else "Без опису"
        
        bot.send_message(message.chat.id, "⏳ Записую в базу на сайт...")
        status = update_github_site(phone, desc)
        
        if status in [200, 201]:
            bot.send_message(message.chat.id, f"✅ Успішно! Номер {phone} вже на сайті.")
        else:
            bot.send_message(message.chat.id, f"❌ Помилка GitHub: {status}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Упс: {e}")

bot.polling(none_stop=True)
