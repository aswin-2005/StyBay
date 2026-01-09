# database.py
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import random

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- Core Functions ---------------- #

def add_product(product: dict):
    """
    Insert or update a product in `products` table and sync its tags in `tags`.
    Expects product["tags"] to be a list[str].
    """
    product_copy = product.copy()
    tags = product_copy.pop("tags", [])

    # Insert / update product
    supabase.table("products").upsert(product_copy).execute()

    # Update tags mapping
    for tag in tags:
        resp = supabase.table("tags").select("product_ids").eq("tag", tag).execute()
        if resp.data:
            product_ids = resp.data[0]["product_ids"]
            if product_copy["product_id"] not in product_ids:
                product_ids.append(product_copy["product_id"])
        else:
            product_ids = [product_copy["product_id"]]

        supabase.table("tags").upsert({
            "tag": tag,
            "product_ids": product_ids
        }).execute()

    return {"status": "success", "product_id": product_copy["product_id"]}


def get_product_by_id(product_id: str):
    """Fetch a single product by its ID."""
    response = supabase.table("products").select("*").eq("product_id", product_id).execute()
    if response.data:
        return response.data[0]
    return None


def get_products_by_tags(tags):
    product_ids = set()

    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            continue

        resp = supabase.table("tags") \
            .select("product_ids") \
            .eq("tag", tag) \
            .execute()

        if not resp.data:
            continue

        for pid in resp.data[0].get("product_ids", []):
            if isinstance(pid, str) and pid.strip():
                product_ids.add(pid)

    if not product_ids:
        return []

    # HARD LIMIT — protects PostgREST
    product_ids = list(product_ids)[:50]

    try:
        resp = supabase.table("products") \
            .select("*") \
            .in_("product_id", product_ids) \
            .execute()
        return resp.data or []
    except Exception as e:
        print("❌ Supabase IN query failed")
        print("product_ids =", product_ids)
        print(e)
        return []



def get_random_products(limit: int = 10):
    resp = supabase.table("products") \
        .select("*") \
        .limit(limit) \
        .execute()
    return resp.data or []


def add_products_batch(products_batch):
    """Upsert a batch of products and update tag references efficiently."""
    if not products_batch:
        return
    try:
        supabase.table("products").upsert(products_batch).execute()
    except Exception as e:
        print(f"⚠️ Failed to upsert products: {e}")
        return
    
    # Aggregate tags
    tag_map = {}
    for p in products_batch:
        for t in p.get("tags", []):
            tag_map.setdefault(t, []).append(p["product_id"])

    if not tag_map:
        return

    try:
        existing_resp = supabase.table("tags").select("tag, product_ids").in_("tag", list(tag_map.keys())).execute()
        existing_map = {row["tag"]: row["product_ids"] for row in existing_resp.data}

        tag_rows = []
        for tag, ids in tag_map.items():
            merged_ids = list(set(existing_map.get(tag, []) + ids))
            tag_rows.append({"tag": tag, "product_ids": merged_ids})

        supabase.table("tags").upsert(tag_rows).execute()

    except Exception as e:
        print(f"⚠️ Failed to upsert tags batch: {e}")

