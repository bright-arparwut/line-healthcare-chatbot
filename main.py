from pyngrok import ngrok
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, Request, Response, status
from typing import List, Optional
from dotenv import load_dotenv
import logging
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    api_response
)
import os
load_dotenv()

# Add these missing environment variable definitions
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print("🔴 ERROR: Please set your LINE Channel Access Token and Channel Secret.")

app = FastAPI()
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("line-chatbot")


@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body_bytes = await request.body()
    body = body_bytes.decode('utf-8')
    logger.info(f"Received body: {body}")
    logger.info(f"Received signature: {signature}")
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        return Response(content="Invalid signature", status_code=status.HTTP_400_BAD_REQUEST)
    
    return Response(content="OK", status_code=status.HTTP_200_OK)

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent):
    logger.info(f"Event: {event}")
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            reply_message_request = ReplyMessageRequest(
                reply_token = event.reply_token,
                messages = [
                    TextMessage(
                        text = f"{event.message.text} - reply from server!!"
                        )
                ]
            )
            api_response = line_bot_api.reply_message(reply_message_request = reply_message_request)
            logger.info(f"Reply message sent: {api_response}")
        except Exception as e:
            logger.error(f"Error replying to message: {e}")
    

if __name__ == "__main__":
    try:
        ngrok_tunnel = ngrok.connect(8000)
        webhook_url = ngrok_tunnel.public_url + '/callback'
        print(f"🌐 ngrok tunnel active: {ngrok_tunnel.public_url}")
        print(f"🔗 LINE Webhook URL: {webhook_url}")
        print("📋 Copy this URL to your LINE Developer Console webhook settings.")
    except Exception as e:
        print(f"🔴 Could not start ngrok: {e}")
        print("Proceeding without ngrok. You'll need to expose port 8000 manually.")

    print("🚀 Starting FastAPI server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)