import requests
from urllib.parse import quote
from Scraper.cookie_manager import get_cookie, report_cookie_status
import time
import uuid



SITE = "ajio"



def debug_print(message, debug=False):
    """Optional descriptive debug function"""
    if debug:
        print(f"🔍 DEBUG: {message}")



def extract_main_image(product, debug=False):
    # Priority 1: PRIMARY product image from 'images' array
    for img in product.get("images", []):
        if img.get("imageType") == "PRIMARY" and img.get("format") == "product" and img.get("url", "").startswith("http"):
            # if debug:
                # debug_print(f"Found main image from images[] PRIMARY: {img['url']}", debug)
            return img["url"]

    # Priority 2: outfitPictureURL from color variant data
    variant_data = product.get("fnlColorVariantData", {})
    if variant_data:
        outfit_url = variant_data.get("outfitPictureURL")
        if outfit_url and outfit_url.startswith("http"):
            # if debug:
            #     debug_print(f"Found main image from outfitPictureURL: {outfit_url}", debug)
            return outfit_url

    # Priority 3: First image in extraImages
    extra_images = product.get("extraImages", [])
    for group in extra_images:
        for img in group.get("images", []):
            if img.get("url", "").startswith("http"):
                # if debug:
                    # debug_print(f"Found main image from extraImages: {img['url']}", debug)
                return img["url"]

    if debug:
        debug_print("No main image found", debug)
    return None





def extract_data(response, debug=False):
    # debug_print(f"Starting data extraction from response", debug)
    extracted_data = []
    products = response.get("products", [])
    debug_print(f"Found {len(products)} products in response", debug)
    
    for i, product in enumerate(products):
        try:
            title = product.get("name")
            url = product.get("url", "").strip("/")
            # debug_print(f"Processing product {i+1}: {title}", debug)
            
            # Skip products without essential data
            if not title or not url:
                # debug_print(f"Skipping product {i+1} - missing title or URL", debug)
                continue
            
            # Extract main image using the new function
            main_image = extract_main_image(product, debug)
            
            item = {
                "source": "Ajio",
                "product_id": str(uuid.uuid4()),
                "title": title,
                "description": product.get("fnlColorVariantData", {}).get("brandName"),
                "product_url": f"https://www.ajio.com/{url}",
                "image_url": main_image,  # Single image instead of array
                "price": product.get("price", {}).get("value")
            }
            # debug_print(f"Successfully extracted data for: {title} - Price: {item['price']} - Image: {'✅' if main_image else '❌'}", debug)
            extracted_data.append(item)
        except Exception as e:
            print(f"Skipping product due to error: {e}")
            if debug:
                import traceback
                traceback.print_exc()
    
    debug_print(f"Extraction completed. Total products extracted: {len(extracted_data)}", debug)
    return extracted_data




def product_search(keyword, offset, rows, debug=False):
    debug_print(f"Starting product search for keyword: '{keyword}'", debug)
    debug_print(f"Search parameters - Offset: {offset}, Rows: {rows}", debug)
    
    sanitized_keyword = quote(keyword)
    # debug_print(f"Sanitized keyword: '{sanitized_keyword}'", debug)
    
    url = f"https://www.ajio.com/api/search?query={sanitized_keyword}&format=json&pageSize={rows}&currentPage={offset}"
    # debug_print(f"Request URL: {url}", debug)
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "accept": "application/json",
        "referer": f"https://www.ajio.com/search/?text={sanitized_keyword}"
    }
    # debug_print(f"Request headers prepared", debug)

    max_cookie_attempts = 2
    for attempt in range(max_cookie_attempts):
        debug_print(f"Cookie attempt {attempt+1}/{max_cookie_attempts}", debug)
        session_data = get_cookie(SITE)
        if session_data is None:
            print("❌ Failed to acquire cookies.")
            debug_print(f"Session acquisition failed", debug)
            continue
        cookies_list = session_data["cookies"]
        session_id = session_data["session_id"]
        debug_print(f"Session acquired - ID: {session_id}, Cookies count: {len(cookies_list)}", debug)
        cookies = {cookie['name']: cookie['value'] for cookie in cookies_list}
        try:
            debug_print(f"Making HTTP request to Ajio API", debug)
            response = requests.get(url, headers=headers, cookies=cookies)
            debug_print(f"Response received - Status code: {response.status_code}", debug)
            if response.status_code == 200:
                debug_print(f"Request successful, extracting data", debug)
                try:
                    data = extract_data(response.json(), debug)
                    # debug_print(f"Reporting session as healthy", debug)
                    report_cookie_status(session_id, True)
                    debug_print(f"Search completed successfully. Returning {len(data)} products", debug)
                    return data if data is not None else []
                except Exception as e:
                    print(f"Error extracting data: {e}")
                    debug_print(f"Data extraction failed: {e}", debug)
                    if debug:
                        import traceback
                        traceback.print_exc()
                    report_cookie_status(session_id, False)
                    continue
            elif response.status_code in [401, 403]:
                print(f"⚠️ Got {response.status_code} - Forbidden or Unauthorized. Marking cookie unhealthy and retrying...")
                debug_print(f"Marking session as unhealthy and retrying", debug)
                report_cookie_status(session_id, False)
                time.sleep(1)
                continue
            else:
                print(f"❌ Request failed with status code: {response.status_code}")
                print("Response text:", response.text)
                debug_print(f"Request failed, marking session as unhealthy", debug)
                report_cookie_status(session_id, False)
                break
        except Exception as e:
            print(f"Request exception: {e}")
            debug_print(f"HTTP request exception: {e}", debug)
            report_cookie_status(session_id, False)
            continue
    debug_print(f"All cookie attempts failed or exhausted", debug)
    return []





def scrape_first_2_pages(keyword, rows_per_page=50, debug=False):
    """Scrape the first 2 pages of products for a given keyword"""
    all_products = []
    total_pages = 2
    
    print(f"🚀 Starting to scrape first {total_pages} pages for keyword: '{keyword}'")
    print(f"📄 Products per page: {rows_per_page}")
    print("=" * 60)
    
    for page in range(1, total_pages + 1):
        print(f"📖 Scraping page {page}/{total_pages}...")
        
        # Call the existing product_search function
        page_products = product_search(keyword, page, rows_per_page, debug=debug)
        
        if page_products:
            all_products.extend(page_products)
            print(f"✅ Page {page} completed - Found {len(page_products)} products")
            
            # Print image stats for debugging
            images_found = sum(1 for product in page_products if product.get('image_url'))
            print(f"   📸 Products with images on this page: {images_found}/{len(page_products)}")
        else:
            print(f"❌ Page {page} failed or returned no products")
        
        # Add a small delay between requests to be respectful
        if page < total_pages:
            time.sleep(2)
        
        print("-" * 40)
    
    print(f"🎉 Scraping completed!")
    print(f"📊 Total products collected: {len(all_products)}")
    
    # Final image statistics
    total_images = sum(1 for product in all_products if product.get('image_url'))
    print(f"📸 Products with images: {total_images}/{len(all_products)}")
    print("=" * 60)
    
    return all_products






def scrape(query):
    return scrape_first_2_pages(query)