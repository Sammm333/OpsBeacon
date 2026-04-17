import os
import json
import urllib3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Fetch configuration from Environment Variables
TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
# Now fetching URL from environment variables for security
DEPLOYKIT_URL = os.environ.get('DEPLOYKIT_URL')

http = urllib3.PoolManager(timeout=5.0)

def check_deploykit_status():
    if not DEPLOYKIT_URL:
        return "⚠️ DEPLOYKIT_URL is not configured in Lambda environment."
    
    try:
        response = http.request('GET', DEPLOYKIT_URL)
        if response.status == 200:
            return "🟢 *DeployKIT Status*\n\n✅ Online and reachable."
        return f"⚠️ *DeployKIT Status*\n\nWarning: Server returned {response.status}"
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return "🔴 *DeployKIT Status*\n\nOffline: Connection refused or timed out."

def lambda_handler(event, context):
    logger.info(f"Incoming Event: {json.dumps(event)}")
    
    if not TOKEN or not CHAT_ID:
        return {"statusCode": 500, "body": "Configuration missing"}
    
    try:
        text_to_send = None

        # 1. Automated Alerts (SNS)
        if 'Records' in event and 'Sns' in event['Records'][0]:
            sns_data = event['Records'][0]['Sns']
            text_to_send = f"🚨 *{sns_data.get('Subject', 'Alert')}*\n\n{sns_data.get('Message')}"
        
        # 2. Manual Commands (Telegram Webhook)
        elif 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            message_obj = body.get('message', {})
            
            # Security: Verify that the message is from YOU
            sender_id = str(message_obj.get('from', {}).get('id'))
            if sender_id != str(CHAT_ID):
                logger.warning(f"Unauthorized access attempt from user: {sender_id}")
                return {"statusCode": 200, "body": "Unauthorized"}

            user_text = message_obj.get('text', '').strip().lower()

            if user_text == "/status":
                text_to_send = check_deploykit_status()
            elif user_text == "/start":
                text_to_send = "OpsBeacon active. Use /status to monitor DeployKIT."
            else:
                text_to_send = f"✅ Received: {user_text}\nType /status to check health."

        if text_to_send:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": text_to_send, "parse_mode": "Markdown"}
            
            http.request('POST', url, 
                         body=json.dumps(payload).encode('utf-8'), 
                         headers={'Content-Type': 'application/json'})

        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {"statusCode": 500, "body": str(e)}