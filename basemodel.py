from pydantic import BaseModel

# 共通のレシピ情報（food_nameとurl）
class RecipeBase(BaseModel):
    food_name: str
    url: str

# 新規作成時に使うモデル（user_idを追加）
class RecipeCreate(RecipeBase):
    user_id: str

# 出力用モデル（idとuser_idを含む）
class RecipeOut(RecipeBase):
    id: str
    user_id: str