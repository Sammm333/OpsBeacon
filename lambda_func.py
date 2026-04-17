import os
import json
import urllib3
import logging
from urllib3.util import Timeout # КРИТИЧНО: Добавляем этот импорт

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
DEPLOYKIT_URL = os.environ.get('DEPLOYKIT_URL')

# Создаем менеджер пула
http = urllib3.PoolManager()

def check_deploykit_status():
    if not DEPLOYKIT_URL:
        return "⚠️ DEPLOYKIT_URL is not configured."
    
    # Ждем подключения 2 секунды. Если за 2с сервер не ответил, считаем его выключенным.
    # Это меньше, чем стандартный таймаут Lambda (3с), поэтому код успеет сработать.
    custom_timeout = Timeout(connect=2.0, read=3.0)
    
    try:
        response = http.request(
            'GET', 
            DEPLOYKIT_URL, 
            retries=False, # Не пытаемся повторно, если сервер упал
            timeout=custom_timeout
        )
        
        if response.status == 200:
            return "🟢 *DeployKIT Status*\n\n✅ Online and reachable."
        return f"⚠️ *DeployKIT Status*\n\nWarning: Server returned {response.status}"
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        # Теперь это сообщение точно дойдет до Telegram
        return "🔴 *DeployKIT Status*\n\n*Status:* Stopped or Turned Off"

def lambda_handler(event, context):
    if not TOKEN or not CHAT_ID:
        return {"statusCode": 500, "body": "Configuration missing"}
    
    try:
        text_to_send = None
        reply_markup = None

        # 1. Обработка команд из Telegram
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            message_obj = body.get('message', {})
            
            sender_id = str(message_obj.get('from', {}).get('id'))
            if sender_id != str(CHAT_ID):
                return {"statusCode": 200, "body": "Unauthorized"}

            user_text = message_obj.get('text', '').strip().lower()

            if user_text == "/status":
                text_to_send = check_deploykit_status()
            elif user_text == "/resource":
                text_to_send = "📂 *OpsBeacon Resources*"
                reply_markup = {"inline_keyboard": [[{"text": "🔗 GitHub", "url": "https://github.com/Sammm333/OpsBeacon.git"}]]}
            elif user_text == "/start":
                text_to_send = "🚀 OpsBeacon Active."

        # 2. Отправка сообщения
        if text_to_send:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": text_to_send, "parse_mode": "Markdown"}
            if reply_markup: payload["reply_markup"] = reply_markup
            
            # Отправляем ответ (с таймаутом на саму отправку)
            http.request('POST', url, body=json.dumps(payload).encode('utf-8'), 
                         headers={'Content-Type': 'application/json'}, timeout=5.0)

        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        return {"statusCode": 200, "body": "Error handled"}