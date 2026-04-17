# 🔦 OpsBeacon

> **A serverless DevOps monitoring and notification gateway — turning Telegram into your personal operations center.**

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900?style=flat-square&logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 📖 Overview

OpsBeacon is a **serverless monitoring and notification bridge** built on AWS Lambda. It solves a real DevOps problem: developers shouldn't have to constantly check AWS consoles or the GitHub Actions tab to know what's happening with their infrastructure.

By connecting **AWS CloudWatch**, **GitHub Actions**, and a **Telegram Bot** through a single Lambda function, OpsBeacon gives you a real-time operations feed directly in your pocket — with zero infrastructure to maintain.

```
  [ GitHub Actions ]  ──────────────────────────────────────────┐
                                                                 ▼
  [ AWS CloudWatch ] ──► [ AWS SNS ] ──► [ AWS Lambda ] ──► [ Telegram ]
                                              ▲
  [ You (Telegram /status) ] ────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🟢 **Instant Status Checks** | Query your live environment health on demand via `/status` |
| 🚨 **Automated Alerts** | Receive critical AWS CloudWatch and SNS alarms directly to Telegram |
| 📦 **Deployment Notifications** | GitHub Actions notifies you the moment a deployment finishes |
| 🛡️ **Identity Guard** | Strict sender ID verification — only you can trigger the Lambda |
| ☁️ **100% Serverless** | Built on AWS Lambda with Function URLs — no servers to manage |
| 💸 **Zero Idle Cost** | Runs completely within AWS Free Tier for personal use |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Compute** | AWS Lambda (Python 3.12) |
| **Monitoring** | AWS CloudWatch, AWS SNS |
| **CI/CD** | GitHub Actions |
| **Notification** | Telegram Bot API (Webhooks) |
| **HTTP** | urllib3 (lightweight, no external deps) |

---

## 🏗️ Architecture

OpsBeacon operates in three distinct modes:

### 1. 🟢 Active Monitoring (On-Demand)
You send `/status` in Telegram → Telegram sends a webhook to Lambda Function URL → Lambda pings your `DEPLOYKIT_URL` → Lambda replies with live status.

### 2. 🚨 Passive Monitoring (Automated Alerts)
AWS CloudWatch detects a threshold breach → CloudWatch triggers an SNS Topic → SNS invokes Lambda → Lambda formats and forwards the alert to your Telegram.

### 3. 🚀 Deployment Awareness (CI/CD)
You push code to GitHub → GitHub Actions runs your deploy pipeline → On success, a `curl` call sends a "Deployment Finished ✅" message directly to your Telegram via the Bot API.

---

## 📁 Project Structure

```
OpsBeacon/
├── lambda_function.py          # Core Lambda handler (main brain)
└── .github/
    └── workflows/
        └── deploy.yml          # GitHub Actions CI/CD pipeline
```

---

## 🚀 Setup & Installation

### Prerequisites
- An AWS Account
- A GitHub repository for your project
- A Telegram account

---

### Step 1 — Create Your Telegram Bot

1. Open Telegram and message **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot` and follow the prompts.
3. Copy the **`TOKEN`** BotFather gives you.
4. Send your new bot any message (to initialize the chat).
5. Visit this URL to find your `CHAT_ID`:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   Look for `"id"` inside the `"from"` object in the JSON response.

---

### Step 2 — Deploy the Lambda Function

1. Go to **AWS Console → Lambda → Create function**.
2. Select **Python 3.12** runtime.
3. Paste the contents of `lambda_function.py` into the inline editor.
4. Under **Configuration → Function URL**, click **Create function URL**.
   - Auth type: **NONE** (Telegram webhook requires a public URL)
5. Under **Configuration → Environment variables**, add:

   | Key | Value |
   |---|---|
   | `TOKEN` | Your Telegram Bot Token |
   | `CHAT_ID` | Your personal Telegram User ID |
   | `DEPLOYKIT_URL` | The HTTP endpoint of your monitored project |

6. Save the **Function URL** — you'll need it in the next step.

---

### Step 3 — Register the Telegram Webhook

Paste the following URL into your browser (replace placeholders with real values):

```
https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=<YOUR_LAMBDA_FUNCTION_URL>&drop_pending_updates=true
```

You should see `{"ok":true,"result":true}`. Telegram will now forward every bot message to your Lambda.

---

### Step 4 — Configure GitHub Actions (CI/CD)

Add the following step to the **end** of your `.github/workflows/deploy.yml`:

```yaml
- name: Notify Telegram on Success
  if: success()
  env:
    TELEGRAM_TOKEN: ${{ secrets.TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.CHAT_ID }}
  run: |
    curl -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}&text=🚀 *Deployment Finished!*%0A%0AProject: *OpsBeacon*%0AStatus: Success ✅&parse_mode=Markdown"
```

Then, in your GitHub repository go to **Settings → Secrets and variables → Actions** and add:
- `TOKEN` — your Telegram Bot Token
- `CHAT_ID` — your Telegram User ID

---

### Step 5 — (Optional) CloudWatch Alarm Integration

To receive automated infrastructure alerts:

1. Go to **AWS CloudWatch → Alarms → Create alarm**.
2. Select a metric (e.g., EC2 CPUUtilization > 80%).
3. Under **Actions**, add an **SNS notification**.
4. Create or select an SNS Topic.
5. Subscribe your **Lambda function** to that SNS topic.

When the alarm fires, CloudWatch → SNS → Lambda → Telegram automatically.

---

## 💻 Core Lambda Code

```python
import os
import json
import urllib3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
DEPLOYKIT_URL = os.environ.get('DEPLOYKIT_URL')

http = urllib3.PoolManager(timeout=5.0)

def check_status():
    if not DEPLOYKIT_URL:
        return "⚠️ DEPLOYKIT_URL environment variable is missing."
    try:
        response = http.request('GET', DEPLOYKIT_URL)
        if response.status == 200:
            return "🟢 *DeployKIT Status*\n\n✅ Online and reachable."
        return f"⚠️ *DeployKIT Status*\n\nServer returned code: {response.status}"
    except Exception:
        return "🔴 *DeployKIT Status*\n\nOffline: Connection timed out."

def lambda_handler(event, context):
    if not TOKEN or not CHAT_ID:
        return {"statusCode": 500, "body": "Config Error"}

    try:
        message_text = None

        # Part A: Handle SNS / CloudWatch Alarms
        if 'Records' in event and 'Sns' in event['Records'][0]:
            sns = event['Records'][0]['Sns']
            message_text = f"🚨 *{sns.get('Subject', 'Alert')}*\n\n{sns.get('Message')}"

        # Part B: Handle Telegram Bot Commands
        elif 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            msg = body.get('message', {})

            # 🛡️ Identity Guard — reject unauthorized senders
            if str(msg.get('from', {}).get('id')) != str(CHAT_ID):
                return {"statusCode": 200, "body": "Unauthorized"}

            cmd = msg.get('text', '').strip().lower()
            if cmd == "/status":
                message_text = check_status()
            elif cmd == "/start":
                message_text = "OpsBeacon Online. Send /status to check health."

        # Part C: Send the message to Telegram
        if message_text:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message_text, "parse_mode": "Markdown"}
            http.request('POST', url, body=json.dumps(payload).encode('utf-8'),
                         headers={'Content-Type': 'application/json'})

        return {"statusCode": 200, "body": "OK"}
    except Exception as e:
        logger.error(str(e))
        return {"statusCode": 500, "body": "Error"}
```

---

## 🔐 Security

OpsBeacon uses a built-in **Identity Guard** to prevent unauthorized access:

- Every inbound Telegram message is validated against the `CHAT_ID` environment variable.
- If the `sender_id` doesn't match, the command is **silently ignored** and the Lambda returns `200 OK` (no error leakage).
- No secrets or tokens are ever hardcoded — all sensitive values are injected via **AWS Environment Variables** and **GitHub Secrets**.

---

## 🐛 Debugging & Observability

All Lambda executions are automatically logged to **AWS CloudWatch Logs**.

To view logs:
1. Go to **AWS Console → Lambda → OpsBeacon → Monitor → View CloudWatch Logs**.
2. Each invocation creates a log stream with full request details and any errors caught by the logger.

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository: [github.com/Sammm333/OpsBeacon](https://github.com/Sammm333/OpsBeacon)
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with ☁️ by **[@Sammm333](https://github.com/Sammm333)**

*Zero servers. Zero noise. Full visibility.*

</div>
