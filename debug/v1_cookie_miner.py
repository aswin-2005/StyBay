import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import random
import time
import uuid
from datetime import datetime

# from Proxy.proxy_extractor import get_proxy

def create_cookies(site):
    if site is None:
        return None
    elif site == 'ajio':
        return create_ajio_cookies()
    elif site == 'myntra':
        return create_myntra_cookies()

def _random_delay():
    """Add a random delay between 2 to 5 seconds to simulate human behavior"""
    time.sleep(random.uniform(2, 5))

def _get_uc_driver():
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")  # or use "--headless" if this fails
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    #  DO NOT pass headless=True here (that breaks uc.Chrome)
    driver = uc.Chrome(options=options)  
    return driver

def create_myntra_cookies():
    raw_cookies = []
    session = None
    driver = _get_uc_driver()

    try:
        _random_delay()
        driver.get("https://www.myntra.com")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "myntraweb-sprite.desktop-logo"))
        )
        _random_delay()
        raw_cookies = driver.get_cookies()
        session = assemble_schema('myntra', raw_cookies)

    except Exception as e:
        print(f"Failed to create session: {e}")

    finally:
        driver.quit()
        return session

def create_ajio_cookies():
    raw_cookies = []
    session = None
    driver = _get_uc_driver()

    try:
        _random_delay()
        driver.get("https://www.ajio.com")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "app"))
        )
        _random_delay()
        raw_cookies = driver.get_cookies()
        session = assemble_schema('ajio', raw_cookies)

    except Exception as e:
        print(f"Failed to create session: {e}")

    finally:
        driver.quit()
        return session

def assemble_schema(site, raw_cookies):
    least_expiry = min([cookie['expiry'] for cookie in raw_cookies if 'expiry' in cookie], default=None)
    session_id = f"{site}_{uuid.uuid4()}"
    session = {
        'session_id': session_id,
        'site': f'{site}.com',
        'cookies': raw_cookies,
        'session_expiry': least_expiry,
        'created_at': datetime.utcnow().isoformat(),
        'last_used_at': None,
        'usage_count': 0
    }
    return session
