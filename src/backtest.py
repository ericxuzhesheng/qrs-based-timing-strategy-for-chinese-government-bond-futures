from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import annualized_return, annualized_volatility, drawdown, max_drawdown, sharpe_ratio


def run_intraday_backtest(
    df: pd.DataFrame,
    close_col: str = "close",
    position_col: str = "position",
    periods_per_year: int = 252 * 54,
) -> pd.DataFrame:
    required = {"date", close_col, position_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for intraday backtest: {sorted(missing)}")

    out = df.copy().sort_values("date").reset_index(drop=True)
    out["ret_benchmark"] = out[close_col].astype(float).pct_change().fillna(0.0)
    out["ret_strategy"] = out[position_col].fillna(0.0).astype(float) * out["ret_benchmark"]
    out["ret_excess"] = out["ret_strategy"] - out["ret_benchmark"]
    out["nav_benchmark"] = (1.0 + out["ret_benchmark"]).cumprod()
    out["nav_strategy"] = (1.0 + out["ret_strategy"]).cumprod()
    out["nav_excess"] = (1.0 + out["ret_excess"]).cumprod()
    out["drawdown_strategy"] = drawdown(out["nav_strategy"])
    out["drawdown_benchmark"] = drawdown(out["nav_benchmark"])
    out["turnover"] = out[position_col].fillna(0.0).astype(float).diff().abs().fillna(0.0)
    return out


def intraday_performance_summary(backtest: pd.DataFrame, periods_per_year: int = 252 * 54) -> pd.DataFrame:
    rows = []
    for label, ret_col, nav_col, dd_col in [
        ("QRS Strategy", "ret_strategy", "nav_strategy", "drawdown_strategy"),
        ("Long-only Benchmark", "ret_benchmark", "nav_benchmark", "drawdown_benchmark"),
    ]:
        returns = backtest[ret_col].dropna().astype(float)
        nav = backtest[nav_col].astype(float)
        annual_return = float(returns.mean() * periods_per_year) if len(returns) else np.nan
        annual_vol = float(returns.std(ddof=1) * np.sqrt(periods_per_year)) if len(returns) > 1 else np.nan
        sharpe = annual_return / annual_vol if np.isfinite(annual_return) and np.isfinite(annual_vol) and annual_vol != 0 else np.nan
        mdd = float(backtest[dd_col].min()) if len(backtest) else np.nan
        calmar = annual_return / abs(mdd) if np.isfinite(annual_return) and np.isfinite(mdd) and mdd != 0 else np.nan
        rows.append(
            {
                "portfolio": label,
                "cumulative_return": float(nav.iloc[-1] - 1.0) if len(nav) else np.nan,
                "annualized_return": annual_return,
                "annualized_volatility": annual_vol,
                "sharpe_ratio": float(sharpe) if np.isfinite(sharpe) else np.nan,
                "max_drawdown": mdd,
                "calmar_ratio": float(calmar) if np.isfinite(calmar) else np.nan,
                "win_rate": float((returns > 0).sum() / max((returns != 0).sum(), 1)),
                "turnover": float(backtest["turnover"].sum()) if label == "QRS Strategy" else 0.0,
            }
        )
    return pd.DataFrame(rows)


def intraday_debug_stats(backtest: pd.DataFrame) -> pd.DataFrame:
    position = backtest["position"].fillna(0.0).astype(float)
    row = {
        "sample_start": pd.to_datetime(backtest["date"].iloc[0]).strftime("%Y-%m-%d %H:%M:%S") if len(backtest) else "",
        "sample_end": pd.to_datetime(backtest["date"].iloc[-1]).strftime("%Y-%m-%d %H:%M:%S") if len(backtest) else "",
        "bar_count": int(len(backtest)),
        "average_position": float(position.mean()) if len(position) else np.nan,
        "long_ratio": float((position > 0).mean()) if len(position) else np.nan,
        "short_ratio": float((position < 0).mean()) if len(position) else np.nan,
        "cash_ratio": float((position == 0).mean()) if len(position) else np.nan,
        "turnover_count": float(backtest["turnover"].sum()) if "turnover" in backtest else np.nan,
        "benchmark_annual_return": float(backtest["ret_benchmark"].mean() * 252 * 54) if "ret_benchmark" in backtest else np.nan,
        "strategy_annual_return": float(backtest["ret_strategy"].mean() * 252 * 54) if "ret_strategy" in backtest else np.nan,
        "strategy_sharpe": float(intraday_performance_summary(backtest).loc[0, "sharpe_ratio"]) if len(backtest) else np.nan,
        "max_drawdown": float(backtest["drawdown_strategy"].min()) if "drawdown_strategy" in backtest else np.nan,
    }
    return pd.DataFrame([row])


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
