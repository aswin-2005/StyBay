import asyncio
import json
from Cookie.harvester import create_cookies
from Cookie.database import add_cookie


async def gather_cookies_and_store(site: str, file_name: str):
    cookies = await create_cookies(site)
    if cookies:
        with open(file_name, 'w') as f:
            json.dump(cookies, f, indent=4)
        add_cookie(cookies)
        print(f"[✔] Stored cookies for {site}")
    else:
        print(f"[✘] Failed to fetch cookies for {site}")

async def main():
    await asyncio.gather(
        gather_cookies_and_store('myntra', 'myntra_cookies.json'),
        gather_cookies_and_store('ajio', 'ajio_cookies.json')
    )

if __name__ == "__main__":
    asyncio.run(main())
