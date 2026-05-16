
from typing import Dict, Any, Optional, List
from datetime import datetime
from backtesting.event_queue import EventQueue
from backtesting.data_feed import HistoricalDataFeed
from backtesting.execution_simulator import ExecutionSimulator
from backtesting.portfolio_simulator import PortfolioSimulator
from backtesting.performance import PerformanceAnalyzer
from backtesting.report import ReportGenerator
from backtesting.event import MarketEvent, SignalEvent, OrderEvent, FillEvent, PositionClosedEvent
from research.strategy_base import StrategyBase

class BacktestEngine:
    def __init__(self, data_feed: HistoricalDataFeed, strategy: StrategyBase,
                 initial_balance: float = 100000.0,
                 commission_per_lot: float = 7.0,
                 slippage_pips: float = 0.5):
        self.data_feed = data_feed
        self.strategy = strategy
        self.queue = EventQueue()
        self.execution = ExecutionSimulator(commission_per_lot, slippage_pips)
        self.portfolio = PortfolioSimulator(initial_balance)
        self.equity_curve: List[float] = [initial_balance]
        self.timestamps: List[str] = []
        self._open_positions: Dict[str, Any] = {}
        self._order_counter = 0

    def _next_order_id(self):
        self._order_counter += 1
        return f"BT-ORDER-{self._order_counter:04d}"

    def run(self) -> Dict[str, Any]:
        for market_event in self.data_feed:
            self.timestamps.append(market_event.timestamp.isoformat())
            # Strategy signal
            signal = self.strategy.on_market_event(market_event)
            if signal:
                self._process_signal(signal, market_event)
            # Check SL/TP for open positions (same-bar policy)
            self._check_sl_tp(market_event)
            # Update equity
            current_prices = {market_event.symbol: market_event.ask if market_event.symbol not in [p["symbol"] for p in self._open_positions.values()] else market_event.bid}
            # Actually update all open position symbols
            price_map = {}
            for pos in self._open_positions.values():
                if pos["symbol"] == market_event.symbol:
                    price_map[pos["symbol"]] = market_event.ask if pos["direction"] == "buy" else market_event.bid
            self.portfolio.update_equity(price_map)
            self.equity_curve.append(self.portfolio.equity)
        # Close any remaining positions at last price
        last_price = 1.0
        if self.timestamps:
            # approximate last known price from equity update
            pass
        for pos in list(self._open_positions.values()):
            self._close_position(pos, pos.get("last_price", pos["entry_price"]), datetime.now())
        summary = PerformanceAnalyzer(self.portfolio.trades, self.equity_curve, self.timestamps).summary()
        return {
            "summary": summary,
            "trades": self.portfolio.trades,
            "equity_curve": self.equity_curve,
            "timestamps": self.timestamps
        }

    def _process_signal(self, signal: SignalEvent, market: MarketEvent):
        if signal.signal in ("buy", "sell"):
            order = OrderEvent(
                timestamp=market.timestamp,
                symbol=signal.symbol,
                direction=signal.signal,
                volume=1.0,
                order_type="market"
            )
            fill = self.execution.simulate_fill(order, market)
            fill = FillEvent(
                timestamp=fill.timestamp,
                symbol=fill.symbol,
                direction=fill.direction,
                volume=fill.volume,
                fill_price=fill.fill_price,
                commission=fill.commission,
                order_id=self._next_order_id()
            )
            self.portfolio.on_fill(fill)
            pos_key = f"{fill.symbol}_{fill.direction}"
            self._open_positions[pos_key] = {
                "symbol": fill.symbol,
                "direction": fill.direction,
                "volume": fill.volume,
                "entry_price": fill.fill_price,
                "commission": fill.commission,
                "last_price": fill.fill_price,
                "sl": signal.meta.get("sl") if signal.meta else None,
                "tp": signal.meta.get("tp") if signal.meta else None,
            }
            self.strategy.on_fill_event(fill)
        elif signal.signal == "close":
            # close all for symbol
            for key, pos in list(self._open_positions.items()):
                if pos["symbol"] == signal.symbol:
                    price = market.bid if pos["direction"] == "buy" else market.ask
                    self._close_position(pos, price, market.timestamp)

    def _check_sl_tp(self, market: MarketEvent):
        for key, pos in list(self._open_positions.items()):
            if pos["symbol"] != market.symbol:
                continue
            price = market.bid if pos["direction"] == "buy" else market.ask
            pos["last_price"] = price
            sl = pos.get("sl")
            tp = pos.get("tp")
            hit = False
            if pos["direction"] == "buy":
                if sl is not None and price <= sl:
                    hit = True
                if tp is not None and price >= tp:
                    hit = True
            else:
                if sl is not None and price >= sl:
                    hit = True
                if tp is not None and price <= tp:
                    hit = True
            if hit:
                self._close_position(pos, price, market.timestamp)

    def _close_position(self, pos: Dict[str, Any], price: float, timestamp: datetime):
        key = f"{pos['symbol']}_{pos['direction']}"
        if key in self._open_positions:
            del self._open_positions[key]
        if pos["direction"] == "buy":
            pnl = (price - pos["entry_price"]) * pos["volume"] * 100000
        else:
            pnl = (pos["entry_price"] - price) * pos["volume"] * 100000
        pnl -= pos["commission"]
        event = PositionClosedEvent(
            timestamp=timestamp,
            symbol=pos["symbol"],
            direction=pos["direction"],
            volume=pos["volume"],
            entry_price=pos["entry_price"],
            exit_price=price,
            pnl=pnl,
            commission=pos["commission"]
        )
        self.portfolio.on_position_closed(event)
        self.strategy.on_position_closed(event)
