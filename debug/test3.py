import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Setup options
options = uc.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

print("Launching headless UC Chrome...")

driver = uc.Chrome(options=options)
driver.get("https://www.myntra.com")
WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="item rilrtl-products-list__item"]'))
)

# Allow time for JavaScript to run and cookies to be set
time.sleep(5)

# Simulate a scroll to trigger more activity
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# Grab cookies
# cookies = driver.get_cookies()

# Print count and cookie content
print("Number of cookies:", len(cookies))
for cookie in cookies:
    print(cookie)

driver.quit()
