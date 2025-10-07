import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import scrapers
from Scraper import amazon_spider as amazon
from Scraper import myntra_spider as myntra
from Scraper import ajio_spider as ajio

# Import tagger and database
import tagger
from database import add_products_batch
import cache


def scrape_site(name, scraper, query):
    """Run a single scraper and return products."""
    print(f"🔍 Scraping {name}...")
    products = scraper.scrape(query)
    print(f"✅ {name}: {len(products)} products found")
    return products


def scrape_all_sites(query):
    """Sequentially scrape all supported sites."""
    all_products = []
    for name, scraper in [
        ("Amazon", amazon),
        ("Myntra", myntra),
        ("Ajio", ajio),
    ]:
        try:
            products = scrape_site(name, scraper, query)
            all_products.extend(products)
        except Exception as e:
            print(f"⚠️ {name} scrape failed: {e}")
    return all_products


def process_batch(batch, batch_id, timestamp):
    """Tag, cache, and store a batch of products."""
    tagged_list = tagger.batch_extract_tags(batch, batch_size=len(batch))
    processed = []

    for product, tags in zip(batch, tagged_list):
        product["tags"] = tags
        product["batch_id"] = batch_id
        product["created_at"] = timestamp

        # Push to cache
        cache.set_product(product["product_id"], product)
        processed.append(product)

    # Push to database
    add_products_batch(processed)

    print(f"✅ Batch processed: {len(processed)} products")
    return processed


def process_products_parallel(products, batch_id, timestamp, batch_size=50):
    """Split products into batches, process in parallel, and return all processed products."""
    batches = [products[i:i + batch_size] for i in range(0, len(products), batch_size)]
    print(f"🏗️ Processing {len(products)} products in {len(batches)} parallel batches...")

    processed_products = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_batch, batch, batch_id, timestamp) for batch in batches]
        for f in as_completed(futures):
            try:
                batch_result = f.result()
                processed_products.extend(batch_result)
            except Exception as e:
                print(f"⚠️ Batch processing failed: {e}")

    return processed_products


def main(query: str):
    batch_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    print(f"\n🚀 Starting scrape pipeline for query: '{query}'")
    print(f"🆔 Batch ID: {batch_id}")

    # Stage 1 — Scrape
    products = scrape_all_sites(query)
    print(f"📦 Total products scraped: {len(products)}")

    # Stage 2 — Tag + Cache + DB
    processed_products = process_products_parallel(products, batch_id, timestamp)
    print("🎉 Pipeline completed successfully!")

    return processed_products
