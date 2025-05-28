from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

import os

load_dotenv() 

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

app = FastAPI()
# .envファイルから環境変数を読み込む
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
# FastAPI インスタンスの作成


# LINEのチャネルシークレットとアクセストークンを環境変数に設定してください
# LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
# LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# LINE Bot の API と Webhook ハンドラの設定

# ルート確認用エンドポイント
@app.get("/")
def read_root():
    return {"message": "Cooking Bot is running!"}

# Webhookのエンドポイント
@app.post("/webhook")
async def callback(request: Request):
    # リクエストヘッダーから署名検証
    signature = request.headers['X-Line-Signature']

    # リクエストボディの取得
    body = await request.body()
    body = body.decode("utf-8")

    print("Request body:", body)

    # 署名の確認
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel secret/access token.")
        return {"message": "Signature verification failed."}

    return {"message": "OK"}

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    print(f"User message: {user_message}")

    # LINEに返すメッセージの作成
    reply_message = f"あなたが送ったメッセージ: {user_message}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )