
import pytest
import pandas as pd
import numpy as np
from research_pipeline.drift_monitor import DriftMonitor

def test_no_drift():
    ref = pd.DataFrame({"feat1": np.random.normal(0, 1, 1000)})
    monitor = DriftMonitor(ref)
    cur = pd.DataFrame({"feat1": np.random.normal(0, 1, 100)})
    report = monitor.check(cur)
    assert report.alert is False
    assert report.missing_rate < 0.01

def test_feature_drift_detected():
    ref = pd.DataFrame({"feat1": np.random.normal(0, 1, 1000)})
    monitor = DriftMonitor(ref)
    cur = pd.DataFrame({"feat1": np.random.normal(5, 1, 100)})
    report = monitor.check(cur)
    assert report.alert is True
    assert report.feature_drift["feat1"] > 3.0

def test_missing_data_alert():
    ref = pd.DataFrame({"feat1": [1.0] * 100})
    monitor = DriftMonitor(ref)
    cur = pd.DataFrame({"feat1": [np.nan] * 20 + [1.0] * 80})
    report = monitor.check(cur)
    assert report.missing_rate > 0.1
    assert report.alert is True

def test_data_quality_fields():
    ref = pd.DataFrame({"feat1": [1.0] * 10, "feat2": [2.0] * 10})
    monitor = DriftMonitor(ref)
    cur = pd.DataFrame({"feat1": [1.0] * 5, "feat2": [2.0] * 5})
    report = monitor.check(cur)
    assert report.data_quality["rows"] == 5
    assert "feat1" in report.data_quality["columns"]
