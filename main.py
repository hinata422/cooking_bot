from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
from basemodel import RecipeCreate
from supabase import create_client, Client
from pydantic import BaseModel

import os
import uvicorn
import pandas as pd
import service as s
import re

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
RAKUTEN_API_KEY = os.getenv("RAKUTEN_API_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

app = FastAPI()

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def read_root():
    return {"message": "Cooking Bot is running!"}

@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers['X-Line-Signature']
    body = await request.body()
    body = body.decode("utf-8")

    print("Request body:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel secret/access token.")
        return {"message": "Signature verification failed."}

    return {"message": "OK"}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if hasattr(event, "delivery_context") and getattr(event.delivery_context, "is_redelivery", False):
        print("⚠️ Redeliveryイベントのためスキップします")
        return

    user_id = event.source.user_id if event.source.type == "user" else "unknown"
    user_message = event.message.text
    print(f"User message: {user_message}")
    print(f"User ID: {user_id}")

    # --- 1. 楽天APIでレシピを検索 ---
    recipe_url = s.get_recipe_by_category(user_message, RAKUTEN_API_KEY)

    # --- 2. 楽天で見つからなかった場合、SerpAPIで検索 ---
    if recipe_url is None or "レシピが見つかりませんでした" in recipe_url:
        recipe_url = s.search_recipe_url(user_message, SERPAPI_KEY)

    reply_text = recipe_url

    # --- 3. Supabaseに保存 ---
    if recipe_url and user_id != "unknown" and "http" in recipe_url:
     recipe_data = RecipeCreate(
        user_id=user_id,
        food_name=user_message,
        url=recipe_url
    )
    res = supabase.table("recipes").insert(recipe_data.model_dump()).execute()
    print("Supabase insert result:", res)

    # --- 4. LINEに返信 ---
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)