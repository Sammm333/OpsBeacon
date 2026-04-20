import os
import json
import urllib3
import logging
from urllib3.util import Timeout

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
DEPLOYKIT_URL = os.environ.get('DEPLOYKIT_URL')

http = urllib3.PoolManager()

def check_deploykit_status():
    if not DEPLOYKIT_URL:
        return "⚠️ DEPLOYKIT_URL is not configured."
    
    # Strict 3-second timeout to prevent Lambda hang
    t = Timeout(connect=3.0, read=3.0)
    
    try:
        # We use 'HEAD' instead of 'GET' to be faster and save bandwidth
        response = http.request('HEAD', DEPLOYKIT_URL, retries=False, timeout=t)
        
        if response.status == 200:
            return "🟢 *DeployKIT Status*\n\n✅ Online and reachable."
        return f"⚠️ *DeployKIT Status*\n\nWarning: Code {response.status}"

    except Exception:
        # This triggers when the Elastic IP doesn't respond (Server Stopped)
        return "🔴 *DeployKIT Status*\n\n*Status:* Stopped or Turned Off"

def lambda_handler(event, context):
    if not TOKEN or not CHAT_ID:
        return {"statusCode": 500, "body": "Config Error"}

    try:
        text_to_send = None
        reply_markup = None

        # A. GitHub Actions / SNS Alerts
        if 'Records' in event:
            sns = event['Records'][0]['Sns']
            text_to_send = f"🚨 *{sns.get('Subject')}*\n\n{sns.get('Message')}"
        
        # B. Telegram Commands
        elif 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            msg = body.get('message', {})
            
            if str(msg.get('from', {}).get('id')) != str(CHAT_ID):
                return {"statusCode": 200}

            cmd = msg.get('text', '').strip().lower()

            if cmd == "/status":
                text_to_send = check_deploykit_status()
            
            elif cmd == "/resource":
                text_to_send = "📂 *Project Resources*\n\nSource code and docs:"
                reply_markup = {
                    "inline_keyboard": [[
                        {"text": "🔗 View on GitHub", "url": "https://github.com/Sammm333/OpsBeacon.git"}
                    ]]
                }
            
            elif cmd == "/start":
                text_to_send = "🚀 *OpsBeacon Active*\n/status - Check EC2\n/resource - Code link"

        # C. Send Response
        if text_to_send:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": text_to_send, "parse_mode": "Markdown"}
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            http.request('POST', url, body=json.dumps(payload).encode('utf-8'), 
                         headers={'Content-Type': 'application/json'}, timeout=5.0)

        return {"statusCode": 200, "body": "OK"}
    except Exception as e:
        logger.error(str(e))
        return {"statusCode": 200}