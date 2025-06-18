import os
from supabase import create_client

def test_supabase_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    assert url is not None, "SUPABASE_URL が設定されていません"
    assert key is not None, "SUPABASE_KEY が設定されていません"

    supabase = create_client(url, key)
    try:
        res = supabase.table("users").select("*").limit(1).execute()
        assert res.data is not None, "データが取得できませんでした"
        print("✅ Supabase接続テスト成功")
    except Exception as e:
        assert False, f"❌ Supabase接続に失敗しました: {e}"