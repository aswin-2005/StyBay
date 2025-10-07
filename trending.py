from datetime import datetime, timedelta
import heapq

class TrendingManager:
    def __init__(self, max_size=500, max_age_days=7, decay_factor=0.9):
        self.scores = {}  # pid -> {"score": int, "last_seen": datetime}
        self.max_size = max_size
        self.max_age = timedelta(days=max_age_days)
        self.decay_factor = decay_factor

    def bump(self, pid, weight=1):
        """Increase score when a product is seen/clicked/purchased."""
        now = datetime.now()
        if pid not in self.scores:
            self.scores[pid] = {"score": weight, "last_seen": now}
        else:
            self.scores[pid]["score"] += weight
            self.scores[pid]["last_seen"] = now

    def decay_scores(self):
        """Gradually reduce score weights over time."""
        for pid, data in list(self.scores.items()):
            data["score"] = int(data["score"] * self.decay_factor)
            if data["score"] <= 0:
                del self.scores[pid]

    def evict(self):
        """Remove outdated or excess items."""
        now = datetime.now()
        # Time-based eviction
        for pid, data in list(self.scores.items()):
            if now - data["last_seen"] > self.max_age:
                del self.scores[pid]
        # Size-based eviction
        if len(self.scores) > self.max_size:
            lowest = heapq.nsmallest(len(self.scores) - self.max_size,
                                     self.scores.items(),
                                     key=lambda x: x[1]["score"])
            for pid, _ in lowest:
                del self.scores[pid]

    def get_top(self, n=10):
        """Return top-N trending product IDs."""
        top = heapq.nlargest(n, self.scores.items(), key=lambda x: x[1]["score"])
        return [pid for pid, _ in top]
