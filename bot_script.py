import telebot
import requests
import base64

# --- НАСТРОЙКИ (ЗАПОЛНИ СВОИ) ---
TOKEN = 'ВАШ_ТЕЛЕГРАМ_ТОКЕН'
GH_TOKEN = 'ВАШ_GITHUB_PAT'
REPO = 'ВАШ_ЛОГИН/kyiv-base'
FILE_PATH = 'numbers.txt'

bot = telebot.TeleBot(TOKEN)

def save_to_github(new_data):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Пытаемся получить файл
    r = requests.get(url, headers=headers)
    sha = None
    old_content = ""
    
    if r.status_code == 200:
        file_data = r.json()
        sha = file_data['sha']
        # Декодируем старое содержимое
        old_content = base64.b64decode(file_data['content']).decode('utf-8')
    
    # 2. Добавляем новую строку (номер)
    updated_content = old_content + f"{new_data}\n"
    encoded = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
    
    # 3. Отправляем обновление в GitHub
    payload = {
        "message": f"Добавлен номер: {new_data}",
        "content": encoded
    }
    if sha:
        payload["sha"] = sha
    
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🦾 СИСТЕМА KYIV BASE АКТИВНА\nОтправь мне номер телефона для записи в базу.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    # Отправляем фидбек пользователю, что мы работаем
    msg = bot.reply_to(message, "⏳ Записываю в реестр GitHub...")
    
    status = save_to_github(message.text)
    
    if status in [200, 201]:
        bot.edit_message_text(f"✅ Контакт `{message.text}` успешно внесен в базу.", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text(f"❌ Ошибка доступа к GitHub (Код: {status})", chat_id=message.chat.id, message_id=msg.message_id)

if __name__ == "__main__":
    print("Бот запущен и ждет сообщений...")
    bot.infinity_polling()
