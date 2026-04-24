from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_qrs_pipeline import _save_common_outputs
from src.backtest import intraday_debug_stats, intraday_performance_summary, performance_summary, run_backtest, run_intraday_backtest
from src.utils import project_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rerun QRS backtest from processed data.")
    parser.add_argument("--mode", choices=["intraday", "daily_baseline"], default="intraday")
    parser.add_argument("--input", default=None)
    parser.add_argument("--contract", default="T")
    parser.add_argument("--periods-per-year", type=int, default=252 * 54)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    default_input = project_path("data", "processed", "qrs_intraday.csv") if args.mode == "intraday" else project_path("data", "processed", "qrs_daily_baseline.csv")
    input_path = Path(args.input) if args.input else default_input
    df = pd.read_csv(input_path, parse_dates=["date"])

    if args.mode == "intraday":
        bt = run_intraday_backtest(df, periods_per_year=args.periods_per_year)
        summary = intraday_performance_summary(bt, periods_per_year=args.periods_per_year)
        debug = intraday_debug_stats(bt)
        metadata = {
            "mode": "intraday",
            "contract": args.contract,
            "input_file": input_path.name,
            "start_date": pd.to_datetime(bt["date"].iloc[0]).strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": pd.to_datetime(bt["date"].iloc[-1]).strftime("%Y-%m-%d %H:%M:%S"),
            "data_frequency": "5-minute intraday",
            "allow_short": str((bt["position"] < 0).any()),
            "run_grid_search": "from processed data",
            "periods_per_year": str(args.periods_per_year),
            "N": "from processed data",
            "M": "from processed data",
            "r2_power": "from processed data",
            "trend_method": "from processed data",
        }
        _save_common_outputs(bt, summary, metadata, debug, {"source": str(input_path)})
    else:
        bt = run_backtest(df)
        summary = performance_summary(bt)
        metadata = {
            "mode": "daily_baseline",
            "contract": args.contract,
            "input_file": input_path.name,
            "start_date": pd.to_datetime(bt["date"].iloc[0]).strftime("%Y-%m-%d"),
            "end_date": pd.to_datetime(bt["date"].iloc[-1]).strftime("%Y-%m-%d"),
            "data_frequency": "daily aggregated baseline",
            "allow_short": "False",
            "run_grid_search": "False",
            "periods_per_year": "252",
            "N": "from processed data",
            "M": "from processed data",
            "r2_power": "from processed data",
            "trend_method": "none",
        }
        _save_common_outputs(bt, summary, metadata, None, {"source": str(input_path)})
    print(f"Backtest rerun complete: {args.mode}")


if __name__ == "__main__":
    main()
