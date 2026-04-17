import os
import json
import urllib3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

http = urllib3.PoolManager()

def lambda_handler(event, context):
    logger.info(f"Full event received: {json.dumps(event)}")
    
    if not TOKEN or not CHAT_ID:
        logger.error("Security Alert: Telegram Credentials Missing in Environment Variables")
        return {"statusCode": 500, "body": "Configuration Error"}
    
    try:
        if 'Records' in event and 'Sns' in event['Records'][0]:
            sns_data = event['Records'][0]['Sns']
            subject = sns_data.get("Subject", "OpsBeacon Alert")
            message = sns_data.get('Message', 'No message content')
            text_to_send = f"🚨 *{subject}*\n\n{message}"
        
        elif 'body' in event:
            raw_body = event['body']
            body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
            
            user_text = body.get('message', {}).get('text', 'No text found')
            text_to_send = f"✅ *OpsBeacon Online*\n\nЯ получил твое сообщение: {user_text}"
        
        else:
            logger.warning("Event format not recognized")
            return {"statusCode": 200, "body": "Unknown format"}

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text_to_send,
            "parse_mode": "Markdown"
        }

        encoded_data = json.dumps(payload).encode('utf-8')
        res = http.request(
            'POST', url, 
            body=encoded_data, 
            headers={'Content-Type': 'application/json'}
        )

        logger.info(f"Telegram response: {res.data.decode('utf-8')}")
        return {"statusCode": 200, "body": "Success"}

    except Exception as e:
        logger.error(f"Critical Error: {str(e)}")
        return {"statusCode": 500, "body": str(e)}