from scraper import scrape_site
from Scraper import ajio_spider as ajio

SITE = ajio

if __name__ == "__main__":
    query = "sneakers"
    products = scrape_site("Ajio", SITE, query)
    print(f"Scraped {len(products)} products from Ajio for query '{query}'")