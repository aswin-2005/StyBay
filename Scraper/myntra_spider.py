import requests
from Scraper.cookie_manager import get_cookie, report_cookie_status
import json
import time
import uuid

SITE = "myntra"

def debug_print(message, debug=False):
    """debug function"""
    if debug:
        print(f"🔍 DEBUG: {message}")

def extract_main_image(product, debug=False):
    """Extract just the first available image URL from product data"""
    
    # Priority 1: Get the first image from imageUrls array
    image_urls = product.get("imageUrls", [])
    if image_urls:
        if isinstance(image_urls, list) and len(image_urls) > 0:
            first_img = image_urls[0]
            
            # Case 1: Direct string URL
            if isinstance(first_img, str) and first_img.startswith("http"):
                if debug:
                    debug_print(f"Found main image from imageUrls: {first_img}", debug)
                return first_img
            
            # Case 2: Dict with 'src' key
            elif isinstance(first_img, dict) and first_img.get("src"):
                main_image = first_img["src"]
                if main_image and isinstance(main_image, str) and main_image.startswith("http"):
                    if debug:
                        debug_print(f"Found main image from imageUrls.src: {main_image}", debug)
                    return main_image
            
            # Case 3: Dict with 'url' key
            elif isinstance(first_img, dict) and first_img.get("url"):
                main_image = first_img["url"]
                if main_image and isinstance(main_image, str) and main_image.startswith("http"):
                    if debug:
                        debug_print(f"Found main image from imageUrls.url: {main_image}", debug)
                    return main_image
        
        # Case 4: imageUrls is a direct string
        elif isinstance(image_urls, str) and image_urls.startswith("http"):
            if debug:
                debug_print(f"Found main image from imageUrls: {image_urls}", debug)
            return image_urls
    
    # Priority 2: Check for standard image fields (only the first one found)
    main_image_fields = ["image", "imageUrl", "thumbnail", "mainImage", "primaryImage", "defaultImage", "searchImage"]
    for field in main_image_fields:
        if field in product and product[field]:
            if isinstance(product[field], str) and product[field].startswith("http"):
                if debug:
                    debug_print(f"Found main image from {field}: {product[field]}", debug)
                return product[field]
            elif isinstance(product[field], dict):
                if "src" in product[field] and product[field]["src"]:
                    if debug:
                        debug_print(f"Found main image from {field}.src: {product[field]['src']}", debug)
                    return product[field]["src"]
                elif "url" in product[field] and product[field]["url"]:
                    if debug:
                        debug_print(f"Found main image from {field}.url: {product[field]['url']}", debug)
                    return product[field]["url"]
    
    if debug:
        debug_print("No main image found", debug)
    
    return None

def extract_all_images(product, debug=False):
    """Extract all available image URLs from product data"""
    all_images = []
    
    image_urls = product.get("imageUrls", [])
    if isinstance(image_urls, list):
        for img in image_urls:
            if isinstance(img, str) and img.startswith("http"):
                all_images.append(img)
            elif isinstance(img, dict):
                if img.get("src") and img["src"].startswith("http"):
                    all_images.append(img["src"])
                elif img.get("url") and img["url"].startswith("http"):
                    all_images.append(img["url"])
    
    return all_images if all_images else None

def extract_data(response: dict, debug=False) -> list[dict]:
    """
    Transform Myntra's raw API payload into a list of normalized product dicts with maximum details.
    """
    debug_print(f"Starting data extraction from response", debug)
    extracted_data = []
    products = response.get("products", [])
    debug_print(f"Found {len(products)} products in response", debug)
    
    for i, product in enumerate(products):
        if not isinstance(product, dict):
            debug_print(f"Skipping product {i+1} - not a valid dict", debug)
            continue
        
        debug_print(f"Processing product {i+1}: {product.get('product', 'Unknown')}", debug)
        
        # Extract main image and all images
        main_image = extract_main_image(product, debug)
        all_images = extract_all_images(product, debug)
        
        # Build comprehensive product dictionary
        item = {
            # Basic Info
            "source": "Myntra",
            "product_id": str(uuid.uuid4()),
            "myntra_product_id": product.get("productId"),
            "style_id": product.get("styleId"),
            
            # Product Details
            "title": product.get("product", ""),
            "brand": product.get("brand", ""),
            "description": product.get("additionalInfo", ""),
            "product_name": product.get("productName", ""),
            "product_display_name": product.get("productDisplayName", ""),
            
            # URLs
            "product_url": f"https://myntra.com/{product.get('landingPageUrl', '').lstrip('/')}",
            "landing_page_url": product.get("landingPageUrl", ""),
            
            # Images
            "image_url": main_image,
            "all_images": all_images,
            "search_image": product.get("searchImage", ""),
            
            # Pricing
            "price": product.get("price"),
            "mrp": product.get("mrp"),
            "discount_label": product.get("discountLabel", ""),
            "discount_display_label": product.get("discountDisplayLabel", ""),
            
            # Rating & Reviews
            "rating": product.get("rating"),
            "rating_count": product.get("ratingCount"),
            
            # Categories & Classification
            "category": product.get("category", ""),
            "sub_category": product.get("subCategory", ""),
            "article_type": product.get("articleType", ""),
            "master_category": product.get("masterCategory", ""),
            
            # Colors & Variants
            "primary_colour": product.get("primaryColour", ""),
            "colors": product.get("colours", []),
            "dominant_color": product.get("dominantColor", ""),
            "sizes": product.get("sizes", []),
            
            # Availability & Stock
            "in_stock": product.get("inStock"),
            "available_sizes": product.get("availableSizes", []),
            
            # Additional Metadata
            "gender": product.get("gender", ""),
            "age_group": product.get("ageGroup", ""),
            "season": product.get("season", ""),
            "year": product.get("year", ""),
            "usage": product.get("usage", ""),
            "base_colour": product.get("baseColour", ""),
            
            # Search & Display
            "search_rank": product.get("rank"),
            "is_sponsored": product.get("isSponsored", False),
            "product_type_by_gender": product.get("productTypeByGender", ""),
            
            # Raw data for any additional fields
            "raw_data": product  # Store complete raw data for reference
        }
        
        debug_print(f"Successfully extracted product {i+1}: {item['title']} - Price: {item['price']} - Image: {'✅' if main_image else '❌'}", debug)
        extracted_data.append(item)
    
    debug_print(f"Extraction completed. Total products extracted: {len(extracted_data)}", debug)
    
    return extracted_data

def product_search(keyword, offset, rows, debug=False):
    debug_print(f"Starting Myntra product search for keyword: '{keyword}'", debug)
    debug_print(f"Search parameters - Offset: {offset}, Rows: {rows}", debug)
    
    # Add validation at start
    if not keyword or not isinstance(keyword, str):
        print("❌ Invalid keyword provided")
        debug_print(f"Keyword validation failed: {keyword}", debug)
        return []
    
    if not isinstance(offset, int) or offset < 0:
        print("❌ Invalid offset provided")
        debug_print(f"Offset validation failed: {offset}", debug)
        return []
    
    if not isinstance(rows, int) or rows <= 0:
        print("❌ Invalid rows provided")
        debug_print(f"Rows validation failed: {rows}", debug)
        return []
    
    debug_print(f"Input validation passed", debug)
    
    sanitized_keyword = keyword.replace(" ", "%20")
    debug_print(f"Sanitized keyword: '{sanitized_keyword}'", debug)
    
    url = f"https://www.myntra.com/gateway/v2/search/{sanitized_keyword}?rows={rows}&o={offset}"
    debug_print(f"Request URL: {url}", debug)
    
    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0"
    }
    debug_print(f"Request headers prepared", debug)

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
            debug_print(f"Making HTTP request to Myntra API", debug)
            response = requests.get(url, headers=headers, cookies=cookies)
            debug_print(f"Response received - Status code: {response.status_code}", debug)
            if response.status_code == 200:
                debug_print(f"Request successful, extracting data", debug)
                try:
                    data = extract_data(response.json(), debug)
                    debug_print(f"Reporting session as healthy", debug)
                    report_cookie_status(session_id, True)
                    debug_print(f"Search completed successfully. Returning {len(data)} products", debug)
                    return data if data is not None else []
                except Exception as e:
                    print(f"Error extracting data: {e}")
                    debug_print(f"Data extraction failed: {e}", debug)
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
    """Scrape the first 2 pages of products for a given keyword from Myntra"""
    all_products = []
    total_pages = 2
    
    print(f"🚀 Starting to scrape first {total_pages} pages from Myntra for keyword: '{keyword}'")
    print(f"📄 Products per page: {rows_per_page}")
    print("🔧 USING ENHANCED MYNTRA SPIDER WITH MAXIMUM DETAILS EXTRACTION")
    print("=" * 60)
    
    for page in range(1, total_pages + 1):
        print(f"📖 Scraping Myntra page {page}/{total_pages}...")
        
        # Calculate offset for Myntra (they use 0-based offset)
        offset = (page - 1) * rows_per_page
        
        # Call the existing product_search function
        page_products = product_search(keyword, offset, rows_per_page, debug=debug)
        
        if page_products:
            all_products.extend(page_products)
            print(f"✅ Myntra page {page} completed - Found {len(page_products)} products")
            
            # Print image stats for debugging
            images_found = sum(1 for product in page_products if product.get('image_url'))
            print(f"   📸 Products with images on this page: {images_found}/{len(page_products)}")
        else:
            print(f"❌ Myntra page {page} failed or returned no products")
        
        # Add a small delay between requests to be respectful
        if page < total_pages:
            time.sleep(2)
        
        print("-" * 40)
    
    print(f"🎉 Myntra scraping completed!")
    print(f"📊 Total products collected from Myntra: {len(all_products)}")
    
    # Final image statistics
    total_images = sum(1 for product in all_products if product.get('image_url'))
    print(f"📸 Products with images: {total_images}/{len(all_products)}")
    
    print("=" * 60)
    
    return all_products

def scrape(query):
    return scrape_first_2_pages(query)

def main(query, output_file="myntra_products.json", debug=False):
    """
    Main function to scrape Myntra and save results to a JSON file.
    
    Args:
        query (str): Search keyword
        output_file (str): Output JSON file path
        debug (bool): Enable debug mode
    
    Returns:
        dict: Dictionary with status and file path
    """
    print(f"🎯 Starting Myntra scraper for query: '{query}'")
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
    result = main("shoes", output_file="myntra_shoes.json", debug=False)
    print(f"\n📋 Final Result: {result['status']}")
    print(f"📊 Products Count: {result['products_count']}")
    if result['file']:
        print(f"💾 File Location: {result['file']}")