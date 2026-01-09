import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from Scraper.cookie_manager import get_cookie, report_cookie_status
import json
import time
import uuid
import re

SITE = "flipkart"

def debug_print(message, debug=False):
    """Optional descriptive debug function"""
    if debug:
        print(f"🔍 DEBUG: {message}")

def save_html_debug(html_content, filename="flipkart_debug.html"):
    """Save HTML for debugging"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 HTML saved to {filename} for debugging")
    except Exception as e:
        print(f"❌ Failed to save HTML: {e}")

def clean_price(price_text):
    """Extract numeric price from text like '₹24,999' or '₹24999'"""
    if not price_text:
        return None
    cleaned = re.sub(r'[^\d.]', '', price_text)
    try:
        return float(cleaned)
    except:
        return None

def extract_main_image(product, debug=False):
    """Extract the main image URL from Flipkart product element"""
    img_elem = product.find("img")
    
    if img_elem:
        image_url = img_elem.get("src") or img_elem.get("data-src")
        
        # Also check srcset
        if not image_url or not image_url.startswith("http"):
            srcset = img_elem.get('srcset', '')
            if srcset:
                urls = re.findall(r'(https?://[^\s,]+)', srcset)
                if urls:
                    image_url = urls[0]
        
        if image_url:
            # Handle protocol-relative URLs
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            if image_url.startswith("http"):
                if debug:
                    debug_print(f"Found main image: {image_url}", debug)
                return image_url
    
    if debug:
        debug_print("No main image found", debug)
    return None

def extract_product_data(product, debug=False):
    """Extract all available data from a single product element"""
    try:
        # Find product link - multiple selector attempts
        link_elem = product.select_one("a.CJa1a1")
        if not link_elem:
            link_elem = product.find("a", title=True)
        if not link_elem:
            link_elem = product.find("a", href=re.compile(r'/p/'))
        
        if not link_elem:
            return None
        
        # Extract title
        title = link_elem.get("title", "").strip()
        if not title:
            title = link_elem.get_text(strip=True)
        
        if not title or len(title) < 5:
            return None
        
        # Extract URL
        href = link_elem.get("href", "")
        if href.startswith("http"):
            product_url = href
        elif href.startswith("/"):
            product_url = "https://www.flipkart.com" + href
        else:
            product_url = "https://www.flipkart.com/" + href
        
        # Extract image
        image_url = extract_main_image(product, debug)
        
        # Extract price - multiple selectors based on the document
        price = None
        price_selectors = [
            "div.hZ3P6w",      # Current selling price - PRIMARY
            "div.Nx9bqj",
            "div._30jeq3",
            "div._25b18c",
            "div.hl05eU"
        ]
        
        for selector in price_selectors:
            price_elem = product.select_one(selector)
            if price_elem:
                try:
                    price_text = price_elem.get_text(strip=True)
                    price = clean_price(price_text)
                    if price:
                        break
                except ValueError:
                    continue
        
        # Extract MRP/original price
        mrp = None
        mrp_selectors = [
            "div.kRYCnD",      # Original price
            "div.yRaY8j",
            "div._3I9_wc._2p6lqe"
        ]
        
        for selector in mrp_selectors:
            mrp_elem = product.select_one(selector)
            if mrp_elem:
                try:
                    mrp_text = mrp_elem.get_text(strip=True)
                    mrp = clean_price(mrp_text)
                    if mrp and mrp > (price or 0):  # MRP should be higher than price
                        break
                except ValueError:
                    continue
        
        # Extract discount
        discount = None
        discount_selectors = [
            "div.UkUFwK",
            "div._3Ay6sb._31Dcoz",
            "div._3xFx9d"
        ]
        
        for selector in discount_selectors:
            discount_elem = product.select_one(selector)
            if discount_elem:
                discount_text = discount_elem.get_text(strip=True)
                discount_match = re.search(r'\b([1-9][0-9]?)%\s*off\b', discount_text, re.IGNORECASE)
                if discount_match:
                    discount = int(discount_match.group(1))
                    if 1 <= discount <= 99:
                        break
        
        # Extract rating - multiple selectors
        rating = None
        rating_selectors = [
            "div.XQDdHH",
            "div._3LWZlK",
            "span._1lRcqv",
            "div.XQDdHH.Ga3i8K",
            "span.XQDdHH"
        ]
        
        for selector in rating_selectors:
            rating_elem = product.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating_str = rating_text.replace('★', '').replace('⭐', '').strip()
                    rating_val = float(rating_str)
                    if 1.0 <= rating_val <= 5.0:
                        rating = rating_val
                        break
                except ValueError:
                    continue
        
        # Extract reviews count
        reviews_count = None
        reviews_selectors = [
            "span.Wphh3N",
            "span._2_R_DZ",
            "span._13vcmD"
        ]
        
        for selector in reviews_selectors:
            reviews_elem = product.select_one(selector)
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_match = re.search(r'([\d,]+)\s*(?:Rating|Review)', reviews_text, re.IGNORECASE)
                if reviews_match:
                    reviews_count = int(reviews_match.group(1).replace(',', ''))
                    break
        
        # Extract description/brand
        description = None
        desc_selectors = [
            "div.FoI10b",
            "div._3Djpdu",
            "ul._1xgFaf"
        ]
        
        for selector in desc_selectors:
            desc_elem = product.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text(strip=True)
                if description:
                    break
        
        # Extract highlights
        highlights = []
        highlight_elems = product.select("ul.G4BRas li, div._1xgFaf ul li, ul._1xgFaf li")
        if highlight_elems:
            highlights = [elem.get_text(strip=True) for elem in highlight_elems]
        
        # Extract offers
        offers = []
        offer_elems = product.select("div._3xFx9d, div.UPUrh")
        if offer_elems:
            offers = [elem.get_text(strip=True) for elem in offer_elems if elem.get_text(strip=True)]
        
        # Extract delivery info
        delivery_info = None
        delivery_selectors = ["div.eFQ30H", "div._2Tpdn3"]
        for selector in delivery_selectors:
            delivery_elem = product.select_one(selector)
            if delivery_elem:
                delivery_info = delivery_elem.get_text(strip=True)
                break
        
        # Extract tags
        tags = []
        tag_elems = product.select("div._16ZfEf, div._3LU4EM")
        if tag_elems:
            tags = [elem.get_text(strip=True) for elem in tag_elems if elem.get_text(strip=True)]
        
        return {
            'title': title,
            'product_url': product_url,
            'image_url': image_url,
            'price': price,
            'mrp': mrp,
            'discount_percentage': discount,
            'rating': rating,
            'reviews_count': reviews_count,
            'description': description,
            'highlights': highlights if highlights else None,
            'offers': offers if offers else None,
            'delivery_info': delivery_info,
            'tags': tags if tags else None
        }
        
    except Exception as e:
        if debug:
            debug_print(f"Error extracting product: {e}", debug)
        return None

def extract_data(html_content, debug=False):
    """Extract product data from Flipkart search results HTML"""
    debug_print(f"Starting data extraction from HTML", debug)
    extracted_data = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find products using data-id attribute first (most reliable)
        products = soup.select("div[data-id]")
        
        if not products:
            # Fallback to class-based selectors
            products = soup.select("div.bLCLBY")
        
        if not products:
            # Find all divs that contain product links
            all_product_links = soup.find_all('a', href=re.compile(r'/p/'))
            debug_print(f"Found {len(all_product_links)} product links", debug)
            
            # Get parent containers
            seen_products = set()
            product_containers = []
            
            for link in all_product_links:
                parent = link.parent
                for _ in range(5):
                    if parent is None:
                        break
                    if parent.name == 'div':
                        html_str = str(parent)[:100]
                        if html_str not in seen_products:
                            seen_products.add(html_str)
                            product_containers.append(parent)
                            break
                    parent = parent.parent
            
            products = product_containers
        
        debug_print(f"Found {len(products)} product containers", debug)
        
        if len(products) < 5 and debug:
            save_html_debug(html_content)
        
        for i, product in enumerate(products):
            product_data = extract_product_data(product, debug)
            
            if product_data and product_data.get('title') and product_data.get('product_url'):
                # Build comprehensive product dictionary
                item = {
                    # Basic Info
                    "source": "Flipkart",
                    "product_id": str(uuid.uuid4()),
                    
                    # Product Details
                    "title": product_data.get('title'),
                    "brand": None,  # Brand extraction is difficult from search results
                    "description": product_data.get('description'),
                    
                    # URLs
                    "product_url": product_data.get('product_url'),
                    
                    # Images
                    "image_url": product_data.get('image_url'),
                    
                    # Pricing
                    "price": product_data.get('price'),
                    "mrp": product_data.get('mrp'),
                    "discount_percentage": product_data.get('discount_percentage'),
                    
                    # Rating & Reviews
                    "rating": product_data.get('rating'),
                    "reviews_count": product_data.get('reviews_count'),
                    
                    # Additional Details
                    "highlights": product_data.get('highlights'),
                    "offers": product_data.get('offers'),
                    "delivery_info": product_data.get('delivery_info'),
                    "tags": product_data.get('tags'),
                }
                
                extracted_data.append(item)
                
                if debug and i < 3:
                    debug_print(f"Product {i+1}: {item['title'][:60]}... - ₹{item['price']} - Rating: {item['rating']}", debug)
        
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        if debug:
            import traceback
            traceback.print_exc()
    
    debug_print(f"Extraction completed. Total products extracted: {len(extracted_data)}", debug)
    return extracted_data

def product_search(keyword, page, rows, debug=False):
    """Search Flipkart for products"""
    debug_print(f"Starting Flipkart product search for keyword: '{keyword}'", debug)
    debug_print(f"Search parameters - Page: {page}, Rows per page: {rows}", debug)
    
    if not keyword or not isinstance(keyword, str):
        print("❌ Invalid keyword provided")
        return []
    
    if not isinstance(page, int) or page < 1:
        print("❌ Invalid page number")
        return []
    
    sanitized_keyword = quote(keyword)
    url = f"https://www.flipkart.com/search?q={sanitized_keyword}&page={page}"
    debug_print(f"Request URL: {url}", debug)
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.flipkart.com/"
    }

    max_cookie_attempts = 2
    for attempt in range(max_cookie_attempts):
        debug_print(f"Cookie attempt {attempt+1}/{max_cookie_attempts}", debug)
        session_data = get_cookie(SITE)
        if session_data is None:
            print("❌ Failed to acquire cookies.")
            continue
        
        cookies_list = session_data["cookies"]
        session_id = session_data["session_id"]
        debug_print(f"Session acquired - ID: {session_id}, Cookies count: {len(cookies_list)}", debug)
        cookies = {cookie['name']: cookie['value'] for cookie in cookies_list}
        
        try:
            debug_print(f"Making HTTP request to Flipkart", debug)
            response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            debug_print(f"Response received - Status code: {response.status_code}", debug)
            
            if response.status_code == 200:
                debug_print(f"Request successful, extracting data", debug)
                try:
                    data = extract_data(response.text, debug)
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
                report_cookie_status(session_id, False)
                time.sleep(1)
                continue
            else:
                print(f"❌ Request failed with status code: {response.status_code}")
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
    
    print(f"🚀 Starting to scrape first {total_pages} pages from Flipkart for keyword: '{keyword}'")
    print(f"📄 Products per page: ~{rows_per_page} (Flipkart determines actual count)")
    print("🔧 USING ENHANCED FLIPKART SPIDER WITH MAXIMUM DETAILS EXTRACTION")
    print("=" * 60)
    
    for page in range(1, total_pages + 1):
        print(f"📖 Scraping Flipkart page {page}/{total_pages}...")
        
        page_products = product_search(keyword, page, rows_per_page, debug=debug)
        
        if page_products:
            all_products.extend(page_products)
            print(f"✅ Flipkart page {page} completed - Found {len(page_products)} products")
            
            images_found = sum(1 for product in page_products if product.get('image_url'))
            ratings_found = sum(1 for product in page_products if product.get('rating'))
            print(f"   📸 Products with images: {images_found}/{len(page_products)}")
            print(f"   ⭐ Products with ratings: {ratings_found}/{len(page_products)}")
        else:
            print(f"❌ Flipkart page {page} failed or returned no products")
        
        if page < total_pages:
            time.sleep(2)
        
        print("-" * 40)
    
    print(f"🎉 Flipkart scraping completed!")
    print(f"📊 Total products collected from Flipkart: {len(all_products)}")
    
    total_images = sum(1 for product in all_products if product.get('image_url'))
    total_ratings = sum(1 for product in all_products if product.get('rating'))
    print(f"📸 Products with images: {total_images}/{len(all_products)}")
    print(f"⭐ Products with ratings: {total_ratings}/{len(all_products)}")
    print("=" * 60)
    
    return all_products

def scrape(query):
    return scrape_first_2_pages(query)

def main(query, output_file="flipkart_products.json", debug=False):
    """
    Main function to scrape Flipkart and save results to a JSON file.
    
    Args:
        query (str): Search keyword
        output_file (str): Output JSON file path
        debug (bool): Enable debug mode
    
    Returns:
        dict: Dictionary with status and file path
    """
    print(f"🎯 Starting Flipkart scraper for query: '{query}'")
    print(f"💾 Output file: {output_file}")
    print("=" * 60)
    
    products = scrape_first_2_pages(query, rows_per_page=50, debug=debug)
    
    if not products:
        print("❌ No products found or scraping failed")
        return {
            "status": "failed",
            "message": "No products found",
            "products_count": 0,
            "file": None
        }
    
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
    result = main("t shirts", output_file="flipkart_tshirts.json", debug=True)
    print(f"\n📋 Final Result: {result['status']}")
    print(f"📊 Products Count: {result['products_count']}")
    if result['file']:
        print(f"💾 File Location: {result['file']}")