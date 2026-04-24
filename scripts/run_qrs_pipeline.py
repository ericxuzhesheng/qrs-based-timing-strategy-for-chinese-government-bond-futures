from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest import (
    intraday_debug_stats,
    intraday_performance_summary,
    performance_summary,
    run_backtest,
    run_intraday_backtest,
)
from src.data_loader import aggregate_to_daily, discover_input_file, load_market_data
from src.grid_search import run_grid_search
from src.qrs_calculator import calculate_qrs, calculate_qrs_intraday
from src.signal_generator import generate_qrs_signals, generate_qrs_intraday_signals
from src.utils import ensure_dir, format_number, format_percent, markdown_table, project_path
from src.visualization import (
    plot_best_strategy_position,
    plot_drawdown,
    plot_nav_comparison,
    plot_qrs_future_return,
    plot_qrs_price_overlay,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run QRS timing pipeline for Chinese government bond futures.")
    parser.add_argument("--mode", choices=["daily_baseline", "intraday"], default="intraday")
    parser.add_argument("--input", default=None, help="CSV/XLSX input file. If omitted, auto-discover a file.")
    parser.add_argument("--sheet-name", default=None, help="Excel sheet name or index. Defaults to the first sheet.")
    parser.add_argument("--contract", default="T", help="Contract label, e.g. T, TL, TF, TS.")
    parser.add_argument("--start-date", default="2024-01-01")
    parser.add_argument("--N", type=int, default=16)
    parser.add_argument("--M", type=int, default=600)
    parser.add_argument("--rolling-window", type=int, default=18)
    parser.add_argument("--zscore-window", type=int, default=120)
    parser.add_argument("--r2-power", type=float, default=2.0)
    parser.add_argument("--S", type=float, default=0.5)
    parser.add_argument("--slope-window", type=int, default=20)
    parser.add_argument("--percentile-window", type=int, default=120)
    parser.add_argument("--long-threshold", type=float, default=0.7)
    parser.add_argument("--exit-threshold", type=float, default=-0.7)
    parser.add_argument("--trend-method", default="ma_compare", choices=["ma_compare", "ma_cross", "price_compare"])
    parser.add_argument("--ma-len-days", type=int, default=5)
    parser.add_argument("--compare-lag-days", type=int, default=2)
    parser.add_argument("--ma-short", type=int, default=5)
    parser.add_argument("--ma-long", type=int, default=20)
    parser.add_argument("--periods-per-year", type=int, default=252 * 54)
    parser.add_argument("--run-grid-search", dest="run_grid_search", action="store_true")
    parser.add_argument("--no-grid-search", dest="run_grid_search", action="store_false")
    parser.set_defaults(run_grid_search=False)
    parser.add_argument("--allow-short", dest="allow_short", action="store_true")
    parser.add_argument("--no-allow-short", dest="allow_short", action="store_false")
    parser.set_defaults(allow_short=True)
    return parser.parse_args()


def _sheet_value(value: str | None) -> str | int | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    return int(text) if text.isdigit() else text


def _resolve_input(path: str | None, contract: str) -> Path:
    input_path = Path(path) if path else discover_input_file(contract)
    if not input_path.is_absolute():
        input_path = (ROOT / input_path).resolve()
    return input_path


def _vertical_metric_table(summary: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        ("Cumulative Return", "cumulative_return", True),
        ("Annualized Return", "annualized_return", True),
        ("Annualized Volatility", "annualized_volatility", True),
        ("Sharpe Ratio", "sharpe_ratio", False),
        ("Max Drawdown", "max_drawdown", True),
        ("Calmar Ratio", "calmar_ratio", False),
        ("Win Rate", "win_rate", True),
        ("Turnover", "turnover", False),
    ]
    rows = []
    for label, col, is_pct in metrics:
        row: dict[str, str] = {"Metric": label}
        for _, item in summary.iterrows():
            value = float(item[col])
            row[str(item["portfolio"])] = format_percent(value) if is_pct else format_number(value)
        rows.append(row)
    return pd.DataFrame(rows)


def _debug_table(debug: pd.DataFrame) -> pd.DataFrame:
    row = debug.iloc[0].to_dict()
    rows = []
    for key, value in row.items():
        if isinstance(value, float):
            display = format_percent(value) if key.endswith("ratio") or "return" in key or "drawdown" in key else format_number(value)
        else:
            display = str(value)
        rows.append({"Metric": key, "Value": display})
    return pd.DataFrame(rows)


def build_report(
    summary: pd.DataFrame,
    metadata: dict[str, Any],
    debug: pd.DataFrame | None = None,
    best_params: dict[str, Any] | None = None,
) -> str:
    metric_table = markdown_table(_vertical_metric_table(summary))
    debug_table = markdown_table(_debug_table(debug)) if debug is not None and not debug.empty else ""
    best_params_text = json.dumps(best_params or {}, ensure_ascii=False, indent=2)

    return rf'''# 基于 QRS 的中国国债期货择时研究报告 | QRS-Based Timing Strategy Report for Chinese Government Bond Futures

<p align="center">
<a href="#zh"><img src="https://img.shields.io/badge/LANGUAGE-%E4%B8%AD%E6%96%87-E84D3D?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE 中文"></a>
<a href="#en"><img src="https://img.shields.io/badge/LANGUAGE-ENGLISH-2F73C9?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE ENGLISH"></a>
</p>

<a id="zh"></a>

## 简体中文

当前语言：中文 | [Switch to English](#en)

---

### 1. 项目概述

本报告展示基于 QRS 指标的中国国债期货择时研究流程. 当前运行模式：`{metadata['mode']}`；当前运行合约：`{metadata['contract']}`；输入数据：`{metadata['input_file']}`；样本区间：`{metadata['start_date']} 至 {metadata['end_date']}`。

### 2. 核心模型逻辑

#### 2.1 QRS 因子构建
QRS 类指标通过价格区间中的阻力与支撑关系刻画趋势质量. 在 5 分钟 OHLC 上执行局部回归：

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t, \quad t \in \{{1,2,\ldots,N\}}
$$

对斜率 $\beta$ 进行滚动 Z-score 标准化，并引入 $R^2$ 作为惩罚项：

$$
qrs = zscore(\beta, M) \times (R^2)^n
$$

#### 2.2 信号设计与趋势过滤
状态机规则：
- **做多**：$QRS > +S$ 且日频趋势向上, 仓位设为 1；
- **做空**：$QRS < -S$ 且日频趋势向下, 仓位设为 -1（若允许做空）；
- **维持**：维持上一根 5 分钟 Bar 的原始仓位。

### 3. 参数搜索空间与最佳参数

默认搜索空间包含 $S$ 阈值、趋势判断方式及均线周期等.

本次回测采用的最佳参数：
```json
{best_params_text}
```

### 4. 回测结果汇总

{metric_table}

### 5. Debug 辅助指标

{debug_table}

### 6. 可视化图表

#### 6.1 因子与价格叠加
![QRS Price Overlay](figures/qrs_price_overlay.png)

#### 6.2 策略净值对比
![Strategy NAV](figures/nav_comparison.png)

#### 6.3 策略回撤
![Drawdown](figures/drawdown.png)

#### 6.4 最佳参数持仓分布
![Best Strategy Position](figures/best_strategy_position.png)

#### 6.5 因子择时能力 (Timing Coefficient)
![QRS Future Return](figures/qrs_future_return.png)

### 7. 免责声明
本报告仅用于量化研究与代码示例，不构成任何投资建议或收益承诺.

---

<a id="en"></a>

## English

Current language: English | [切换到中文](#zh)

---

### 1. Project Overview

This report presents a QRS-based timing workflow for Chinese government bond futures. Current mode: `{metadata['mode']}`; contract: `{metadata['contract']}`; input data: `{metadata['input_file']}`; sample period: `{metadata['start_date']} to {metadata['end_date']}`.

### 2. Core Model Logic

#### 2.1 QRS Factor Construction
QRS indicators describe trend quality through resistance-support relationships. A local regression is performed on 5-minute OHLC bars:

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t, \quad t \in \{{1,2,\ldots,N\}}
$$

The slope $\beta$ is standardized via rolling Z-score and adjusted by an $R^2$ penalty term:

$$
qrs = zscore(\beta, M) \times (R^2)^n
$$

#### 2.2 Signal Design and Trend Filter
The state machine rules:
- **Long**: $QRS > +S$ and daily trend is UP, position becomes 1;
- **Short**: $QRS < -S$ and daily trend is DOWN, position becomes -1 (if allowed);
- **Otherwise**: Carry the previous raw position.

### 3. Parameter Search Space & Best Parameters

The default search space covers $S$ thresholds, trend methods, and MA periods.

Parameters used in this run:
```json
{best_params_text}
```

### 4. Backtest Results

{metric_table}

### 5. Debug Metrics

{debug_table}

### 6. Visualization

#### 6.1 Factor & Price Overlay
![QRS Price Overlay](figures/qrs_price_overlay.png)

#### 6.2 Strategy NAV Comparison
![Strategy NAV](figures/nav_comparison.png)

#### 6.3 Strategy Drawdown
![Drawdown](figures/drawdown.png)

#### 6.4 Best Strategy Position
![Best Strategy Position](figures/best_strategy_position.png)

#### 6.5 Timing Coefficient (QRS Future Return)
![QRS Future Return](figures/qrs_future_return.png)

### 7. Disclaimer
This report is for quantitative research and demonstration only. It does not constitute investment advice or any return guarantee.
'''


def _save_common_outputs(bt: pd.DataFrame, summary: pd.DataFrame, metadata: dict[str, Any], debug: pd.DataFrame | None, best_params: dict[str, Any] | None) -> None:
    figures_dir = project_path("results", "figures")
    tables_dir = project_path("results", "tables")
    ensure_dir(figures_dir)
    ensure_dir(tables_dir)

    summary.to_csv(tables_dir / "backtest_summary.csv", index=False, encoding="utf-8-sig")
    nav_cols = [c for c in ["date", "ret_strategy", "ret_benchmark", "ret_excess", "nav_strategy", "nav_benchmark", "nav_excess", "position", "turnover"] if c in bt.columns]
    if not nav_cols:
        nav_cols = ["date", "strategy_return", "benchmark_return", "strategy_nav", "benchmark_nav", "position", "turnover"]
    bt[nav_cols].to_csv(tables_dir / "strategy_nav.csv", index=False, encoding="utf-8-sig")

    plot_qrs_price_overlay(bt, figures_dir / "qrs_price_overlay.png")
    plot_nav_comparison(bt, figures_dir / "nav_comparison.png")
    plot_drawdown(bt, figures_dir / "drawdown.png")
    plot_qrs_future_return(bt, figures_dir / "qrs_future_return.png")
    if "position" in bt.columns:
        plot_best_strategy_position(bt, figures_dir / "best_strategy_position.png")

    project_path("results", "report.md").write_text(build_report(summary, metadata, debug, best_params), encoding="utf-8")


def run_intraday(args: argparse.Namespace, raw: pd.DataFrame, input_path: Path) -> None:
    qrs_all = calculate_qrs_intraday(raw, N=args.N, M=args.M, n=args.r2_power)
    qrs_eval = qrs_all.loc[pd.to_datetime(qrs_all["date"]) >= pd.to_datetime(args.start_date)].copy().reset_index(drop=True)
    if qrs_eval.empty:
        raise ValueError(f"No rows after start date {args.start_date}")

    best_params: dict[str, Any] = {
        "S": args.S,
        "trend_method": args.trend_method,
        "ma_len_days": args.ma_len_days,
        "compare_lag_days": args.compare_lag_days,
        "ma_short": args.ma_short,
        "ma_long": args.ma_long,
        "grid_search": False,
    }

    tables_dir = project_path("results", "tables")
    ensure_dir(tables_dir)
    if args.run_grid_search:
        grid_results, best_params = run_grid_search(qrs_eval, allow_short=args.allow_short, periods_per_year=args.periods_per_year)
        best_params = {k: (None if pd.isna(v) else v) for k, v in best_params.items()}
        best_params["grid_search"] = True
        grid_results.to_csv(tables_dir / "qrs_grid_search_results.csv", index=False, encoding="utf-8-sig")
        (tables_dir / "best_params.json").write_text(json.dumps(best_params, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        (tables_dir / "best_params.json").write_text(json.dumps(best_params, ensure_ascii=False, indent=2), encoding="utf-8")

    signal_df = generate_qrs_intraday_signals(
        qrs_eval,
        S=float(best_params["S"]),
        trend_method=str(best_params["trend_method"]),
        ma_len_days=int(best_params.get("ma_len_days") or args.ma_len_days),
        compare_lag_days=int(best_params.get("compare_lag_days") or args.compare_lag_days),
        ma_short=int(best_params.get("ma_short") or args.ma_short),
        ma_long=int(best_params.get("ma_long") or args.ma_long),
        allow_short=args.allow_short,
    )
    bt = run_intraday_backtest(signal_df, periods_per_year=args.periods_per_year)
    summary = intraday_performance_summary(bt, periods_per_year=args.periods_per_year)
    debug = intraday_debug_stats(bt)

    processed_path = project_path("data", "processed", "qrs_intraday.csv")
    ensure_dir(processed_path.parent)
    bt.to_csv(processed_path, index=False, encoding="utf-8-sig")

    metadata = {
        "mode": "intraday",
        "contract": args.contract,
        "input_file": input_path.name,
        "start_date": pd.to_datetime(bt["date"].iloc[0]).strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": pd.to_datetime(bt["date"].iloc[-1]).strftime("%Y-%m-%d %H:%M:%S"),
        "data_frequency": "5-minute intraday",
        "allow_short": str(args.allow_short),
        "run_grid_search": str(args.run_grid_search),
        "periods_per_year": str(args.periods_per_year),
        "N": str(args.N),
        "M": str(args.M),
        "r2_power": str(args.r2_power),
        "trend_method": str(best_params["trend_method"]),
    }
    _save_common_outputs(bt, summary, metadata, debug, best_params)
    print(f"Mode: intraday")
    print(f"Input: {input_path}")
    print(f"Rows: raw={len(raw)}, eval={len(qrs_eval)}, output={len(bt)}")
    print(f"Best params: {best_params}")
    print(summary.to_string(index=False))
    print(debug.to_string(index=False))


def run_daily_baseline(args: argparse.Namespace, raw: pd.DataFrame, input_path: Path) -> None:
    daily = aggregate_to_daily(raw)
    qrs = calculate_qrs(
        daily,
        rolling_window=args.rolling_window,
        zscore_window=args.zscore_window,
        r2_power=args.r2_power,
        slope_window=args.slope_window,
        percentile_window=args.percentile_window,
    )
    signals = generate_qrs_signals(qrs, long_threshold=args.long_threshold, exit_threshold=args.exit_threshold)
    bt = run_backtest(signals)
    summary = performance_summary(bt)
    processed_path = project_path("data", "processed", "qrs_daily_baseline.csv")
    ensure_dir(processed_path.parent)
    bt.to_csv(processed_path, index=False, encoding="utf-8-sig")
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
        "N": str(args.rolling_window),
        "M": str(args.zscore_window),
        "r2_power": str(args.r2_power),
        "trend_method": "none",
    }
    _save_common_outputs(bt, summary, metadata, None, {"mode": "daily_baseline"})
    print(f"Mode: daily_baseline")
    print(f"Input: {input_path}")
    print(f"Rows: raw={len(raw)}, daily={len(daily)}, output={len(bt)}")


def run_pipeline(args: argparse.Namespace) -> None:
    input_path = _resolve_input(args.input, args.contract)
    raw = load_market_data(input_path, sheet_name=_sheet_value(args.sheet_name))
    if args.mode == "intraday":
        run_intraday(args, raw, input_path)
    else:
        run_daily_baseline(args, raw, input_path)


if __name__ == "__main__":
    run_pipeline(parse_args())
