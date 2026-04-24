from __future__ import annotations

import numpy as np
import pandas as pd

from .trend_filter import build_daily_trend_filter_from_intraday


def generate_qrs_intraday_signals(
    df: pd.DataFrame,
    qrs_col: str = "qrs",
    close_col: str = "close",
    S: float = 0.5,
    trend_method: str = "ma_compare",
    ma_len_days: int = 5,
    compare_lag_days: int = 2,
    ma_short: int = 5,
    ma_long: int = 20,
    allow_short: bool = True,
) -> pd.DataFrame:
    required = {"date", qrs_col, close_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for QRS intraday signals: {sorted(missing)}")

    out = df.copy().sort_values("date").reset_index(drop=True)
    close = pd.Series(out[close_col].to_numpy(dtype=float), index=pd.to_datetime(out["date"]), name=close_col)
    trend = build_daily_trend_filter_from_intraday(
        close_intraday=close,
        ma_len_days=ma_len_days,
        compare_lag_days=compare_lag_days,
        trend_method=trend_method,
        ma_short=ma_short,
        ma_long=ma_long,
    )
    trend = trend.reindex(close.index)
    qrs = out[qrs_col].astype(float)
    trend_up = trend["trend_up_intraday"].to_numpy(dtype=bool)
    trend_down = trend["trend_down_intraday"].to_numpy(dtype=bool)
    threshold = float(S)

    raw_position = np.zeros(len(out), dtype=float)
    long_signal = np.zeros(len(out), dtype=int)
    short_signal = np.zeros(len(out), dtype=int)
    current = 0.0

    for i, value in enumerate(qrs.to_numpy(dtype=float)):
        if np.isfinite(value):
            if value > threshold and trend_up[i]:
                current = 1.0
                long_signal[i] = 1
            elif value < -threshold and trend_down[i]:
                current = -1.0 if allow_short else 0.0
                short_signal[i] = 1
        raw_position[i] = current

    out["qrs"] = qrs
    out["trend_up"] = trend_up.astype(int)
    out["trend_down"] = trend_down.astype(int)
    out["long_signal"] = long_signal
    out["short_signal"] = short_signal
    out["raw_position"] = raw_position
    out["position"] = pd.Series(raw_position, index=out.index).shift(1).fillna(0.0)
    return out


def generate_qrs_signals(
    data: pd.DataFrame,
    signal_col: str = "qrs_zscore",
    long_threshold: float = 0.7,
    exit_threshold: float = -0.7,
) -> pd.DataFrame:
    if signal_col not in data.columns:
        raise ValueError(f"Signal column not found: {signal_col}")

    out = data.copy().sort_values("date").reset_index(drop=True)
    factor = out[signal_col].astype(float)
    raw_position = np.zeros(len(out), dtype=float)
    current = 0.0

    for i, value in enumerate(factor):
        if np.isfinite(value):
            if value > float(long_threshold):
                current = 1.0
            elif value < float(exit_threshold):
                current = 0.0
        raw_position[i] = current

    out["raw_signal"] = raw_position
    out["position"] = pd.Series(raw_position, index=out.index).shift(1).fillna(0.0)
    return out
