from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import annualized_return, annualized_volatility, drawdown, max_drawdown, sharpe_ratio


def run_backtest(data: pd.DataFrame, periods_per_year: int = 252) -> pd.DataFrame:
    required = {"date", "close", "position"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns for backtest: {sorted(missing)}")

    out = data.copy().sort_values("date").reset_index(drop=True)
    out["benchmark_return"] = out["close"].pct_change().fillna(0.0)
    out["strategy_return"] = out["position"].fillna(0.0) * out["benchmark_return"]
    out["strategy_nav"] = (1.0 + out["strategy_return"]).cumprod()
    out["benchmark_nav"] = (1.0 + out["benchmark_return"]).cumprod()
    out["strategy_drawdown"] = drawdown(out["strategy_nav"])
    out["benchmark_drawdown"] = drawdown(out["benchmark_nav"])
    out["turnover"] = out["position"].fillna(0.0).diff().abs().fillna(0.0)
    return out


def performance_summary(backtest: pd.DataFrame, periods_per_year: int = 252) -> pd.DataFrame:
    rows = []
    for label, ret_col, nav_col in [
        ("QRS Strategy", "strategy_return", "strategy_nav"),
        ("Long-only Benchmark", "benchmark_return", "benchmark_nav"),
    ]:
        returns = backtest[ret_col].astype(float)
        nav = backtest[nav_col].astype(float)
        mdd = max_drawdown(nav)
        ann_ret = annualized_return(returns, periods_per_year)
        calmar = ann_ret / abs(mdd) if np.isfinite(ann_ret) and np.isfinite(mdd) and mdd != 0 else np.nan
        rows.append(
            {
                "portfolio": label,
                "cumulative_return": float(nav.iloc[-1] - 1.0) if len(nav) else np.nan,
                "annualized_return": ann_ret,
                "annualized_volatility": annualized_volatility(returns, periods_per_year),
                "sharpe_ratio": sharpe_ratio(returns, periods_per_year),
                "max_drawdown": mdd,
                "calmar_ratio": float(calmar) if np.isfinite(calmar) else np.nan,
                "win_rate": float((returns > 0).sum() / max((returns != 0).sum(), 1)),
                "turnover": float(backtest["turnover"].sum()) if label == "QRS Strategy" else 0.0,
            }
        )
    return pd.DataFrame(rows)
