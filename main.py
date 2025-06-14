from fastapi import FastAPI, Request # FastAPIのインポート
from linebot import LineBotApi, WebhookHandler # LINE Bot APIのインポート
from linebot.exceptions import InvalidSignatureError # 署名検証エラーのインポート
from linebot.models import MessageEvent, TextMessage, TextSendMessage # LINEのメッセージイベントとテキストメッセージのインポート
from dotenv import load_dotenv # .envファイルから環境変数を読み込むためのライブラリ

import os # 環境変数の読み込み
import uvicorn # Uvicornサーバーの起動用ライブラリ
import pandas as pd # データフレーム操作のためのライブラリ
import service as s

load_dotenv() 

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")# 環境変数からLINEのチャンネルシークレットを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")# 環境変数からLINEのチャンネルアクセストークンを取得
RAKUTEN_API_KEY = os.getenv("RAKUTEN_API_KEY")


app = FastAPI() 

# .envファイルから環境変数を読み込む
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
    import re

    user_message = event.message.text
    print(f"User message: {user_message}")

    # 入力例: 主菜:鶏肉 副菜:サラダ 使わない:卵
    main = sub = exclude = ""
    m = re.search(r"主菜[:：]([^\s]+)", user_message)
    s_ = re.search(r"副菜[:：]([^\s]+)", user_message)
    e = re.search(r"使わない[:：]([^\s]+)", user_message)
    if m:
        main = m.group(1)
    if s_:
        sub = s_.group(1)
    if e:
        exclude = e.group(1)

    # ユーザーIDを取得
    line_user_id = event.source.user_id
    user_res = s.supabase.table("users").select("id").eq("line_user_id", line_user_id).execute()

    if not user_res.data:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ユーザーが登録されていません"))
        return

    user_id = user_res.data[0]["id"]

    # レシピ検索処理
    recipe_text, recipe_id = s.get_recipe_by_category(main, sub, exclude, RAKUTEN_API_KEY)

    if recipe_id:
        # 中間テーブルに保存
        s.supabase.table("user_recipe").insert({
            "user_id": user_id,
            "recipe_id": recipe_id
        }).execute()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=recipe_text)
    )

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=8000)