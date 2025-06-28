import requests
import pandas as pd
import time
import re
import os
from dotenv import load_dotenv

load_dotenv()


SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# 楽天レシピAPIでカテゴリからレシピを取得
def get_recipe_by_category(user_message: str, RAKUTEN_API_KEY: str):
    parent_dict = {}

    res = requests.get(
        'https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426',
        params={'applicationId': RAKUTEN_API_KEY}
    )
    json_data = res.json()

    df = pd.DataFrame(columns=['category1', 'category2', 'category3', 'categoryId', 'categoryName'])

    for category in json_data['result']['large']:
        df = pd.concat([df, pd.DataFrame({
            'category1': category['categoryId'],
            'category2': "",
            'category3': "",
            'categoryId': category['categoryId'],
            'categoryName': category['categoryName']
        }, index=[0])], ignore_index=True)

    for category in json_data['result']['medium']:
        df = pd.concat([df, pd.DataFrame({
            'category1': category['parentCategoryId'],
            'category2': category['categoryId'],
            'category3': "",
            'categoryId': f"{category['parentCategoryId']}-{category['categoryId']}",
            'categoryName': category['categoryName']
        }, index=[0])], ignore_index=True)
        parent_dict[str(category['categoryId'])] = category['parentCategoryId']

    for category in json_data['result']['small']:
        parent = parent_dict.get(category['parentCategoryId'], "")
        df = pd.concat([df, pd.DataFrame({
            'category1': parent,
            'category2': category['parentCategoryId'],
            'category3': category['categoryId'],
            'categoryId': f"{parent}-{category['parentCategoryId']}-{category['categoryId']}",
            'categoryName': category['categoryName']
        }, index=[0])], ignore_index=True)

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

    return None


# SerpAPIを使ってレシピURLを検索
def search_recipe_url(query: str, serpapi_key: str = SERPAPI_KEY) -> str:
    try:
        params = {
            "q": f"{query} site:cookpad.com OR site:kurashiru.com OR site:delishkitchen.tv OR site:recipe.rakuten.co.jp",
            "api_key": serpapi_key,
            "engine": "google",
            "hl": "ja",
            "gl": "jp",
            "num": 5
        }

        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()

        for result in data.get("organic_results", []):
            url = result.get("link", "")
            if re.match(r"https?://(cookpad\.com|www\.kurashiru\.com|delishkitchen\.tv|recipe\.rakuten\.co\.jp)/", url):
                return url

        return "信頼できるレシピURLが見つかりませんでした。"

    except Exception as e:
        print("🛑 SerpAPI error:", e)
        return "レシピURL取得時にエラーが発生しました。"