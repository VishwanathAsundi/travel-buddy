from config import Config
import logging
import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    """Thread-safe rate limiter for Google Places API"""
    
    def __init__(self, max_requests_per_second=10, max_requests_per_day=100000):
        self.max_requests_per_second = max_requests_per_second
        self.max_requests_per_day = max_requests_per_day
        self.requests_per_second = deque()
        self.requests_per_day = deque()
        self.lock = Lock()
        self.daily_reset_time = time.time() + 86400  # 24 hours from now
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        with self.lock:
            current_time = time.time()
            
            # Reset daily counter if needed
            if current_time >= self.daily_reset_time:
                self.requests_per_day.clear()
                self.daily_reset_time = current_time + 86400
            
            # Clean old requests (older than 1 second)
            while self.requests_per_second and current_time - self.requests_per_second[0] >= 1.0:
                self.requests_per_second.popleft()
            
            # Clean old daily requests (older than 24 hours)
            while self.requests_per_day and current_time - self.requests_per_day[0] >= 86400:
                self.requests_per_day.popleft()
            
            # Check daily limit
            if len(self.requests_per_day) >= self.max_requests_per_day:
                wait_time = 86400 - (current_time - self.requests_per_day[0])
                logging.info(f"Daily rate limit reached. Waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                self.requests_per_day.clear()
                self.daily_reset_time = time.time() + 86400
            
            # Check per-second limit
            if len(self.requests_per_second) >= self.max_requests_per_second:
                wait_time = 1.0 - (current_time - self.requests_per_second[0])
                if wait_time > 0:
                    logging.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                    time.sleep(wait_time)
                    current_time = time.time()
            
            # Record this request
            self.requests_per_second.append(current_time)
            self.requests_per_day.append(current_time)