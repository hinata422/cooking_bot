import requests
import pandas as pd
import json
import time
import re
import os
import json

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def generate_recipe_with_openai(food_name: str) -> str:
    try:
        chat_response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "あなたはプロのレシピ選定アシスタントです。"
                        "ユーザーから食材や料理名を受け取ったら、"
                        "信頼できるレシピページをインターネット検索で探し、"
                        "検索結果の中で最も上位に表示された詳細レシピページのURLを1つだけ返してください。"
                        "URLは必ず以下の信頼できるドメインの中から選んでください："
                        "cookpad.com、kurashiru.com、delishkitchen.tv、recipe.rakuten.co.jp。"
                        "URL以外の文章は一切含めず、URLのみを出力してください。"
                    )
                },
                {
                    "role": "user",
                    "content": f"{food_name} を使ったレシピページのURLを教えてください。"
                }
            ],
            temperature=0.7,
            max_tokens=300
        )

        content = chat_response.choices[0].message.content.strip()
        print("🔁 OpenAIからの返答:", content)

        # URL 抽出
        match = re.search(r'https://(?:cookpad\.com|www\.kurashiru\.com|delishkitchen\.tv|recipe\.rakuten\.co\.jp)/recipe/\S+', content)
        if match:
            return match.group(0)
        else:
            return "OpenAIからレシピURLを取得できませんでした。"

    except Exception as e:
        print(f"🛑 OpenAI API error: {e}")
        return "OpenAI APIエラーが発生しました。"