import requests # HTTPリクエストを送るためのライブラリ
import pandas as pd # データフレーム操作のためのライブラリ
import json # JSONデータの操作のためのライブラリ
import time # 時間操作のためのライブラリ
import re

def get_recipe_by_category(user_message:str, RAKUTEN_API_KEY:str):
    parent_dict = {}
    
    res = requests.get( 
        'https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426',
        params={'applicationId': RAKUTEN_API_KEY}
    )
    json_data = json.loads(res.text)

    df = pd.DataFrame(columns=['category1', 'category2', 'category3', 'categoryId', 'categoryName'])

    # 大カテゴリ
    for category in json_data['result']['large']:
        df = pd.concat([df, pd.DataFrame({
            'category1': category['categoryId'],
            'category2': "",
            'category3': "",
            'categoryId': category['categoryId'],
            'categoryName': category['categoryName']
        }, index=[0])], ignore_index=True)

    # 中カテゴリ
    for category in json_data['result']['medium']:
        df = pd.concat([df, pd.DataFrame({
            'category1': category['parentCategoryId'],
            'category2': category['categoryId'],
            'category3': "",
            'categoryId': f"{category['parentCategoryId']}-{category['categoryId']}",
            'categoryName': category['categoryName']
        }, index=[0])], ignore_index=True)
        parent_dict[str(category['categoryId'])] = category['parentCategoryId']

    # 小カテゴリ
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
        
def generate_recipe_with_dify(food_name: str, dify_url: str, dify_key: str) -> str:
    headers = {
        "Authorization": f"Bearer {dify_key}",
        "Content-Type": "application/json"
    }

    data = {
        "inputs": {
            "食材": food_name
        }
    }

    try:
        response = requests.post(dify_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        # "answer" にレシピがあると想定
        generated_text = result.get("answer", "")
        urls = re.findall(r'https?://\S+', generated_text)
        return urls[0] if urls else generated_text

    except Exception as e:
        print(f"Dify API error: {e}")
        return "レシピが見つかりませんでした"