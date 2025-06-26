import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

def scroll_to_bottom(driver, pause_time=2, max_scrolls=20):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_ajio_products(query):
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36")

    driver = uc.Chrome(options=options)
    results = []

    try:
        driver.get(f"https://www.ajio.com/search/?text={query}")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="item rilrtl-products-list__item"]'))
        )

        scroll_to_bottom(driver)

        product_elements = driver.find_elements(By.CSS_SELECTOR, 'div[class*="item rilrtl-products-list__item"]')

        for product in product_elements:
            try:
                brand = product.find_element(By.CSS_SELECTOR, 'div[class*="brand"]').text
                title = product.find_element(By.CSS_SELECTOR, 'div[class*="name"]').text
                price = product.find_element(By.CSS_SELECTOR, 'span[class*="price"]').text
                link = product.find_element(By.TAG_NAME, 'a').get_attribute('href')

                results.append({
                    'brand': brand,
                    'title': title,
                    'price': price,
                    'link': link
                })
            except Exception:
                continue

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        driver.quit()

    return results

if __name__ == "__main__":
    query = "shirt"
    products = scrape_ajio_products(query)

    with open("ajio_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(products)} products to 'ajio_products.json'")
