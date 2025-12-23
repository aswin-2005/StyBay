from playwright.sync_api import sync_playwright
import random
import time
import json
from datetime import datetime
import os

DEBUG_DIR = "cookie_debug"

def create_cookies(site):
    if site == 'ajio':
        return create_ajio_cookies()
    elif site == 'myntra':  
        return create_myntra_cookies()
    elif site == 'flipkart':
        return create_flipkart_cookies()
    return None

def _random_delay(min_sec=2, max_sec=4.5):
    time.sleep(random.uniform(min_sec, max_sec))

def _human_like_mouse_movement(page):
    """Simulate human-like mouse movements"""
    for _ in range(random.randint(2, 4)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        page.mouse.move(x, y, steps=random.randint(10, 30))
        time.sleep(random.uniform(0.1, 0.3))

def create_ajio_cookies():
    """Enhanced Ajio cookie generation with better session establishment"""
    try:
        with sync_playwright() as p:
            # Use Chromium instead of Firefox - generally better for scraping
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            
            # More realistic browser context
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-IN",
                timezone_id="Asia/Kolkata",
                viewport={"width": 1920, "height": 1080},
                color_scheme="light",
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False,
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                }
            )
            
            # Hide automation indicators
            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                window.chrome = { runtime: {} };
            """)
            
            print("🌐 Navigating to Ajio homepage...")
            _random_delay(1, 2)
            
            # Navigate to homepage
            page.goto("https://www.ajio.com", wait_until="networkidle", timeout=30000)
            _random_delay(2, 3)
            
            # Simulate human behavior
            print("🖱️  Simulating human interactions...")
            _human_like_mouse_movement(page)
            
            # Scroll a bit
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
            _random_delay(1, 2)
            
            # Try to interact with the page (hover over elements)
            try:
                # Look for any clickable element and hover
                page.hover("a", timeout=5000)
            except:
                pass
            
            _random_delay(2, 3)
            
            # Perform a search to establish better session
            try:
                print("🔍 Performing search to establish session...")
                page.goto("https://www.ajio.com/search/?text=shoes", wait_until="domcontentloaded", timeout=30000)
                _random_delay(2, 4)
                _human_like_mouse_movement(page)
            except Exception as e:
                print(f"⚠️  Search page navigation failed: {e}")
            
            # Get cookies
            raw_cookies = context.cookies()
            
            print(f"✅ Collected {len(raw_cookies)} cookies for Ajio")
            
            browser.close()
            
            return raw_cookies

    except Exception as e:
        print(f"❌ Failed to create Ajio session: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_myntra_cookies():
    """Original Myntra cookie logic - unchanged"""
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
                locale="en-US",
                timezone_id="Asia/Kolkata",
                viewport={"width": 1366, "height": 768},
                color_scheme="light"
            )
            page = context.new_page()
            _random_delay()
            page.goto("https://www.myntra.com", wait_until="domcontentloaded")
            page.mouse.move(100, 100)
            time.sleep(3)
            raw_cookies = context.cookies()
            browser.close()

            return raw_cookies

    except Exception as e:
        print(f"❌ Failed to create Myntra session: {e}")
        return None

def create_flipkart_cookies():
    """Original Flipkart cookie logic - unchanged"""
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
                locale="en-US",
                timezone_id="Asia/Kolkata",
                viewport={"width": 1366, "height": 768},
                color_scheme="light"
            )
            page = context.new_page()
            _random_delay()
            page.goto("https://www.flipkart.com", wait_until="domcontentloaded")
            page.mouse.move(150, 150)
            time.sleep(3)
            raw_cookies = context.cookies()
            browser.close()

            return raw_cookies

    except Exception as e:
        print(f"❌ Failed to create Flipkart session: {e}")
        return None