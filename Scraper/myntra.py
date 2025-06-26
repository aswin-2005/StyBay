import requests
from cookie_manager import lock_session, release_session
import json

SITE = "myntra"


def extract_data(response: dict) -> list[dict]:
    """
    Transform Myntra's raw API payload into a list of normalized product dicts.
    """
    extracted_data = []

    for product in response.get("products", []):
        item = {
            "source": "Myntra",
            "title": product.get("product"),
            "description": product.get("additionalInfo"),
            "product_url": f"https://myntra.com/{product.get('landingPageUrl', '').lstrip('/')}",
            "image_urls": [img.get("src") for img in product.get("imageUrls", [])],
            "price": product.get("price"),
            "rating": product.get("rating"),
        }
        extracted_data.append(item)

    return extracted_data




def product_search(keyword, offset, rows, retry_if_forbidden=True):

    sanitized_keyword = keyword.replace(" ", "%20")


    url = f"https://www.myntra.com/gateway/v2/search/{sanitized_keyword}?rows={rows}&o={offset}"
    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0"
    }

    try:
        session_data = lock_session(SITE)
        if session_data is None:
            print("❌ Failed to acquire cookies.")
            return []

        cookies_list, session_id = session_data
        cookies = {cookie['name']: cookie['value'] for cookie in cookies_list}
    except Exception as e:
        print(f"Failed to load cookies{e}")

    response = requests.get(url, headers=headers, cookies=cookies)

    if response.status_code == 200:

        data = extract_data(response.json())
        release_session(session_id, 'healthy')
        return data

    elif response.status_code in [401, 403] and retry_if_forbidden:
        print(f"⚠️ Got {response.status_code} - Forbidden or Unauthorized. Refreshing cookies and retrying...")
        release_session(session_id, 'unhealthy')
        return product_search(keyword, offset, rows, retry_if_forbidden=False)
    else:
        print(f"❌ Request failed with status code: {response.status_code}")
        print("Response text:", response.text)
        return None