"""
Central strategy registry for listing, validating, and retrieving strategies.
"""
from typing import Dict, Type, List, Any
from strategies.base import BaseStrategy, StrategyConfig

# Import all strategy modules directly
import strategies.trend as trend
import strategies.momentum as momentum
import strategies.mean_reversion as mean_reversion
import strategies.pairs as pairs
import strategies.fx_carry as fx_carry
import strategies.volatility as volatility
import strategies.factors as factors
import strategies.regime as regime
import strategies.ensemble as ensemble


class StrategyRegistry:
    _registry: Dict[str, Type[BaseStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        if not issubclass(strategy_class, BaseStrategy):
            raise TypeError(f"{strategy_class.__name__} must inherit from BaseStrategy")
        cls._registry[name] = strategy_class

    @classmethod
    def get(cls, name: str) -> Type[BaseStrategy]:
        if name not in cls._registry:
            raise KeyError(f"Strategy '{name}' not found. Available: {list(cls._registry.keys())}")
        return cls._registry[name]

    @classmethod
    def list_strategies(cls) -> List[str]:
        return sorted(cls._registry.keys())

    @classmethod
    def validate_all(cls) -> Dict[str, Any]:
        results = {}
        for name, strat_class in cls._registry.items():
            try:
                cfg = StrategyConfig(name=name, symbols=["DEMO"])
                instance = strat_class(cfg)
                results[name] = {"status": "ok", "class": strat_class.__name__}
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        return results

    @classmethod
    def is_registered(cls, name: str) -> bool:
        return name in cls._registry


def _register_defaults() -> None:
    StrategyRegistry.register("time_series_momentum", trend.TimeSeriesMomentum)
    StrategyRegistry.register("ma_crossover", trend.MACrossover)
    StrategyRegistry.register("channel_breakout", trend.ChannelBreakout)
    StrategyRegistry.register("cross_sectional_momentum", momentum.CrossSectionalMomentum)
    StrategyRegistry.register("relative_strength", momentum.RelativeStrength)
    StrategyRegistry.register("zscore_mean_reversion", mean_reversion.ZScoreMeanReversion)
    StrategyRegistry.register("rsi_mean_reversion", mean_reversion.RSImeanReversion)
    StrategyRegistry.register("pairs_trading", pairs.PairsTradingSignal)
    StrategyRegistry.register("fx_carry", fx_carry.FXCarrySignal)
    StrategyRegistry.register("atr_breakout", volatility.ATRBreakout)
    StrategyRegistry.register("volatility_breakout", volatility.VolatilityBreakout)
    StrategyRegistry.register("multi_factor_ranking", factors.MultiFactorRanking)
    StrategyRegistry.register("volatility_regime", regime.VolatilityRegime)
    StrategyRegistry.register("trend_regime", regime.TrendRegime)
    StrategyRegistry.register("risk_on_off", regime.RiskOnOffFilter)
    StrategyRegistry.register("ensemble_selector", ensemble.EnsembleSelector)


_register_defaults()
