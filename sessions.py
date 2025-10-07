from datetime import datetime, timedelta
import uuid
import tagger  # assuming extract_tags_from_text exists here

class SessionManager:
    def __init__(self, request_ttl_seconds=1800, max_seen_products=100):
        """
        request_ttl_seconds: inactivity period after which a session is purged
        max_seen_products: maximum number of seen products to track per session
        """
        self.sessions = {}
        self.request_ttl = timedelta(seconds=request_ttl_seconds)
        self.max_seen_products = max_seen_products

    def create_session(self, session_type, query="", tags=None):
        """Create and register a new session."""
        rid = uuid.uuid4()

        # --- Generate tags from query if not provided ---
        if tags is None:
            tags = tagger.extract_tags_from_text(query)  # convert query into meaningful tags

        self.sessions[rid] = {
            "session_type": session_type,
            "query": query,
            "tags": tags,
            "last_request_at": datetime.now(),
            "seen_products": []
        }
        return str(rid)

    def get_session(self, rid):
        """Retrieve session dict by ID."""
        return self.sessions.get(rid)

    def add_to_seen(self, rid, pid):
        """Track that a product has been served to a session."""
        session = self.get_session(rid)
        if not session:
            return
        seen = session["seen_products"]
        if pid not in seen:
            seen.append(pid)
            if len(seen) > self.max_seen_products:
                del seen[0]

    def update_last_request(self, rid):
        """Refresh session timestamp."""
        session = self.get_session(rid)
        if session:
            session["last_request_at"] = datetime.now()

    def cleanup(self):
        """Purge stale sessions beyond TTL."""
        now = datetime.now()
        to_delete = [
            rid for rid, s in self.sessions.items()
            if now - s["last_request_at"] > self.request_ttl
        ]
        for rid in to_delete:
            del self.sessions[rid]

    def get_session_snapshot(self, rid):
        """Return a copy of session info suitable for client consumption."""
        session = self.get_session(rid)
        if not session:
            return None
        return {
            "rid": str(rid),
            "session_type": session["session_type"],
            "query": session.get("query", ""),
            "tags": session.get("tags", []),
            "last_request_at": session.get("last_request_at").isoformat(),
            "seen_products": list(session.get("seen_products", []))
        }