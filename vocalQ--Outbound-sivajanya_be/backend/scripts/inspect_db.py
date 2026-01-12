
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

try:
    res = supabase.table("calls").select("*").limit(1).execute()
    if res.data:
        print("Columns in 'calls' table:")
        print(res.data[0].keys())
    else:
        print("No calls found in the table. Cannot auto-detect columns.")
        # Let's try to get schema info if possible, or just list what we expect
except Exception as e:
    print(f"Error: {e}")
