import requests
import json

with open("cookies.json", "r") as r:
    cookie_list = json.load(r)  # ✅ parse JSON into dict

cookies = {cookie['name']: cookie['value'] for cookie in cookie_list}

url = "https://www.ajio.com/api/search?query=red%20shirts&format=json&pageSize=50&currentPage=0"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "accept": "application/json",
    "referer": "https://www.ajio.com/search/?text=red%20shirts"
}

response = requests.get(url, headers=headers, cookies=cookies)

with open("output.json", "w") as w:
    json.dump(response.json(), w, indent=4)

print(f"Status Code: {response.status_code}")
