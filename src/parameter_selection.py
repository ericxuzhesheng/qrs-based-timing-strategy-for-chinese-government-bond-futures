from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def evaluate_qrs_predictive_power(
    qrs: pd.Series,
    close: pd.Series,
    horizon_bars: int = 54,
    n_quantiles: int = 5,
) -> dict:
    """
    Evaluate the predictive power of a QRS factor series.
    
    Args:
        qrs: The QRS factor series.
        close: The close price series (must have the same index or length).
        horizon_bars: The look-ahead horizon for future returns.
        n_quantiles: Number of quantiles for spread calculation.
        
    Returns:
        A dictionary containing predictive metrics.
    """
    # Calculate future returns: (P_{t+h} / P_t) - 1
    # We use shift(-horizon_bars) to align future return with current factor
    future_ret = close.shift(-horizon_bars) / close - 1.0
    
    # Align factor and future returns, dropping NaNs
    valid_mask = qrs.notna() & future_ret.notna()
    f = qrs[valid_mask]
    r = future_ret[valid_mask]
    
    if len(f) < 20:  # Minimum sample size
        return {
            "ic": np.nan,
            "rank_ic": np.nan,
            "ic_ir": np.nan,
            "positive_ic_ratio": np.nan,
            "future_return_top": np.nan,
            "future_return_bottom": np.nan,
            "future_return_spread": np.nan,
            "monotonicity_score": np.nan,
            "sample_size": len(f)
        }
    
    # 1. Pearson IC
    ic = float(np.corrcoef(f, r)[0, 1])
    
    # 2. Spearman Rank IC
    rank_ic, _ = stats.spearmanr(f, r)
    rank_ic = float(rank_ic)
    
    # 3. ICIR - Since we are likely evaluating on a single window here, 
    # a true ICIR requires rolling ICs. For a static window, we'll return NaN
    # or implement a sub-window logic if needed. 
    # For now, let's keep it as NaN as per prompt instructions for static window.
    ic_ir = np.nan
    
    # 4. Positive IC Ratio
    # If we had a series of ICs, we'd calculate this. 
    # For a single window, it's 1.0 if ic > 0 else 0.0.
    pos_ic_ratio = 1.0 if ic > 0 else 0.0
    
    # 5. Future Return Spread
    # Use qcut to divide into quantiles
    try:
        quantiles = pd.qcut(f, n_quantiles, labels=False, duplicates='drop')
        quantile_returns = r.groupby(quantiles).mean()
        
        top_ret = float(quantile_returns.iloc[-1]) if len(quantile_returns) > 1 else np.nan
        bottom_ret = float(quantile_returns.iloc[0]) if len(quantile_returns) > 1 else np.nan
        spread = top_ret - bottom_ret
        
        # Monotonicity score: correlation between quantile index and quantile return
        if len(quantile_returns) > 2:
            m_score, _ = stats.spearmanr(range(len(quantile_returns)), quantile_returns.values)
            m_score = float(m_score)
        else:
            m_score = np.nan
    except:
        top_ret = np.nan
        bottom_ret = np.nan
        spread = np.nan
        m_score = np.nan
        
    return {
        "ic": ic,
        "rank_ic": rank_ic,
        "ic_ir": ic_ir,
        "positive_ic_ratio": pos_ic_ratio,
        "future_return_top": top_ret,
        "future_return_bottom": bottom_ret,
        "future_return_spread": spread,
        "monotonicity_score": m_score,
        "sample_size": len(f)
    }
