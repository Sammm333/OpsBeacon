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
        sns_data = event['Records'][0]['Sns']
        subject = sns_data.get("Subject", "OpsBeacon Alert")
        message = sns_data.get('Message', 'No message content')

        formatted_text = f"🚨 *{subject}*\n\n{message}"

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": formatted_text,
            "parse_mode": "Markdown"
        }

        encoded_data = json.dumps(payload).encode('utf-8')
        response = http.request(
            'POST',
            url,
            body=encoded_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status != 200:
            logger.error(f"Telegram API error: {response.data.decode('utf-8')}")
            return {"statusCode": response.status, "body": "API Error"}
        
        logger.info("Alert sent successfully")
        return {"statusCode": 200, "body": "Alert Sent"}
        
    except Exception as e:
        logger.error(f"Process Error: {str(e)}")
        return {"statusCode": 500, "body": "Internal Server Error"}