import requests
from cookie_manager import lock_session, release_session

SITE = "ajio"


def extract_data(response):
    extracted_data = []

    for product in response.get("products", []):
        try:
            item = {
                "source": "Ajio",
                "title": product.get("name"),
                "description": product.get("fnlColorVariantData", {}).get("brandName"),
                "product_url": f"https://www.ajio.com/{product.get('url', '').lstrip('/')}",
                "image_urls": [
                    img.get("images", {}).get("url")
                    for img in product.get("extraImages", [])
                    if "images" in img and "url" in img["images"]
                ],
                "price": product.get("price", {}).get("value")
            }
            extracted_data.append(item)
        except Exception as e:
            # Optional: log or print to debug faulty items
            print(f"Skipping product due to error: {e}")

    return extracted_data




def product_search(keyword, offset, rows, retry_if_forbidden=True):

    sanitized_keyword = keyword.replace(" ", "%20")


    url = f"https://www.ajio.com/api/search?query={sanitized_keyword}&format=json&pageSize={rows}&currentPage={offset}"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "accept": "application/json",
        "referer": "https://www.ajio.com/search/?text={sanitized_keyword}"
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