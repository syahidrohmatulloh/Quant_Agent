
import heapq
from typing import List, Any

class EventQueue:
    def __init__(self):
        self._queue: List[tuple] = []
        self._counter = 0

    def put(self, timestamp, event):
        heapq.heappush(self._queue, (timestamp, self._counter, event))
        self._counter += 1

    def get(self):
        if not self._queue:
            return None
        ts, _, event = heapq.heappop(self._queue)
        return ts, event

    def empty(self) -> bool:
        return len(self._queue) == 0

    def __len__(self):
        return len(self._queue)
