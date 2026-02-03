import telebot
import requests
import base64
from datetime import datetime

# Все данные уже вшиты:
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
REPO = "Metaimperiya/kyiv-base"
# Внимание: для записи на GitHub боту всё равно нужен доступ. 
# Если ты ещё не сделал Personal Access Token (PAT), бот выдаст ошибку "401".
GH_TOKEN = "ЗАМЕНИ_ЭТО_НА_СВОЙ_TOKEN_ЕСЛИ_ЕЩЕ_НЕ_СДЕЛАЛ" 

bot = telebot.TeleBot(TOKEN)

def update_github_site(phone, desc):
    url = f"https://api.github.com/repos/{REPO}/contents/index.html"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. Запрашиваем файл с Гитхаба
    r = requests.get(url, headers=headers)
    if r.status_code != 200: return f"Ошибка Гитхаба: {r.status_code}"
    
    data = r.json()
    content = base64.b64decode(data['content']).decode('utf-8')
    sha = data['sha']
    
    # 2. Формируем новую карточку
    date_str = datetime.now().strftime("%d.%m %H:%M")
    new_card = f"""
        <div class="card">
            <div class="card-meta"><span>📅 {date_str}</span></div>
            <h3>{desc}</h3>
            <span class="phone">{phone}</span>
            <a href="tel:{phone}" class="btn-call">Зателефонувати</a>
        </div>"""
    
    # 3. Вставляем карточку после <div id="feed">
    if '<div id="feed">' in content:
        new_content = content.replace('<div id="feed">', '<div id="feed">' + new_card)
    else:
        new_content = content + new_card # если тег не найден
        
    # 4. Сохраняем обратно
    payload = {
        "message": f"Добавлен номер {phone}",
        "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🚀 KYIV SYSTEM READY.\nПиши: [номер] [описание]\nПример: 0931112233 Маникюр Оля")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    parts = message.text.split(' ', 1)
    phone = parts[0]
    desc = parts[1] if len(parts) > 1 else "Без описания"
    
    bot.send_message(message.chat.id, "⏳ Сохраняю в базу на GitHub...")
    
    status = update_github_site(phone, desc)
    
    if status == 200 or status == 201:
        bot.send_message(message.chat.id, f"✅ Готово! Номер {phone} уже на сайте.")
    else:
        bot.send_message(message.chat.id, f"❌ Не удалось сохранить. Ошибка: {status}\nПроверь GitHub Token!")

bot.polling(none_stop=True)
