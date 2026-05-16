
import uuid
import time
import threading
from typing import Callable, Any, Optional, Dict
from datetime import datetime, timezone
from scheduler.job_store import JobStore
from scheduler.retry_policy import RetryPolicy
from scheduler.heartbeat import Heartbeat

class TaskScheduler:
    def __init__(self, job_store: Optional[JobStore] = None,
                 retry_policy: Optional[RetryPolicy] = None):
        self.job_store = job_store or JobStore()
        self.retry_policy = retry_policy or RetryPolicy()
        self.heartbeat = Heartbeat(component="scheduler")
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._last_success_at: Optional[str] = None
        self._last_failure_at: Optional[str] = None
        self._failure_count = 0

    def add_interval_task(self, task_id: str, fn: Callable, interval_seconds: float,
                          args: Optional[tuple] = None, kwargs: Optional[dict] = None):
        self._tasks[task_id] = {
            "fn": fn,
            "interval": interval_seconds,
            "args": args or (),
            "kwargs": kwargs or {},
            "last_run": None
        }

    def start(self):
        self._running = True
        self.heartbeat.beat("running")
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self.heartbeat.beat("stopped")
        if self._thread:
            self._thread.join(timeout=5.0)

    def _loop(self):
        while self._running:
            now = time.time()
            for task_id, task in self._tasks.items():
                if task["last_run"] is None or (now - task["last_run"]) >= task["interval"]:
                    self._run_task(task_id, task)
                    task["last_run"] = now
            self.heartbeat.beat("ok")
            time.sleep(1.0)

    def _run_task(self, task_id: str, task: Dict[str, Any]):
        job_id = str(uuid.uuid4())
        self.job_store.add(job_id, task_id, {})
        self.job_store.start(job_id)
        try:
            result = self.retry_policy.execute(task["fn"], *task["args"], **task["kwargs"])
            self.job_store.complete(job_id, result)
            self._last_success_at = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            self.job_store.fail(job_id, str(e))
            self._last_failure_at = datetime.now(timezone.utc).isoformat()
            self._failure_count += 1

    def tick(self):
        """Manual tick for testing without threads."""
        for task_id, task in self._tasks.items():
            self._run_task(task_id, task)
        self.heartbeat.beat("ok")

    def is_running(self) -> bool:
        return self._running

    def summary(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "tasks": list(self._tasks.keys()),
            "last_success_at": self._last_success_at,
            "last_failure_at": self._last_failure_at,
            "failure_count": self._failure_count,
            "heartbeat": self.heartbeat.to_dict()
        }
