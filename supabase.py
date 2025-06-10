from supabase import create_cliant,Cliant
from dotenv import load_dotenv
import os

load_dotenv()

url=os.getenv("SUPABASE_URL")
key=os.getenv("SUPABASE_KEY")
supabase: Cliant = create_cliant(url, key)

data = {"message": "Hello Supabase!"}
res = supabase.table("test_table").insert(data).execute()
print(res)
