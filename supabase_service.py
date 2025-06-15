from supabase import create_client,Client
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.v3.webhook import WebhookHandler
import os

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")# 環境変数からLINEのチャンネルシークレットを取得
handler = WebhookHandler(LINE_CHANNEL_SECRET)

url=os.getenv("SUPABASE_URL")
key=os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)# Supabaseクライアントの作成

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    recipe_title = event.message.text
    line_user_id = event.source.user_id

    # ユーザーID取得
    user_response = supabase.table("user").select("id").eq("line_user_id", line_user_id).execute()

    if user_response.data:
        user_id = user_response.data[0]["id"]

        # レシピを保存
        recipe_data = {"name": recipe_title,"url": "https://example.com"}  # 仮URLでOK
        recipes_response = supabase.table("recipe").insert(recipe_data).execute()

        if recipes_response.data:
            recipe_id = recipes_response.data[0]["id"]

            # 中間テーブルに保存
            link_data = {"user_id": user_id, "recipe_id": recipe_id}
            link_response = supabase.table("user_recipe").insert(link_data).execute()

            print("中間テーブルに保存しました:", link_response.data)
        else:
            print("レシピの保存に失敗しました")
    else:
        print("ユーザーが登録されていません")


def check_connection():
    try:
        res = supabase.table("user").select("*").limit(1).execute()
        print("✅ Supabase に接続できました！")
        print("取得したデータ:", res.data)
    except Exception as e:
            print("❌ Supabase 接続エラー:", e)
    
if __name__ == "__main__":
        check_connection()