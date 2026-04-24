from __future__ import annotations

import numpy as np
import pandas as pd


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
