# cookie_manager.py

import os
import json
import uuid
from datetime import datetime, timedelta
from Scraper.Cookies.harvester import create_cookies

COOKIE_DIR = "Scraper/Cookies/cookies_disk"
MAX_FAILED_ATTEMPTS = 3
COOKIE_LIFETIME_HOURS = 24

os.makedirs(COOKIE_DIR, exist_ok=True)


def _get_cookie_file(site):
    """Get the file path for a site's cookies."""
    return os.path.join(COOKIE_DIR, f"{site}.json")


def _load_cookies(site):
    """Load cookies from disk for a specific site."""
    try:
        with open(_get_cookie_file(site), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_cookies(site, cookies):
    """Save cookies to disk for a specific site."""
    with open(_get_cookie_file(site), "w") as f:
        json.dump(cookies, f, indent=2)


def _create_cookie_session(site):
    """Create a new cookie session for a site."""
    cookies = create_cookies(site)
    if not cookies:
        return None

    # Calculate earliest expiry from all cookies
    expiry_timestamps = [c.get("expires") for c in cookies if c.get("expires") and isinstance(c.get("expires"), (int, float)) and c.get("expires") > 0]
    earliest_expiry = min(expiry_timestamps) if expiry_timestamps else None

    return {
        "id": str(uuid.uuid4()),
        "site": site,
        "cookies": cookies,
        "created_at": datetime.utcnow().isoformat(),
        "cookie_expiry": earliest_expiry,
        "is_healthy": True,
        "usage_count": 0,
        "last_used": None,
        "failed_attempts": 0,
    }


def _is_cookie_healthy(cookie_session):
    """Check if a cookie session is healthy and valid."""
    # Check health flag
    if not cookie_session.get("is_healthy", True):
        return False
    
    # Check failed attempts
    if cookie_session.get("failed_attempts", 0) >= MAX_FAILED_ATTEMPTS:
        return False
    
    # Check cookie expiry
    expiry_val = cookie_session.get("cookie_expiry")
    if expiry_val is not None:
        try:
            # Only check expiry if it's a valid positive timestamp
            if isinstance(expiry_val, (int, float)) and expiry_val > 0:
                expiry = datetime.fromtimestamp(expiry_val)
                if datetime.utcnow() > expiry:
                    return False
            # If expiry is 0 or negative, treat as session cookie (not expired)
        except Exception:
            # If expiry is invalid, treat as session cookie (not expired)
            pass
    
    # Check session age
    created_at = datetime.fromisoformat(cookie_session["created_at"])
    if datetime.utcnow() - created_at > timedelta(hours=COOKIE_LIFETIME_HOURS):
        return False
    
    return True


def _get_best_cookie(cookie_sessions):
    """Get the best healthy cookie session based on usage and recency."""
    healthy_sessions = [s for s in cookie_sessions if _is_cookie_healthy(s)]
    
    if not healthy_sessions:
        return None
    
    # Sort by usage count (ascending) and last used time (oldest first)
    healthy_sessions.sort(key=lambda s: (
        s.get("usage_count", 0),
        s.get("last_used") or "0"
    ))
    
    return healthy_sessions[0]


def get_cookie(site):
    """Get the best available cookie for a site."""
    cookie_sessions = _load_cookies(site)
    best_cookie = _get_best_cookie(cookie_sessions)
    
    if best_cookie:
        # Update usage stats
        best_cookie["usage_count"] += 1
        best_cookie["last_used"] = datetime.utcnow().isoformat()
        _save_cookies(site, cookie_sessions)
        
        return {
            "cookies": best_cookie["cookies"],
            "session_id": best_cookie["id"],
            "is_healthy": best_cookie["is_healthy"]
        }
    
    # Create new cookie session if no healthy ones exist
    new_session = _create_cookie_session(site)
    if new_session:
        new_session["usage_count"] = 1
        new_session["last_used"] = datetime.utcnow().isoformat()
        cookie_sessions.append(new_session)
        _save_cookies(site, cookie_sessions)
        
        return {
            "cookies": new_session["cookies"],
            "session_id": new_session["id"],
            "is_healthy": True
        }
    
    return None


def report_cookie_status(session_id, is_working=True):
    """Report whether a cookie is working or failed."""
    for file in os.listdir(COOKIE_DIR):
        if not file.endswith(".json"):
            continue
        
        site = file[:-5]  # Remove .json extension
        cookie_sessions = _load_cookies(site)
        
        for session in cookie_sessions:
            if session["id"] == session_id:
                if is_working:
                    # Reset failed attempts if working
                    session["failed_attempts"] = 0
                    session["is_healthy"] = True
                else:
                    # Increment failed attempts and mark unhealthy if threshold reached
                    session["failed_attempts"] = session.get("failed_attempts", 0) + 1
                    if session["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
                        session["is_healthy"] = False
                
                session["last_used"] = datetime.utcnow().isoformat()
                _save_cookies(site, cookie_sessions)
                return True
    
    return False


def cleanup_unhealthy_cookies():
    """Remove all unhealthy and expired cookie sessions."""
    cleaned_count = 0
    
    for file in os.listdir(COOKIE_DIR):
        if not file.endswith(".json"):
            continue
        
        site = file[:-5]
        cookie_sessions = _load_cookies(site)
        initial_count = len(cookie_sessions)
        
        # Keep only healthy cookie sessions
        healthy_sessions = [s for s in cookie_sessions if _is_cookie_healthy(s)]
        
        if healthy_sessions:
            _save_cookies(site, healthy_sessions)
            cleaned_count += initial_count - len(healthy_sessions)
        else:
            # Remove file if no healthy sessions remain
            os.remove(_get_cookie_file(site))
            cleaned_count += initial_count
    
    return cleaned_count


def get_cookie_stats(site):
    """Get statistics for cookies of a specific site."""
    cookie_sessions = _load_cookies(site)
    healthy_sessions = [s for s in cookie_sessions if _is_cookie_healthy(s)]
    
    return {
        "site": site,
        "total_cookies": len(cookie_sessions),
        "healthy_cookies": len(healthy_sessions),
        "unhealthy_cookies": len(cookie_sessions) - len(healthy_sessions),
        "sessions": [
            {
                "id": s["id"],
                "is_healthy": s.get("is_healthy", True),
                "usage_count": s.get("usage_count", 0),
                "failed_attempts": s.get("failed_attempts", 0),
                "created_at": s["created_at"],
                "last_used": s.get("last_used"),
                "valid": _is_cookie_healthy(s)
            }
            for s in cookie_sessions
        ]
    }


def get_all_sites_stats():
    """Get statistics for all sites with cookies."""
    stats = {}
    
    for file in os.listdir(COOKIE_DIR):
        if file.endswith(".json"):
            site = file[:-5]
            stats[site] = get_cookie_stats(site)
    
    return stats