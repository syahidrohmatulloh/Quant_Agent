import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from broker_integration.mt5.mt5_errors import (
    MT5Error,
    MT5ModuleNotFoundError,
    MT5TerminalUnavailableError,
    MT5InitializationError,
    MT5SymbolError,
    MT5DataError,
    MT5TimeframeError,
)


def test_error_hierarchy():
    assert issubclass(MT5ModuleNotFoundError, MT5Error)
    assert issubclass(MT5TerminalUnavailableError, MT5Error)
    assert issubclass(MT5InitializationError, MT5Error)
    assert issubclass(MT5SymbolError, MT5Error)
    assert issubclass(MT5DataError, MT5Error)
    assert issubclass(MT5TimeframeError, MT5Error)


def test_error_messages():
    e = MT5ModuleNotFoundError("package missing")
    assert str(e) == "package missing"
