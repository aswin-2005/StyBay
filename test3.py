from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_product_meta(pid: str):
    """
    Return product metadata for a given product ID.
    """
    prod_resp = supabase.table("products").select("*").eq("product_id", pid).execute()
    if prod_resp.data:
        return prod_resp.data[0]
    return None

if __name__ == "__main__":
    test_pid = "004197cd-fe2b-4243-b20e-57888ab3ab98"
    meta = get_product_meta(test_pid)
    print(f"Metadata for product ID {test_pid}:")
    print(meta)