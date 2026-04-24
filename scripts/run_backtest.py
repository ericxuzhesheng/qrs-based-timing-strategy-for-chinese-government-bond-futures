from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_qrs_pipeline import build_report
from src.backtest import performance_summary, run_backtest
from src.signal_generator import generate_qrs_signals
from src.utils import ensure_dir, project_path
from src.visualization import plot_drawdown, plot_nav_comparison, plot_qrs_future_return, plot_qrs_price_overlay


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rerun QRS backtest from processed qrs_daily.csv.")
    parser.add_argument("--input", default=str(project_path("data", "processed", "qrs_daily.csv")))
    parser.add_argument("--contract", default="T")
    parser.add_argument("--long-threshold", type=float, default=0.7)
    parser.add_argument("--exit-threshold", type=float, default=-0.7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    processed = pd.read_csv(args.input, parse_dates=["date"])
    signals = generate_qrs_signals(processed, long_threshold=args.long_threshold, exit_threshold=args.exit_threshold)
    bt = run_backtest(signals)
    summary = performance_summary(bt)

    figures_dir = project_path("results", "figures")
    tables_dir = project_path("results", "tables")
    ensure_dir(figures_dir)
    ensure_dir(tables_dir)

    bt.to_csv(project_path("data", "processed", "qrs_daily.csv"), index=False, encoding="utf-8-sig")
    summary.to_csv(tables_dir / "backtest_summary.csv", index=False, encoding="utf-8-sig")
    bt[["date", "strategy_return", "benchmark_return", "strategy_nav", "benchmark_nav", "position", "turnover"]].to_csv(
        tables_dir / "strategy_nav.csv", index=False, encoding="utf-8-sig"
    )
    plot_qrs_price_overlay(bt, figures_dir / "qrs_price_overlay.png")
    plot_nav_comparison(bt, figures_dir / "nav_comparison.png")
    plot_drawdown(bt, figures_dir / "drawdown.png")
    plot_qrs_future_return(bt, figures_dir / "qrs_future_return.png")

    metadata = {
        "contract": args.contract,
        "input_file": Path(args.input).name,
        "start_date": pd.to_datetime(bt["date"].iloc[0]).strftime("%Y-%m-%d"),
        "end_date": pd.to_datetime(bt["date"].iloc[-1]).strftime("%Y-%m-%d"),
        "rolling_window": "from processed data",
        "zscore_window": "from processed data",
        "r2_power": "from processed data",
        "long_threshold": str(args.long_threshold),
        "exit_threshold": str(args.exit_threshold),
    }
    project_path("results", "report.md").write_text(build_report(summary, metadata), encoding="utf-8")
    print("Backtest rerun complete.")


if __name__ == "__main__":
    main()
