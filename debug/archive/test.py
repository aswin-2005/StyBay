from CookieJar.cookie_miner import create_cookies
from CookieJar.database import add_to_db
import json

# Get Myntra cookies and save them to a file
myntra_cookies = create_cookies('myntra')
with open('myntra_cookies.json', 'w') as f:
    json.dump(myntra_cookies, f, indent=4)
    if myntra_cookies:
        print("Total cookies collected:", len(myntra_cookies['cookies']))
    else:
        print("No cookies generated.")