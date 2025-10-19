from flask import Flask, jsonify, request
import random
import uuid

# --- Internal Modules --- #
from trending import TrendingManager
from sessions import SessionManager
import scraper
import database

# ---------------- Configuration ---------------- #
app = Flask(__name__)
REQUEST_TTL = 60 * 30  # 30 minutes
tag_index = dict()  # tag -> set(product_ids)

# ---------------- Managers ---------------- #
trending = TrendingManager(max_size=500, max_age_days=7, decay_factor=0.9)
session_mgr = SessionManager(request_ttl_seconds=REQUEST_TTL)

# ---------------- Helper Functions ---------------- #
def get_from_cache(session, rowsize):
    """Retrieve products from cache based on session tags."""
    candidate_products = {}
    for tag in session.get('tags', []):
        for pid in tag_index.get(tag, []):
            if pid not in session['seen_products']:
                candidate_products[pid] = candidate_products.get(pid, 0) + 1

    sorted_candidates = sorted(candidate_products.items(), key=lambda x: x[1], reverse=True)
    chunk = []
    # Cache removed — return empty
    return chunk


def get_from_db(session, rowsize):
    """Retrieve products from database with tag overlap."""
    session_tags = set(session.get('tags', []))
    candidate_products = []
    for product in database.get_products_by_tags(session.get('tags', [])):
        pid = product['product_id']
        if pid in session['seen_products']:
            continue
        product_tags = set(product.get('tags', []))
        overlap_count = len(session_tags & product_tags)
        candidate_products.append((overlap_count, product))
    candidate_products.sort(key=lambda x: x[0], reverse=True)

    chunk = []
    for _, product in candidate_products[:rowsize]:
        pid = product['product_id']
        chunk.append(product)
        session_mgr.add_to_seen(session['rid'], pid)
        trending.bump(pid, weight=3)
    return chunk


# ---------------- Routes ---------------- #
@app.get("/search")
def search():
    rid = request.args.get("rid", "")
    query = request.args.get("q", "")
    rowsize = request.args.get("rowsize", "")

    if not query.strip():
        return jsonify({"error": "Missing 'q' parameter"}), 400
    if not rowsize.isdigit() or int(rowsize) <= 0:
        return jsonify({"error": "'rowsize' must be a positive integer"}), 400
    rowsize = int(rowsize)

    # --- Session setup --- #
    new_session = False
    if not rid:
        rid = session_mgr.create_session("search", query)
        new_session = True
    session = session_mgr.get_session(uuid.UUID(rid))
    if not session:
        return jsonify({"error": "Session not found"}), 404
    session['rid'] = uuid.UUID(rid)

    # --- Get products --- #
    chunk = []
    # chunk = get_from_cache(session, rowsize)
    if len(chunk) < rowsize:
        chunk.extend(get_from_db(session, rowsize - len(chunk)))
    if len(chunk) < rowsize:
        print(f"⚙️ Live scrape triggered for '{query}'")
        new_products = scraper.main(query)
        serve_products = new_products[:rowsize - len(chunk)]
        for product in serve_products:
            pid = product['product_id']
            session_mgr.add_to_seen(session['rid'], pid)
            trending.bump(pid, weight=3)
        chunk.extend(serve_products)

    session_mgr.update_last_request(session['rid'])

    # --- Build response --- #
    resp = {
        "session": session_mgr.get_session_snapshot(uuid.UUID(rid)),
        "products": chunk
    }
    return jsonify(resp), 200


@app.get("/feed")
def feed():
    rid = request.args.get("rid", "")
    rowsize = request.args.get("rowsize", "")

    if not rowsize.isdigit() or int(rowsize) <= 0:
        return jsonify({"error": "Invalid 'rowsize'"}), 400
    rowsize = int(rowsize)

    if not rid:
        rid = session_mgr.create_session("feed")
    session = session_mgr.get_session(uuid.UUID(rid))
    if not session:
        return jsonify({"error": "Session not found"}), 404
    session['rid'] = uuid.UUID(rid)

    top_trending = trending.get_top(100)
    TRENDING_LIMIT = min(int(0.7 * rowsize), len(top_trending))
    RECENT_LIMIT = min(int(0.2 * rowsize), len(session['seen_products']))
    RANDOM_LIMIT = rowsize - TRENDING_LIMIT - RECENT_LIMIT

    trending_ids = random.sample(top_trending, TRENDING_LIMIT)
    recent_ids = random.sample(session['seen_products'], RECENT_LIMIT)
    random_products = database.get_random_products(limit=RANDOM_LIMIT)

    product_ids = trending_ids + recent_ids + [p['product_id'] for p in random_products]
    random.shuffle(product_ids)

    chunk = []
    for pid in product_ids:
        product = database.get_product_by_id(pid)
        if product:
            chunk.append(product)
            session_mgr.add_to_seen(session['rid'], pid)
            trending.bump(pid, weight=1)

    session_mgr.update_last_request(session['rid'])

    # --- Build response --- #
    resp = {
        "session": session_mgr.get_session_snapshot(uuid.UUID(rid)),
        "products": chunk
    }
    return jsonify(resp), 200


# ---------------- Entry ---------------- #
if __name__ == "__main__":
    print("🚀 Starting Flask product feed server on http://localhost:5000")
    app.run("localhost", 5000)
