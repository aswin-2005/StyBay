from playwright.sync_api import sync_playwright
import time, json

def main():
    with sync_playwright() as p:
        # 1. Launch Firefox in headless mode (stealthy)
        browser = p.firefox.launch(headless=True)

        # 2. Create a stealthy, human-like browser context
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
            locale="en-US",
            timezone_id="Asia/Kolkata",
            viewport={"width": 1366, "height": 768},
            color_scheme="light",
        )

        # 3. Open a new page
        page = context.new_page()

        # 4. Add a small random delay to mimic human delay
        time.sleep(2 + (1 * time.time() % 1))

        # 5. Navigate to the target site
        page.goto("https://www.myntra.com", wait_until="domcontentloaded")
        print("[✔] Page loaded successfully.")

        # 6. Simulate a user hovering or clicking (optional but human-like)
        try:
            page.mouse.move(100, 100)
            time.sleep(1)
        except:
            pass

        # 7. Wait for cookies and scripts to settle
        time.sleep(5)

        # 8. Save cookies for reuse
        cookies = context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
        print(f"[✔] Saved {len(cookies)} cookies.")

        browser.close()

if __name__ == "__main__":
    main()
