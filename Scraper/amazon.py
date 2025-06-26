import requests
from bs4 import BeautifulSoup
import json
import os



RAW_RESPONSE_DIR = 'Scrape/Debug/raw_response'
REFINED_RESPONSE_DIR = 'product_search/debug/refined_response'



def extract_data(soup):
    products = []
    for product in soup.select("div.s-main-slot div[data-component-type='s-search-result']"):
        title_elem = product.select_one("span.a-size-base-plus")
        link_elem = product.select_one("a.a-link-normal")
        img_elem = product.select_one("img.s-image")
        price_whole = product.select_one(".a-price-whole")
        rating_elem = product.select_one(".a-icon-alt")
        desc_elem = product.select_one("h2.a-size-base-plus span")
        title = title_elem.get_text(strip=True) if title_elem else None
        link = "https://www.amazon.in" + link_elem["href"] if link_elem and link_elem.has_attr("href") else None
        image = img_elem["src"] if img_elem and img_elem.has_attr("src") else None
        price_text = price_whole.get_text(strip=True) if price_whole else None
        price = None
        if price_text:
            price = price_text.replace(',', '')
            price = price.replace('.','')
            price = int(price)
        rating = rating_elem.get_text(strip=True) if rating_elem else None
        description = desc_elem.get_text(strip=True) if desc_elem else None

        products.append({
            "source": "Amazon",
            "title": title,
            "description": description,
            "product_url": link,
            "image_urls": [image],
            "price": price,
            "rating": rating
        })
    return products



def debug(data, response, keyword, page):
    # Save raw HTML
    os.makedirs(RAW_RESPONSE_DIR, exist_ok=True)
    raw_file = os.path.join(RAW_RESPONSE_DIR, f"{keyword.replace(' ', '_')}_amazon_page{page}.html")
    with open(raw_file, "w", encoding="utf-8") as f:
        f.write(response.text)
    # Save JSON
    os.makedirs(REFINED_RESPONSE_DIR, exist_ok=True)
    refined_file = os.path.join(REFINED_RESPONSE_DIR, f"{keyword.replace(' ', '_')}_amazon_page{page}.json")
    with open(refined_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved raw HTML to: {raw_file}")
    print(f"✅ Saved extracted JSON to: {refined_file}")



def product_search(keyword, page):
    sanitized_keyword = keyword.replace(" ", "+")
    url = f"https://www.amazon.in/s?k={sanitized_keyword}&page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.amazon.in/",
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    if response.status_code != 200:
        print(f"❌ ERROR: Failed to fetch page. Status code: {response.status_code}")
        return []
    data = extract_data(soup)
    # debug(data, response, keyword, page)
    return data

