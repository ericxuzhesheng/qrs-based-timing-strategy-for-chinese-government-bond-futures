from __future__ import annotations

import logging
import pandas as pd
import numpy as np
from typing import Any, List, Dict

from src.qrs_calculator import calculate_qrs_intraday
from src.signal_generator import generate_qrs_intraday_signals
from src.backtest import run_intraday_backtest, intraday_performance_summary
from src.parameter_selection import evaluate_qrs_predictive_power

logger = logging.getLogger(__name__)

def run_dynamic_qrs_selection(
    ohlc: pd.DataFrame,
    qrs_param_grid: List[Dict[str, Any]],
    signal_param_grid: List[Dict[str, Any]],
    train_window_bars: int = 54 * 60,
    test_window_bars: int = 54 * 10,
    rebalance_every_bars: int = 54,
    horizon_bars: int = 54,
    selection_metric: str = "rank_ic",
    allow_short: bool = True,
    periods_per_year: int = 252 * 54,
) -> pd.DataFrame:
    """
    Run walk-forward backtest with dynamic parameter selection.
    
    Two-step selection:
    1. Select best QRS factor params based on predictive power (IC/Rank IC).
    2. Select best Signal params based on training Sharpe.
    """
    df = ohlc.copy().sort_values("date").reset_index(drop=True)
    n_total = len(df)
    
    # Pre-calculate all QRS factor variations for caching
    qrs_cache = {}
    for p in qrs_param_grid:
        key = (p["N"], p["M"], p["n"], p.get("normalize_penalty", False))
        if key not in qrs_cache:
            qrs_cache[key] = calculate_qrs_intraday(
                df, N=p["N"], M=p["M"], n=p["n"], 
                normalize_penalty=p.get("normalize_penalty", False)
            )["qrs"]
            
    # Result containers
    out_signals = []
    param_trace = []
    
    # Rolling loop
    # Start when we have enough data for the first training window
    start_idx = train_window_bars
    
    while start_idx < n_total:
        train_start = max(0, start_idx - train_window_bars)
        train_end = start_idx
        test_end = min(n_total, start_idx + rebalance_every_bars)
        
        if train_end - train_start < train_window_bars * 0.8: # Tolerance
             break
             
        train_df = df.iloc[train_start:train_end]
        test_df = df.iloc[train_end:test_end]
        
        if test_df.empty:
            break
            
        # Step 1: Select Best QRS Factor
        best_qrs_params = None
        best_qrs_score = -np.inf
        
        for p in qrs_param_grid:
            key = (p["N"], p["M"], p["n"], p.get("normalize_penalty", False))
            qrs_train = qrs_cache[key].iloc[train_start:train_end]
            
            metrics = evaluate_qrs_predictive_power(
                qrs_train, train_df["close"], horizon_bars=horizon_bars
            )
            score = metrics.get(selection_metric, np.nan)
            
            if not np.isnan(score) and score > best_qrs_score:
                best_qrs_score = score
                best_qrs_params = p
                
        if best_qrs_params is None:
            # Fallback to first if none meet criteria
            best_qrs_params = qrs_param_grid[0]
            best_qrs_score = 0.0
            
        # Step 2: Select Best Signal Params using the selected QRS
        best_signal_params = None
        best_signal_sharpe = -np.inf
        
        selected_qrs_full = qrs_cache[(best_qrs_params["N"], best_qrs_params["M"], best_qrs_params["n"], best_qrs_params.get("normalize_penalty", False))]
        train_with_qrs = train_df.copy()
        train_with_qrs["qrs"] = selected_qrs_full.iloc[train_start:train_end]
        
        for sp in signal_param_grid:
            sig_train = generate_qrs_intraday_signals(
                train_with_qrs,
                S=sp["S"],
                trend_method=sp["trend_method"],
                ma_len_days=sp.get("ma_len_days", 5),
                compare_lag_days=sp.get("compare_lag_days", 2),
                ma_short=sp.get("ma_short", 5),
                ma_long=sp.get("ma_long", 20),
                allow_short=allow_short
            )
            bt_train = run_intraday_backtest(sig_train, periods_per_year=periods_per_year)
            summary_train = intraday_performance_summary(bt_train, periods_per_year=periods_per_year)
            sharpe = summary_train.loc[summary_train["portfolio"] == "QRS Strategy", "sharpe_ratio"].values[0]
            
            if not np.isnan(sharpe) and sharpe > best_signal_sharpe:
                best_signal_sharpe = sharpe
                best_signal_params = sp
                
        if best_signal_params is None:
            best_signal_params = signal_param_grid[0]
            
        # Apply selected params to test window
        test_with_qrs = test_df.copy()
        test_with_qrs["qrs"] = selected_qrs_full.iloc[train_end:test_end]
        
        # Note: generate_qrs_intraday_signals internally does shift(1) for position.
        # However, to be extra safe in walk-forward, we need to ensure the FIRST position 
        # of the test window uses the LAST signal from the training window IF POSSIBLE.
        # But wait, generate_qrs_intraday_signals creates 'position' as shift(1) of 'raw_position'.
        # If we only pass the test window, the first row's position will be 0 (fillna).
        # To fix this, we should pass a bit of history to generate_qrs_intraday_signals or stitch correctly.
        
        # Better: apply to train+test and then slice test. 
        # But trend filter also needs history.
        history_start = max(0, train_end - 60*54) # 60 days history for MA
        combined_for_sig = df.iloc[history_start:test_end].copy()
        combined_for_sig["qrs"] = selected_qrs_full.iloc[history_start:test_end]
        
        sig_combined = generate_qrs_intraday_signals(
            combined_for_sig,
            S=best_signal_params["S"],
            trend_method=best_signal_params["trend_method"],
            ma_len_days=best_signal_params.get("ma_len_days", 5),
            compare_lag_days=best_signal_params.get("compare_lag_days", 2),
            ma_short=best_signal_params.get("ma_short", 5),
            ma_long=best_signal_params.get("ma_long", 20),
            allow_short=allow_short
        )
        
        # Slice the test part
        test_sig_final = sig_combined.iloc[-(test_end - train_end):].copy()
        
        out_signals.append(test_sig_final)
        
        # Log parameter selection
        trace_entry = {
            "date": test_df["date"].iloc[0],
            "selection_score": best_qrs_score,
            "train_sharpe": best_signal_sharpe,
            **{f"selected_{k}": v for k, v in best_qrs_params.items()},
            **{f"selected_{k}": v for k, v in best_signal_params.items()}
        }
        param_trace.append(trace_entry)
        
        # Move forward
        start_idx += rebalance_every_bars
        
    if not out_signals:
        return pd.DataFrame()
        
    final_bt_df = pd.concat(out_signals).reset_index(drop=True)
    
    # Run final backtest on the concatenated signals
    final_bt = run_intraday_backtest(final_bt_df, periods_per_year=periods_per_year)
    
    # Add selected params info
    param_df = pd.DataFrame(param_trace)
    
    # Merge trace info into final_bt for analysis (optional but helpful)
    # Since trace is per rebalance, we forward fill it
    final_bt["date_dt"] = pd.to_datetime(final_bt["date"])
    param_df["date_dt"] = pd.to_datetime(param_df["date"])
    
    final_bt = pd.merge_asof(
        final_bt.sort_values("date_dt"), 
        param_df.sort_values("date_dt"), 
        on="date_dt", 
        direction="backward",
        suffixes=("", "_trace")
    )
    
    return final_bt, param_df
