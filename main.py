from fastapi import FastAPI, Request # FastAPIのインポートMore actions
from linebot import LineBotApi, WebhookHandler # LINE Bot APIのインポート
from linebot.exceptions import InvalidSignatureError # 署名検証エラーのインポート
from linebot.models import MessageEvent, TextMessage, TextSendMessage # LINEのメッセージイベントとテキストメッセージのインポート
from dotenv import load_dotenv # .envファイルから環境変数を読み込むためのライブラリ
from basemodel import RecipeCreate
from supabase import create_client, Client # Supabaseのクライアントを作成するためのライブラリ
from pydantic import BaseModel # PydanticのBaseModelをインポート

import os # 環境変数の読み込み
import uvicorn # Uvicornサーバーの起動用ライブラリ
import pandas as pd # データフレーム操作のためのライブラリ
import service as s
import re

load_dotenv() 

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")# 環境変数からLINEのチャンネルシークレットを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")# 環境変数からLINEのチャンネルアクセストークンを取得
RAKUTEN_API_KEY = os.getenv("RAKUTEN_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_API_URL = os.getenv("DIFY_API_URL")



app = FastAPI() 

# .envファイルから環境変数を読み込む
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# LINE Bot の API と Webhook ハンドラの設定

# ルート確認用エンドポイント
@app.get("/")
def read_root():
    return {"message": "Cooking Bot is running!"}

# Webhookのエンドポイント
@app.post("/webhook")
async def callback(request: Request): # Webhookのリクエストを受け取るエンドポイント
    # リクエストヘッダーから署名検証
    signature = request.headers['X-Line-Signature']# X-Line-Signatureヘッダーから署名を取得

    # リクエストボディの取得
    body = await request.body()#
    body = body.decode("utf-8") # バイト列を文字列にデコード

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
    # Redelivery（再送信）イベントを無視する
    if hasattr(event, "delivery_context") and getattr(event.delivery_context, "is_redelivery", False):
        print("⚠️ Redeliveryイベントのためスキップします")
        return

    if event.source.type == "user":
        user_id = event.source.user_id
    else:
        user_id = "unknown"

    user_message = event.message.text
    print(f"User message: {user_message}")
    print(f"User ID: {user_id}")

    # ① 楽天APIからレシピ取得
    recipe_url = s.get_recipe_by_category(user_message, RAKUTEN_API_KEY)

    # ② なければDifyで生成
    if recipe_url is None:
        generated_response = s.generate_recipe_with_dify(user_message, DIFY_API_URL, DIFY_API_KEY)

        # URLを含んでいるか？
        urls = re.findall(r'https?://\S+', generated_response)
        recipe_url = urls[0] if urls else None
        reply_text = recipe_url if recipe_url else generated_response
    else:
        reply_text = recipe_url

    # ④ Supabaseに保存
    if recipe_url and user_id != "unknown":
        recipe_data = RecipeCreate(user_id=user_id, food_name=user_message, url=recipe_url)
        supabase.table("recipes").insert(recipe_data.model_dump()).execute()

    # ⑤ LINEに返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)