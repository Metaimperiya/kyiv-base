import telebot
import os

# Твой токен
TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "KYIV DATABASE BOT АКТИВИРОВАН 🚀\nКидай номер и описание через пробел (например: 0931234567 Маникюр Оля)")

@bot.message_handler(content_types=['text'])
def save_contact(message):
    # Логика: берем текст, делим на номер и описание
    data = message.text.split(' ', 1)
    phone = data[0]
    desc = data[1] if len(data) > 1 else "Без описания"
    
    # Ответ пользователю
    response = f"✅ ПРИНЯТО В БАЗУ:\n📞 Номер: {phone}\n📝 Инфо: {desc}"
    bot.send_message(message.chat.id, response)
    
    # ТУТ БУДЕТ КОД ЗАПИСИ В INDEX.HTML (сделаем следующим шагом)

if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
