import telebot
import requests
import base64
from flask import Flask, request
import json

TOKEN = "8410156942:AAF0Si5lojhItnQREdC2rbW_N-NuWolcwJw"
REPO = "Metaimperiya/kyiv-base"
GH_TOKEN = "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"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# 🔧 НАСТРОЙКИ GITHUB API
GITHUB_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",  # ОБЯЗАТЕЛЬНО
    "User-Agent": "KYIV-BOT"
}

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'CRM работает! <a href="/debug">Debug</a>', 200

# 🔧 ДЕБАГ ЭНДПОИНТ
@app.route('/debug')
def debug():
    """Проверка подключения"""
    test_url = f"https://api.github.com/repos/{REPO}"
    res = requests.get(test_url, headers=GITHUB_HEADERS)
    
    return f"""
    <h2>Debug GitHub API</h2>
    <p>Token start: {GH_TOKEN[:20]}...</p>
    <p>Status: <strong>{res.status_code}</strong></p>
    <p>Response: {res.text[:500] if res.status_code != 200 else '✅ OK'}</p>
    <p>Headers used: {json.dumps(GITHUB_HEADERS, indent=2)}</p>
    """

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    try:
        bot.reply_to(message, "⏳ Проверяю доступ к GitHub...")
        
        # Сначала проверяем доступ
        test_url = f"https://api.github.com/repos/{REPO}"
        test_res = requests.get(test_url, headers=GITHUB_HEADERS)
        
        if test_res.status_code == 401:
            bot.reply_to(message, "❌ GitHub: 401 Unauthorized. Токен недействителен!")
            return
        elif test_res.status_code == 403:
            bot.reply_to(message, "❌ GitHub: 403 Forbidden. Нет прав к репозиторию!")
            bot.reply_to(message, f"Подробности: {test_res.text[:200]}")
            return
        elif test_res.status_code == 404:
            bot.reply_to(message, f"❌ Репозиторий {REPO} не найден!")
            return
        elif test_res.status_code != 200:
            bot.reply_to(message, f"❌ GitHub ошибка {test_res.status_code}")
            return
        
        # Теперь работаем с файлом
        parts = message.text.strip().split(' ', 1)
        phone = parts[0].strip()
        desc = parts[1] if len(parts) > 1 else "Новый контакт"
        
        bot.reply_to(message, f"✅ GitHub доступ есть! Записываю {phone}...")
        
        # 1. Получаем index.html
        url = f"https://api.github.com/repos/{REPO}/contents/index.html"
        get_res = requests.get(url, headers=GITHUB_HEADERS)
        
        if get_res.status_code != 200:
            bot.reply_to(message, f"❌ Не могу получить файл: {get_res.status_code}")
            return
            
        file_data = get_res.json()
        
        # 2. Декодируем
        try:
            content = base64.b64decode(file_data['content']).decode('utf-8')
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка декодирования: {e}")
            return
        
        # 3. Добавляем карточку
        new_card = f'''<div class="card">
    <h3>{desc}</h3>
    <span class="phone">{phone}</span>
    <a href="tel:{phone}" class="btn-call">Позвонить</a>
</div>'''
        
        # Ищем где вставить
        if '<div id="feed">' in content:
            updated = content.replace('<div id="feed">', f'<div id="feed">\n{new_card}')
        else:
            # Попробуем найти body и вставить перед закрывающим
            updated = content.replace('</body>', f'{new_card}\n</body>')
        
        # 4. Отправляем обновление
        payload = {
            "message": f"Добавлен контакт: {phone}",
            "content": base64.b64encode(updated.encode('utf-8')).decode('utf-8'),
            "sha": file_data['sha'],
            "branch": "main"
        }
        
        put_res = requests.put(url, json=payload, headers=GITHUB_HEADERS)
        
        if put_res.status_code in [200, 201]:
            bot.reply_to(message, f"✅ Контакт добавлен!\n📞 {phone}\n🌐 https://kyiv-base.vercel.app/")
        else:
            error_text = put_res.text[:200] if put_res.text else "Нет деталей"
            bot.reply_to(message, f"❌ Ошибка записи {put_res.status_code}: {error_text}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Общая ошибка: {str(e)}")

if __name__ == "__main__":
    print("=== Запуск KYIV CRM ===")
    # Тестовый запрос
    test_url = f"https://api.github.com/repos/{REPO}"
    res = requests.get(test_url, headers=GITHUB_HEADERS)
    print(f"GitHub API статус: {res.status_code}")
    
    if res.status_code == 200:
        print("✅ GitHub доступен!")
    else:
        print(f"❌ GitHub недоступен: {res.text[:100]}")
    
    app.run(host='0.0.0.0', port=8080)
