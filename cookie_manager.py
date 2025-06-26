from Cookie.harvester import create_cookies
from Cookie.database import acquire_cookie, add_cookie, release_cookie


def lock_session(site):
    session = acquire_cookie(site)
    if session is None:
        cookies = create_cookies(site)
        response = add_cookie(cookies, site)
        if response is None:
            return None  # safer than returning 500
        # simulate a full session structure
        data = response.data[0]  # this is a list of rows
        return [data['cookies'], data['session_id']]
    return [session['cookies'], session['session_id']]


def release_session(session_id, validity):
    response = release_cookie(session_id, validity)
    if not response or len(response.data) == 0:
        return 404
    else:
        return 200