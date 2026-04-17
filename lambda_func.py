import os
import json
import urllib3
import logging

# Initialize logging for CloudWatch monitoring
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables configured in AWS Lambda
TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
# Replace with the public endpoint of your DeployKIT project
DEPLOYKIT_URL = "http://13.48.224.107:8000/"

# Use PoolManager for persistent connections and define request timeouts
http = urllib3.PoolManager(timeout=5.0)

def check_deploykit_status():
    """
    Performs a health check on the DeployKIT project endpoint.
    Returns a formatted string for Telegram.
    """
    try:
        response = http.request('GET', DEPLOYKIT_URL)
        if response.status == 200:
            return "🟢 *DeployKIT Status*\n\n✅ Online and reachable."
        else:
            return f"⚠️ *DeployKIT Status*\n\nWarning: Server returned status code {response.status}"
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return "🔴 *DeployKIT Status*\n\nOffline: Could not connect to the server."

def lambda_handler(event, context):
    """
    Main entry point for AWS Lambda. 
    Handles SNS notifications (Alerts) and API Gateway/Function URL requests (Commands).
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    if not TOKEN or not CHAT_ID:
        logger.error("Missing required environment variables: TOKEN or CHAT_ID")
        return {"statusCode": 500, "body": "Configuration Error"}
    
    try:
        text_to_send = None

        # Process SNS events (e.g., CloudWatch Alarms)
        if 'Records' in event and 'Sns' in event['Records'][0]:
            sns_data = event['Records'][0]['Sns']
            subject = sns_data.get("Subject", "OpsBeacon Alert")
            message = sns_data.get('Message', 'No message content')
            text_to_send = f"🚨 *{subject}*\n\n{message}"
        
        # Process incoming Telegram messages via Webhook
        elif 'body' in event:
            raw_body = event['body']
            body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
            
            message_obj = body.get('message', {})
            user_text = message_obj.get('text', '').strip().lower()

            # Command routing
            if user_text == "/status":
                text_to_send = check_deploykit_status()
            elif user_text == "/start":
                text_to_send = "Welcome to OpsBeacon. Use /status to check DeployKIT health."
            else:
                text_to_send = f"✅ Received: {user_text}\nUse /status for project health."
        
        # Guard clause for unrecognized event formats
        if not text_to_send:
            logger.warning("Unrecognized event format or empty message.")
            return {"statusCode": 200, "body": "No action taken"}

        # Telegram API request payload
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text_to_send,
            "parse_mode": "Markdown"
        }

        # Dispatch notification to Telegram
        encoded_data = json.dumps(payload).encode('utf-8')
        response = http.request(
            'POST', url, 
            body=encoded_data, 
            headers={'Content-Type': 'application/json'}
        )

        logger.info(f"Telegram response: {response.data.decode('utf-8')}")
        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        logger.error(f"Critical error in lambda_handler: {str(e)}")
        return {"statusCode": 500, "body": str(e)}