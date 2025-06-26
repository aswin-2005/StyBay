import requests

BASE_URL = "http://localhost:5050/api"

def log_result(endpoint, method, status_code, ok):
    print(f"[{method}] {endpoint} → {'PASS' if ok else 'FAIL'} ({status_code})")


def test_ping():
    resp = requests.get(f"{BASE_URL}/ping")
    log_result("/ping", "GET", resp.status_code, resp.ok)


def test_acquire_cookie(site):
    resp = requests.post(f"{BASE_URL}/cookies", json={"site": site})
    log_result("/cookies", "POST", resp.status_code, resp.ok)
    return resp.json().get("session", {}).get("session_id") if resp.ok else None


def test_release_cookie(session_id, valid="true"):
    resp = requests.delete(f"{BASE_URL}/cookies/{session_id}", params={"valid": valid})
    log_result(f"/cookies/{session_id}?valid={valid}", "DELETE", resp.status_code, resp.ok)


def test_refresh():
    resp = requests.post(f"{BASE_URL}/cookies/refresh")
    log_result("/cookies/refresh", "POST", resp.status_code, resp.ok)


def run_tests():
    print("== Running Cookie API Tests ==\n")

    test_ping()

    # Simulate acquiring a cookie
    session_id = test_acquire_cookie("myntra")

    if session_id:
        # Release it with valid=true
        test_release_cookie(session_id, valid="true")

        # Try to release a non-existent session
        test_release_cookie("nonexistent-session-id", valid="false")

    # Test refresh endpoint
    test_refresh()

    print("\n== All tests completed ==")


if __name__ == "__main__":
    run_tests()
