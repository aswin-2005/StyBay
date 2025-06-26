from CookieJar.database import add_to_db
import json

with open('myntra_cookies.json', 'r') as f:
    session = json.load(f)

add_to_db(session)