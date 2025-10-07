import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import quote_plus
import uuid

SITE = "amazon"

def debug_print(message, debug=False):
    """debug function"""
    if debug:
        print(f"🔍 DEBUG: {message}")















def extract_main_image(product, debug=False):
    """Extract the main image URL from Amazon product element"""
    img_elem = product.select_one("img.s-image")
    if img_elem and img_elem.has_attr("src"):
        image_url = img_elem["src"]
        if image_url and image_url.startswith("http"):
            if debug:
                debug_print(f"Found main image: {image_url}", debug)
            return image_url
    
    if debug:
        debug_print("No main image found", debug)
    return None















def extract_data(soup, debug=False):
    """Transform Amazon's HTML response into a list of normalized product dicts"""
    debug_print(f"Starting data extraction from soup", debug)
    extracted_data = []
    products = soup.select("div.s-main-slot div[data-component-type='s-search-result']")
    debug_print(f"Found {len(products)} products in response", debug)
    
    for i, product in enumerate(products):
        try:
            debug_print(f"Processing product {i+1}", debug)
            
            title_elem = product.select_one("span.a-size-base-plus")
            link_elem = product.select_one("a.a-link-normal")
            price_whole = product.select_one(".a-price-whole")
            rating_elem = product.select_one(".a-icon-alt")
            desc_elem = product.select_one("h2.a-size-base-plus span")
            
            title = title_elem.get_text(strip=True) if title_elem else None
            link = "https://www.amazon.in" + link_elem["href"] if link_elem and link_elem.has_attr("href") else None
            
            # Skip products without essential data
            if not title or not link:
                debug_print(f"Skipping product {i+1} - missing title or URL", debug)
                continue
            
            # Extract main image using the new function
            main_image = extract_main_image(product, debug)
            debug_print(f"Extracted main_image for product {i+1}: {main_image}", debug)
            
            # Fixed price parsing
            price = None
            if price_whole:
                try:
                    price_text = price_whole.get_text(strip=True)
                    price_clean = price_text.replace('₹', '').replace(',', '').strip()
                    price = float(price_clean)
                    debug_print(f"Product {i+1} price parsed: ₹{price}", debug)
                except ValueError:
                    debug_print(f"Product {i+1} price parsing failed: {price_text}", debug)
                    price = None
            
            rating = None
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)  # "4.1 out of 5 stars"
                try:
                    rating = float(rating_text.split()[0])  # take first part "4.1"
                except ValueError:
                    rating = None
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            item = {
                "source": "Amazon",
                "product_id": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "product_url": link,
                "image_url": main_image,  # Single image instead of array
                "price": price,
                "rating": rating
            }
            
            debug_print(f"Successfully extracted product {i+1}: {title} - Price: ₹{price} - Image: {'✅' if main_image else '❌'}", debug)
            extracted_data.append(item)
                
        except Exception as e:
            print(f"Error extracting product {i}: {e}")
            debug_print(f"Exception in product {i+1}: {e}", debug)
            if debug:
                import traceback
                traceback.print_exc()
            continue
    
    debug_print(f"Extraction completed. Total products extracted: {len(extracted_data)}", debug)
    return extracted_data






def product_search(keyword, page, debug=False):
    debug_print(f"Starting Amazon product search for keyword: '{keyword}'", debug)
    debug_print(f"Search parameters - Page: {page}", debug)
    
    # Add validation at start
    if not keyword or not isinstance(keyword, str):
        print("❌ Invalid keyword provided")
        debug_print(f"Keyword validation failed: {keyword}", debug)
        return []
    
    if not isinstance(page, int) or page < 1:
        print("❌ Invalid page provided")
        debug_print(f"Page validation failed: {page}", debug)
        return []
    
    debug_print(f"Input validation passed", debug)
    
    sanitized_keyword = quote_plus(keyword)
    debug_print(f"Sanitized keyword: '{sanitized_keyword}'", debug)
    
    url = f"https://www.amazon.in/s?k={sanitized_keyword}&page={page}"
    debug_print(f"Request URL: {url}", debug)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.amazon.in/",
    }
    debug_print(f"Request headers prepared", debug)
    
    try:
        debug_print(f"Making HTTP request to Amazon", debug)
        response = requests.get(url, headers=headers)
        debug_print(f"Response received - Status code: {response.status_code}", debug)
        
        if response.status_code != 200:
            print(f"❌ ERROR: Failed to fetch page. Status code: {response.status_code}")
            debug_print(f"Request failed with status {response.status_code}", debug)
            return []
        
        debug_print(f"Request successful, parsing HTML with BeautifulSoup", debug)
        soup = BeautifulSoup(response.content, "html.parser")
        debug_print(f"HTML parsed successfully", debug)
        
        debug_print(f"Extracting product data", debug)
        data = extract_data(soup, debug)
        
        debug_print(f"Search completed successfully. Returning {len(data)} products", debug)
        return data if data is not None else []
        
    except Exception as e:
        print(f"Request exception: {e}")
        debug_print(f"HTTP request exception: {e}", debug)
        if debug:
            import traceback
            traceback.print_exc()
        return []





















def scrape_first_2_pages(keyword, debug=False):
    """Scrape the first 2 pages of products for a given keyword from Amazon"""
    all_products = []
    total_pages = 2
    
    print(f"🚀 Starting to scrape first {total_pages} pages from Amazon for keyword: '{keyword}'")
    print("🔧 USING UPDATED AMAZON SPIDER WITH IMPROVED STRUCTURE")  # ← Debug marker
    print("=" * 60)
    
    for page in range(1, total_pages + 1):
        print(f"📖 Scraping Amazon page {page}/{total_pages}...")
        
        # Call the existing product_search function
        page_products = product_search(keyword, page, debug=debug)
        
        if page_products:
            all_products.extend(page_products)
            print(f"✅ Amazon page {page} completed - Found {len(page_products)} products")
            
            # Print image stats for debugging
            images_found = sum(1 for product in page_products if product.get('image_url'))
            print(f"   📸 Products with images on this page: {images_found}/{len(page_products)}")
        else:
            print(f"❌ Amazon page {page} failed or returned no products")
        
        # Add a small delay between requests to be respectful
        if page < total_pages:
            time.sleep(3)  # Slightly longer delay for Amazon
        
        print("-" * 40)
    
    print(f"🎉 Amazon scraping completed!")
    print(f"📊 Total products collected from Amazon: {len(all_products)}")
    
    # Final image statistics
    total_images = sum(1 for product in all_products if product.get('image_url'))
    print(f"📸 Products with images: {total_images}/{len(all_products)}")
    
    # Debug: Show a sample product structure
    if all_products:
        sample = all_products[0]
        print(f"🔍 FINAL DEBUG: Sample product has image_url: {'✅' if sample.get('image_url') else '❌'}")
        if sample.get('image_url'):
            print(f"🔍 FINAL DEBUG: Image URL: {sample['image_url'][:50]}...")
    
    print("=" * 60)
    
    return all_products

def scrape(query):
    return scrape_first_2_pages(query)
