from __future__ import annotations

import itertools
from typing import Any

import pandas as pd

from .backtest import intraday_performance_summary, run_intraday_backtest
from .signal_generator import generate_qrs_intraday_signals


DEFAULT_S_VALUES = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
DEFAULT_TREND_METHODS = ["ma_compare", "ma_cross", "price_compare"]
DEFAULT_MA_LEN_DAYS = [3, 5, 10, 20]
DEFAULT_COMPARE_LAG_DAYS = [1, 2, 3]
DEFAULT_MA_SHORT = [3, 5, 10]
DEFAULT_MA_LONG = [10, 20, 30]


def iter_param_grid(
    s_values: list[float] | None = None,
    trend_methods: list[str] | None = None,
    ma_len_days_values: list[int] | None = None,
    compare_lag_days_values: list[int] | None = None,
    ma_short_values: list[int] | None = None,
    ma_long_values: list[int] | None = None,
):
    s_values = DEFAULT_S_VALUES if s_values is None else s_values
    trend_methods = DEFAULT_TREND_METHODS if trend_methods is None else trend_methods
    ma_len_days_values = DEFAULT_MA_LEN_DAYS if ma_len_days_values is None else ma_len_days_values
    compare_lag_days_values = DEFAULT_COMPARE_LAG_DAYS if compare_lag_days_values is None else compare_lag_days_values
    ma_short_values = DEFAULT_MA_SHORT if ma_short_values is None else ma_short_values
    ma_long_values = DEFAULT_MA_LONG if ma_long_values is None else ma_long_values

    if "ma_compare" in trend_methods:
        for S, ma_len_days, compare_lag_days in itertools.product(s_values, ma_len_days_values, compare_lag_days_values):
            yield {
                "S": float(S),
                "trend_method": "ma_compare",
                "ma_len_days": int(ma_len_days),
                "compare_lag_days": int(compare_lag_days),
                "ma_short": None,
                "ma_long": None,
            }
    if "ma_cross" in trend_methods:
        for S, ma_short, ma_long in itertools.product(s_values, ma_short_values, ma_long_values):
            if int(ma_short) >= int(ma_long):
                continue
            yield {
                "S": float(S),
                "trend_method": "ma_cross",
                "ma_len_days": None,
                "compare_lag_days": None,
                "ma_short": int(ma_short),
                "ma_long": int(ma_long),
            }
    if "price_compare" in trend_methods:
        for S, ma_len_days in itertools.product(s_values, ma_len_days_values):
            yield {
                "S": float(S),
                "trend_method": "price_compare",
                "ma_len_days": int(ma_len_days),
                "compare_lag_days": None,
                "ma_short": None,
                "ma_long": None,
            }


def run_grid_search(
    qrs_df: pd.DataFrame,
    allow_short: bool = True,
    periods_per_year: int = 252 * 54,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for params in iter_param_grid():
        signal_df = generate_qrs_intraday_signals(
            qrs_df,
            S=float(params["S"]),
            trend_method=str(params["trend_method"]),
            ma_len_days=int(params["ma_len_days"] or 5),
            compare_lag_days=int(params["compare_lag_days"] or 2),
            ma_short=int(params["ma_short"] or 5),
            ma_long=int(params["ma_long"] or 20),
            allow_short=allow_short,
        )
        bt = run_intraday_backtest(signal_df, periods_per_year=periods_per_year)
        summary = intraday_performance_summary(bt, periods_per_year=periods_per_year)
        strat = summary.loc[summary["portfolio"] == "QRS Strategy"].iloc[0].to_dict()
        rows.append({**params, **{k: v for k, v in strat.items() if k != "portfolio"}})

    results = pd.DataFrame(rows).sort_values("sharpe_ratio", ascending=False).reset_index(drop=True)
    best = results.iloc[0].to_dict()
    return results, best

