
import os
import pytest
from config.settings import Settings

def test_settings_defaults():
    assert Settings.MODE == "paper" or Settings.MODE is not None
    assert Settings.SQLITE_PATH is not None

def test_settings_types():
    assert isinstance(Settings.PAPER_INITIAL_BALANCE, float)
    assert isinstance(Settings.PAPER_COMMISSION_PER_LOT, float)
