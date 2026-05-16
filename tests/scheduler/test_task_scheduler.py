
import pytest
from scheduler.task_scheduler import TaskScheduler
from scheduler.job_store import JobStore
from scheduler.retry_policy import RetryPolicy

def test_scheduler_add_task():
    scheduler = TaskScheduler()
    calls = []
    scheduler.add_interval_task("test", lambda: calls.append(1), interval_seconds=1.0)
    assert "test" in scheduler._tasks

def test_scheduler_tick_runs_task():
    scheduler = TaskScheduler()
    calls = []
    scheduler.add_interval_task("test", lambda: calls.append(1), interval_seconds=1.0)
    scheduler.tick()
    assert len(calls) == 1

def test_scheduler_records_success():
    scheduler = TaskScheduler()
    scheduler.add_interval_task("test", lambda: 42, interval_seconds=1.0)
    scheduler.tick()
    assert scheduler._last_success_at is not None
    assert scheduler._failure_count == 0

def test_scheduler_records_failure():
    scheduler = TaskScheduler()
    scheduler.add_interval_task("test", lambda: (_ for _ in ()).throw(RuntimeError("fail")), interval_seconds=1.0)
    scheduler.tick()
    assert scheduler._last_failure_at is not None
    assert scheduler._failure_count == 1

def test_scheduler_summary():
    scheduler = TaskScheduler()
    scheduler.add_interval_task("a", lambda: None, interval_seconds=1.0)
    summary = scheduler.summary()
    assert summary["running"] is False
    assert "a" in summary["tasks"]
    assert "heartbeat" in summary
