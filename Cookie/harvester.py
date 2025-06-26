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
    return None

def _random_delay():
    time.sleep(random.uniform(2, 4.5))

# def dump_cookies(site, cookies):
#     if cookies:
#         os.makedirs(DEBUG_DIR, exist_ok=True)
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"{DEBUG_DIR}/{site}_cookies_{timestamp}.json"
#         try:
#             with open(filename, "w", encoding='utf-8') as f:
#                 json.dump(cookies, f, indent=2)
#             print(f"✅ Cookies dumped to {filename}")
#         except Exception as e:
#             print(f"❌ Failed to write cookie debug file: {e}")

def create_myntra_cookies():
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

            # dump_cookies("myntra", raw_cookies)  # 🪵 Debugging line
            return raw_cookies

    except Exception as e:
        print(f"❌ Failed to create Myntra session: {e}")
        return None

def create_ajio_cookies():
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
            page.goto("https://www.ajio.com", wait_until="domcontentloaded")
            page.mouse.move(120, 120)
            time.sleep(3)
            raw_cookies = context.cookies()
            browser.close()

            # dump_cookies("ajio", raw_cookies)  # 🪵 Debugging line
            return raw_cookies

    except Exception as e:
        print(f"❌ Failed to create Ajio session: {e}")
        return None
