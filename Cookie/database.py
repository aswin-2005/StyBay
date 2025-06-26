from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime
import uuid
import time
from Cookie.harvester import create_cookies  

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)

def add_cookie(cookies, site):
    least_expiry = min([cookie["expires"] for cookie in cookies if "expires" in cookie], default=None)

    session = {
        'session_id': f"{site}_{uuid.uuid4()}",
        'site': f'{site}.com',
        'cookies': cookies,
        'session_expiry': least_expiry,  # MUST be Unix timestamp (int)
        'created_at': datetime.utcnow().isoformat(),
        'last_used_at': None,
        'usage_count': 0,
        'health': 'healthy',
        'in_use': False
    }

    return supabase.table("CookieJar").insert(session).execute()


def remove_cookie(session_id):
    return supabase.table("CookieJar").delete().eq("session_id", session_id).execute()


def acquire_cookie(site):
    now = int(time.time())  # current Unix timestamp

    response = (
        supabase.table("CookieJar")
        .select("*")
        .eq("site", site)
        .eq("health", "healthy")
        .eq("in_use", False)
        .order("usage_count", desc=False)
        .order("last_used_at", desc=False)
        .order("session_expiry", desc=False)
        .limit(1)
        .execute()    
    )

    if response.data:
        cookie = response.data[0]
        session_id = cookie["session_id"]
        current_usage = cookie.get("usage_count", 0)

        # Atomically mark as in_use
        update_response = (
            supabase.table("CookieJar")
            .update({
                "in_use": True,
                "last_used_at": datetime.utcnow().isoformat(),
                "usage_count": current_usage + 1
            })
            .eq("session_id", session_id)
            .eq("in_use", False)
            .execute()
        )

        if update_response.data:
            return {
                **cookie,
                "in_use": True,
                "last_used_at": datetime.utcnow().isoformat(),
                "usage_count": current_usage + 1
            }

    return None


def release_cookie(session_id, valid):
    response = supabase.table("CookieJar").update({
        "in_use": False,
        "health": valid
    }).eq("session_id", session_id).execute()

    # Check if any rows were updated
    if not response.data or len(response.data) == 0:
        return None

    return response

def refresh_cookies():
    now = int(time.time())  # current Unix timestamp

    response = (
        supabase.table("CookieJar")
        .select("session_id, site")
        .or_(
            f"health.eq.unhealthy,session_expiry.lte.{now}"
        )
        .execute()
    )

    if not response.data:
        print("[✓] No cookies to refresh.")
        return

    sessions_to_refresh = response.data
    refreshed_count = 0

    for session in sessions_to_refresh:
        site = session["site"].replace(".com", "")
        session_id = session["session_id"]

        remove_cookie(session_id)

        new_session = create_cookies(site)
        if new_session:
            add_cookie(new_session["cookies"], site)
            refreshed_count += 1

    print(f"[✓] Refreshed {refreshed_count} cookies.")
