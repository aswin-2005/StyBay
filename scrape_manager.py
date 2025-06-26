import Scraper.amazon as amazon
import Scraper.myntra as myntra
import Scraper.ajio as ajio
import json


amazon_resp = amazon.product_search("Red Shirt", 1)
print(f"amazon response generated {len(amazon_resp)} items")
myntra_resp = myntra.product_search("Red Shirt", 0, 50)
print(f"myntra response generated {len(myntra_resp)} items")
ajio_resp = ajio.product_search("Red Shirt", 0, 50)
print(f"ajio response generated {len(ajio_resp)} items")

with open('amazon_response.json', 'w') as f:
    json.dump(amazon_resp, f, indent=2, ensure_ascii=False)
print("amazon response saved")
with open('myntra_response.json', 'w') as f:
    json.dump(myntra_resp, f, indent=2, ensure_ascii=False)
print("myntra response saved")
with open('ajio_response.json', 'w') as f:
    json.dump(ajio_resp, f, indent=2, ensure_ascii=False)
print("ajio response saved")
print("All responses saved successfully.")