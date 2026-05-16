
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from live_data.market_clock import MarketClock

def main():
    clock = MarketClock()
    status = clock.session_status()
    print("System Health Check")
    print("=" * 30)
    for k, v in status.items():
        print(f"{k}: {v}")
    if status["is_trading"]:
        print("Status: OK")
        sys.exit(0)
    else:
        print("Status: MARKET CLOSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
