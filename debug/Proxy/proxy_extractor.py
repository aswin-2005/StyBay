import requests
from time import time, sleep


# Constants
PROXY_API_URL = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=https&ssl=yes&timeout=10000&country=all&ssl=all&anonymity=all"
CACHE_TTL = 600  # 10 minutes in seconds


# In-memory cache for recently used proxies
proxy_cache = {}  # Format: {proxy_ip: timestamp_last_used}



def is_proxy_stale(proxy_ip):
    """Check if a proxy has not been used recently or is expired in cache."""
    now = time()
    return proxy_ip not in proxy_cache or (now - proxy_cache[proxy_ip]) > CACHE_TTL



def get_proxy_list():
    """Fetch the proxy list from ProxyScrape API."""
    try:
        response = requests.get(PROXY_API_URL)
        if response.status_code == 200:
            proxies = response.text.strip().split('\n')
            proxies = [proxy.strip() for proxy in proxies if proxy.strip()]
            return proxies
        else:
            print(f"[!] Failed to fetch proxies. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"[!] Error fetching proxies: {str(e)}")
        return []



def get_fresh_proxy():
    """Return the first fresh (stale or unused) proxy from the list."""
    proxies = get_proxy_list()
    for proxy in proxies:
        if is_proxy_stale(proxy):
            proxy_cache[proxy] = time()  # Mark as used
            print(f"[+] Using proxy: {proxy}")
            return proxy

    print("[!] No fresh proxies found. Consider increasing TTL or waiting.")
    return None



def validate_proxy(proxy):
    """Optional: Validate proxy with a test request (e.g., httpbin.org/ip)"""
    try:
        test_url = "http://httpbin.org/ip"
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}",
        }
        r = requests.get(test_url, proxies=proxies, timeout=5)
        if r.status_code == 200:
            print(f"[✓] Proxy {proxy} is working.")
            return True
    except:
        pass

    print(f"[x] Proxy {proxy} failed.")
    return False



def get_proxy():
    while True:
        proxy = get_fresh_proxy()
        if proxy and validate_proxy(proxy):
            # Use proxy for actual request logic here
            print(f"[→] Ready to use: {proxy}")
            return proxy
        else:
            print("[…] Retrying...")
            sleep(1)