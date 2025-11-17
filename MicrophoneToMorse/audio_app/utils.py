import collections
import time


class WarningThrottler:
    def __init__(self, name: str, interval: float = 0.5):
        self.name = name
        self.interval = interval
        self.last_warning_times = collections.defaultdict(lambda: 0)

    def warn(self, key: str, message: str) -> bool:
        current_time = time.time()
        if (current_time - self.last_warning_times[key]) > self.interval:
            print(f"[{self.name}] Warning: {message}")
            self.last_warning_times[key] = current_time
            return True
        return False
