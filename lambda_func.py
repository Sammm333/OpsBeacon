import os
import json
import urllib3
import logging
from dotenv import load_dotenv

logger = logging.getLogger()
logger.setLevel(logging.INFO)

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

http = urllib3.PoolManager()

def lambda_handler(event, context):
    if not TOKEN or not CHAT_ID:
        logger.error("Security Alert: Telegram Credentials Missing")
        return {"statusCode": 500, "body": "Configuration Error"}
    
    try:
        if 'Records' in event and 'Sns' in event['Records'][0]:
            sns_data = event['Records'][0]['Sns']
            subject = sns_data.get("Subject", "OpsBeacon Alert")
            message = sns_data.get('Message', 'No message content')
            formatted_text = f"🚨 *{subject}*\n\n{message}"
        
        elif 'body' in event:
            body = json.loads(event['body'])
            user_text = body.get('message', {}).get('text', 'No text')
            formatted_text = f"✅ *OpsBeacon Online*\n\nЯ получил твое сообщение: {user_text}"
        
        else:
            logger.info("Unknown event format")
            return {"statusCode": 200, "body": "Unknown Event"}

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": formatted_text,
            "parse_mode": "Markdown"
        }

        encoded_data = json.dumps(payload).encode('utf-8')
        response = http.request(
            'POST', url, body=encoded_data,
            headers={'Content-Type': 'application/json'}
        )

        return {"statusCode": 200, "body": "OK"}
        
    except Exception as e:
        logger.error(f"Process Error: {str(e)}")
        return {"statusCode": 500, "body": "Error"}