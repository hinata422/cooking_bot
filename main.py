from fastapi import FastAPI, Request # FastAPIのインポート
from linebot import LineBotApi, WebhookHandler # LINE Bot APIのインポート
from linebot.exceptions import InvalidSignatureError # 署名検証エラーのインポート
from linebot.models import MessageEvent, TextMessage, TextSendMessage # LINEのメッセージイベントとテキストメッセージのインポート
from dotenv import load_dotenv # .envファイルから環境変数を読み込むためのライブラリ

import os # 環境変数の読み込み
import uvicorn # Uvicornサーバーの起動用ライブラリ
import requests # HTTPリクエストを送るためのライブラリ
import pandas as pd # データフレーム操作のためのライブラリ
import json # JSONデータの操作のためのライブラリ
import time # 時間操作のためのライブラリ

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
    user_message = event.message.text
    print(f"User message: {user_message}")

    # LINEに返すメッセージの作成
    reply_message = f"あなたが送ったメッセージ: {user_message}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

if __name__ == "__main__":
    
    # Uvicornサーバーを起動
    uvicorn.run(app, host="0.0.0.0", port=8000)
# uvicorn main:app --reload
# で実行可能


def get_recipe_by_category(user_message):
    parent_dict = {}
    
    res = requests.get(
        'https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426',
        params={'applicationId': RAKUTEN_API_KEY}
    )
    json_data = json.loads(res.text)

    df = pd.DataFrame(columns=['category1', 'category2', 'category3', 'categoryId', 'categoryName'])

    # 大カテゴリ
    for category in json_data['result']['large']:
        df = df.append({
            'category1': category['categoryId'],
            'category2': "",
            'category3': "",
            'categoryId': category['categoryId'],
            'categoryName': category['categoryName']
        }, ignore_index=True)

    # 中カテゴリ
    for category in json_data['result']['medium']:
        df = df.append({
            'category1': category['parentCategoryId'],
            'category2': category['categoryId'],
            'category3': "",
            'categoryId': f"{category['parentCategoryId']}-{category['categoryId']}",
            'categoryName': category['categoryName']
        }, ignore_index=True)
        parent_dict[str(category['categoryId'])] = category['parentCategoryId']

    # 小カテゴリ
    for category in json_data['result']['small']:
        parent = parent_dict.get(category['parentCategoryId'], "")
        df = df.append({
            'category1': parent,
            'category2': category['parentCategoryId'],
            'category3': category['categoryId'],
            'categoryId': f"{parent}-{category['parentCategoryId']}-{category['categoryId']}",
            'categoryName': category['categoryName']
        }, ignore_index=True)

        df_keyword = df.query('categoryName.str.contains(@user_message)', engine='python')

    for index, row in df_keyword.iterrows():
        time.sleep(1)
        category_id = row['categoryId']

        url = "https://app.rakuten.co.jp/services/api/Recipe/CategoryRanking/20170426"
        params = {
            "applicationId": RAKUTEN_API_KEY,
            "categoryId": category_id
        }
        response = requests.get(url, params=params)
        data = response.json()
        print("楽天APIからのデータ：", data)

        try:
            top = data["result"][0]
            title = top["recipeTitle"]
            recipe_url = top["recipeUrl"]
            return f"🍽 人気レシピ：{title}\n🔗 {recipe_url}"
        except Exception:
            return "レシピが見つかりませんでした🙇"

    

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    
    recipe = get_recipe_by_category(user_message)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=recipe)
    )
