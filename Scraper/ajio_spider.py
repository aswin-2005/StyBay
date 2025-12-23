import requests
from urllib.parse import quote
from Scraper.cookie_manager import get_cookie, report_cookie_status
import json
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
            return img["url"]

    # Priority 2: outfitPictureURL from color variant data
    variant_data = product.get("fnlColorVariantData", {})
    if variant_data:
        outfit_url = variant_data.get("outfitPictureURL")
        if outfit_url and outfit_url.startswith("http"):
            return outfit_url

    # Priority 3: First image in extraImages
    extra_images = product.get("extraImages", [])
    for group in extra_images:
        for img in group.get("images", []):
            if img.get("url", "").startswith("http"):
                return img["url"]

    if debug:
        debug_print("No main image found", debug)
    return None

def extract_all_images(product, debug=False):
    """Extract all available image URLs from product data"""
    all_images = []
    
    # From images array
    for img in product.get("images", []):
        img_url = img.get("url", "")
        if img_url and img_url.startswith("http") and img_url not in all_images:
            all_images.append(img_url)
    
    # From extraImages
    for group in product.get("extraImages", []):
        for img in group.get("images", []):
            img_url = img.get("url", "")
            if img_url and img_url.startswith("http") and img_url not in all_images:
                all_images.append(img_url)
    
    # From variant data
    variant_data = product.get("fnlColorVariantData", {})
    if variant_data:
        outfit_url = variant_data.get("outfitPictureURL")
        if outfit_url and outfit_url.startswith("http") and outfit_url not in all_images:
            all_images.append(outfit_url)
    
    return all_images if all_images else None

def safe_get(data, *keys, default=None):
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, {})
        else:
            return default
    return data if data != {} else default

def extract_data(response, debug=False):
    debug_print(f"Starting data extraction from response", debug)
    extracted_data = []
    products = response.get("products", [])
    debug_print(f"Found {len(products)} products in response", debug)
    
    for i, product in enumerate(products):
        try:
            title = product.get("name")
            url = product.get("url", "").strip("/")
            debug_print(f"Processing product {i+1}: {title}", debug)
            
            # Skip products without essential data
            if not title or not url:
                debug_print(f"Skipping product {i+1} - missing title or URL", debug)
                continue
            
            # Extract images
            main_image = extract_main_image(product, debug)
            all_images = extract_all_images(product, debug)
            
            # Get nested data safely
            price_data = product.get("price", {})
            variant_data = product.get("fnlColorVariantData", {})
            waist_sizes = product.get("waistSizes", {})
            segmentation = product.get("segmentation", {})
            
            # Build comprehensive product dictionary
            item = {
                # Basic Info
                "source": "Ajio",
                "product_id": str(uuid.uuid4()),
                "ajio_product_id": product.get("code"),
                "model_code": product.get("modelCode"),
                
                # Product Details
                "title": title,
                "name": product.get("name"),
                "brand": variant_data.get("brandName"),
                "description": product.get("baseOptions"),
                "product_type": segmentation.get("productType"),
                
                # URLs
                "product_url": f"https://www.ajio.com/{url}",
                "url_key": url,
                
                # Images
                "image_url": main_image,
                "all_images": all_images,
                
                # Pricing
                "price": price_data.get("value"),
                "currency": price_data.get("currencyIso"),
                "formatted_price": price_data.get("formattedValue"),
                "was_price": safe_get(product, "wasPriceData", "value"),
                "was_price_formatted": safe_get(product, "wasPriceData", "formattedValue"),
                "discount_percentage": product.get("discount"),
                "offer": product.get("offer"),
                
                # Ratings & Reviews
                "rating": product.get("ratingsAndReviewsStatistics"),
                
                # Categories & Classification
                "categories": product.get("categories", []),
                "category_type": segmentation.get("categoryType"),
                "article_type": segmentation.get("articleType"),
                "category_path": product.get("categoryPath"),
                "base_options": product.get("baseOptions"),
                
                # Colors & Variants
                "color": variant_data.get("color"),
                "color_name": variant_data.get("colorName"),
                "color_families": variant_data.get("colorFamilies", []),
                "outfit_picture_url": variant_data.get("outfitPictureURL"),
                
                # Sizes & Availability
                "available_sizes": product.get("availableSizes", []),
                "size_type": product.get("sizeType"),
                "waist_sizes": waist_sizes,
                "in_stock": product.get("stock", {}).get("stockLevelStatus") == "inStock",
                "stock_level": product.get("stock", {}).get("stockLevel"),
                
                # Gender & Demographics
                "gender": segmentation.get("gender"),
                "age_group": segmentation.get("ageGroup"),
                
                # Additional Metadata
                "is_express": product.get("isExpress", False),
                "is_new": product.get("isNew", False),
                "is_trending": product.get("isTrending", False),
                "is_only_few_left": product.get("isOnlyFewLeft", False),
                "premium_product": product.get("premiumProduct", False),
                "fast_fashion_product": product.get("fastFashionProduct", False),
                
                # Search & Display
                "search_boost_score": product.get("searchBoostScore"),
                "boost": product.get("boost"),
                
                # Facets & Filters
                "facets": product.get("facets", []),
                "exclusion": product.get("exclusion"),
                
                # Labels & Badges
                "badges": product.get("badges", []),
                "special_price_badge": product.get("specialPriceBadge"),
                
                # Delivery & Logistics
                "cod_enabled": product.get("codEnabled"),
                
                # Raw data for any additional fields
                "raw_data": product
            }
            
            debug_print(f"Successfully extracted data for: {title} - Price: {item['price']} - Image: {'✅' if main_image else '❌'}", debug)
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
    
    url = f"https://www.ajio.com/api/search?query={sanitized_keyword}&format=json&pageSize={rows}&currentPage={offset}"
    
    # Enhanced headers to look more like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": f"https://www.ajio.com/search/?text={sanitized_keyword}",
        "Origin": "https://www.ajio.com",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    max_cookie_attempts = 3  # Increased attempts
    for attempt in range(max_cookie_attempts):
        debug_print(f"Cookie attempt {attempt+1}/{max_cookie_attempts}", debug)
        session_data = get_cookie(SITE)
        if session_data is None:
            print("❌ Failed to acquire cookies.")
            debug_print(f"Session acquisition failed", debug)
            # Wait before next attempt
            if attempt < max_cookie_attempts - 1:
                time.sleep(3)
            continue
            
        cookies_list = session_data["cookies"]
        session_id = session_data["session_id"]
        debug_print(f"Session acquired - ID: {session_id}, Cookies count: {len(cookies_list)}", debug)
        cookies = {cookie['name']: cookie['value'] for cookie in cookies_list}
        
        try:
            debug_print(f"Making HTTP request to Ajio API", debug)
            
            # Create a session for better connection handling
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(url, cookies=cookies, timeout=30)
            debug_print(f"Response received - Status code: {response.status_code}", debug)
            
            if response.status_code == 200:
                debug_print(f"Request successful, extracting data", debug)
                try:
                    data = extract_data(response.json(), debug)
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
                print(f"⚠️  Got {response.status_code} - Forbidden or Unauthorized. Marking cookie unhealthy and retrying...")
                debug_print(f"Marking session as unhealthy and retrying", debug)
                report_cookie_status(session_id, False)
                
                # Progressive backoff
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
                
            else:
                print(f"❌ Request failed with status code: {response.status_code}")
                print("Response text:", response.text[:500])  # Print first 500 chars
                debug_print(f"Request failed, marking session as unhealthy", debug)
                report_cookie_status(session_id, False)
                break
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Request timeout on attempt {attempt + 1}")
            report_cookie_status(session_id, False)
            if attempt < max_cookie_attempts - 1:
                time.sleep(2)
            continue
            
        except Exception as e:
            print(f"Request exception: {e}")
            debug_print(f"HTTP request exception: {e}", debug)
            report_cookie_status(session_id, False)
            if attempt < max_cookie_attempts - 1:
                time.sleep(2)
            continue
            
    debug_print(f"All cookie attempts failed or exhausted", debug)
    return []

def scrape_first_2_pages(keyword, rows_per_page=50, debug=False):
    """Scrape the first 2 pages of products for a given keyword"""
    all_products = []
    total_pages = 2
    
    print(f"🚀 Starting to scrape first {total_pages} pages from Ajio for keyword: '{keyword}'")
    print(f"📄 Products per page: {rows_per_page}")
    print("🔧 USING ENHANCED AJIO SPIDER WITH MAXIMUM DETAILS EXTRACTION")
    print("=" * 60)
    
    for page in range(1, total_pages + 1):
        print(f"📖 Scraping Ajio page {page}/{total_pages}...")
        
        # Call the existing product_search function
        page_products = product_search(keyword, page, rows_per_page, debug=debug)
        
        if page_products:
            all_products.extend(page_products)
            print(f"✅ Ajio page {page} completed - Found {len(page_products)} products")
            
            # Print image stats for debugging
            images_found = sum(1 for product in page_products if product.get('image_url'))
            print(f"   📸 Products with images on this page: {images_found}/{len(page_products)}")
        else:
            print(f"❌ Ajio page {page} failed or returned no products")
        
        # Add a delay between requests to be respectful
        if page < total_pages:
            wait_time = 3 + (page * 0.5)  # Progressive delay
            print(f"⏳ Waiting {wait_time:.1f}s before next page...")
            time.sleep(wait_time)
        
        print("-" * 40)
    
    print(f"🎉 Ajio scraping completed!")
    print(f"📊 Total products collected from Ajio: {len(all_products)}")
    
    # Final image statistics
    total_images = sum(1 for product in all_products if product.get('image_url'))
    print(f"📸 Products with images: {total_images}/{len(all_products)}")
    print("=" * 60)
    
    return all_products

def scrape(query):
    return scrape_first_2_pages(query)

def main(query, output_file="ajio_products.json", debug=False):
    """
    Main function to scrape Ajio and save results to a JSON file.
    
    Args:
        query (str): Search keyword
        output_file (str): Output JSON file path
        debug (bool): Enable debug mode
    
    Returns:
        dict: Dictionary with status and file path
    """
    print(f"🎯 Starting Ajio scraper for query: '{query}'")
    print(f"💾 Output file: {output_file}")
    print("=" * 60)
    
    # Scrape products
    products = scrape_first_2_pages(query, rows_per_page=50, debug=debug)
    
    if not products:
        print("❌ No products found or scraping failed")
        return {
            "status": "failed",
            "message": "No products found",
            "products_count": 0,
            "file": None
        }
    
    # Save to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Successfully saved {len(products)} products to {output_file}")
        
        return {
            "status": "success",
            "message": f"Successfully scraped {len(products)} products",
            "products_count": len(products),
            "file": output_file,
            "data": products
        }
    
    except Exception as e:
        print(f"❌ Error saving to JSON: {e}")
        return {
            "status": "error",
            "message": f"Error saving to JSON: {e}",
            "products_count": len(products),
            "file": None,
            "data": products
        }

if __name__ == "__main__":
    # Example usage
    result = main("shoes", output_file="ajio_shoes.json", debug=False)
    print(f"\n📋 Final Result: {result['status']}")
    print(f"📊 Products Count: {result['products_count']}")
    if result['file']:
        print(f"💾 File Location: {result['file']}")