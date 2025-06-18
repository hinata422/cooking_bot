from supabase import create_client, Client
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.v3.webhook import WebhookHandler
import os

# 環境変数読み込み
load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
handler = WebhookHandler(LINE_CHANNEL_SECRET)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("✅ イベントを受信しました")

    recipe_title = event.message.text
    line_user_id = event.source.user_id

    print(f"📝 レシピタイトル: {recipe_title}")
    print(f"👤 LINEユーザーID: {line_user_id}")

    try:
        # ユーザーID取得
        user_response = supabase.table("users").select("id").eq("line_user_id", line_user_id).execute()
        print(f"🔍 Supabaseユーザー取得結果: {user_response.data}")
    except Exception as e:
        print("❌ ユーザー取得エラー:", e)
        return

    if user_response.data:
        user_id = user_response.data[0]["id"]
        print(f"✅ ユーザーID: {user_id}")

        recipe_data = {
            "name": recipe_title,
            "url": "https://example.com"  # 仮URL
        }

        try:
            recipe_response = supabase.table("recipes").insert(recipe_data).execute()
            print(f"📥 レシピ挿入結果: {recipe_response.data}")
        except Exception as e:
            print("❌ レシピ挿入エラー:", e)
            return

        if recipe_response.data:
            recipe_id = recipe_response.data[0]["id"]
            print(f"✅ レシピID: {recipe_id}")

            link_data = {
                "user_id": user_id,
                "recipe_id": recipe_id
            }

            try:
                link_response = supabase.table("user_recipe").insert(link_data).execute()
                print(f"🔗 中間テーブル挿入結果: {link_response.data}")
            except Exception as e:
                print("❌ 中間テーブル保存エラー:", e)
        else:
            print("⚠️ レシピ保存に失敗しました（dataなし）")
    else:
        print("⚠️ ユーザーが見つかりません")

def check_connection():
    try:
        res = supabase.table("users").select("*").limit(1).execute()
        print("✅ Supabase に接続できました！")
        print("📦 ユーザーデータ:", res.data)
    except Exception as e:
        print("❌ Supabase 接続エラー:", e)

if __name__ == "__main__":
    check_connection()