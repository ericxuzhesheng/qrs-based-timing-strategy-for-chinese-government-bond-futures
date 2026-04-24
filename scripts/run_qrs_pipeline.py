from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest import performance_summary, run_backtest
from src.data_loader import aggregate_to_daily, discover_input_file, load_market_data
from src.qrs_calculator import calculate_qrs
from src.signal_generator import generate_qrs_signals
from src.utils import ensure_dir, format_number, format_percent, markdown_table, project_path
from src.visualization import plot_drawdown, plot_nav_comparison, plot_qrs_future_return, plot_qrs_price_overlay


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run QRS timing pipeline for Chinese government bond futures.")
    parser.add_argument("--input", default=None, help="CSV/XLSX input file. If omitted, auto-discover a file.")
    parser.add_argument("--sheet-name", default=None, help="Excel sheet name or index. Defaults to the first sheet.")
    parser.add_argument("--contract", default="T", help="Contract label, e.g. T, TL, TF, TS.")
    parser.add_argument("--rolling-window", type=int, default=18)
    parser.add_argument("--zscore-window", type=int, default=120)
    parser.add_argument("--r2-power", type=float, default=2.0)
    parser.add_argument("--slope-window", type=int, default=20)
    parser.add_argument("--percentile-window", type=int, default=120)
    parser.add_argument("--long-threshold", type=float, default=0.7)
    parser.add_argument("--exit-threshold", type=float, default=-0.7)
    return parser.parse_args()


def _sheet_value(value: str | None) -> str | int | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    return int(text) if text.isdigit() else text


def build_report(summary: pd.DataFrame, metadata: dict[str, str]) -> str:
    display = summary.copy()
    for col in ["cumulative_return", "annualized_return", "annualized_volatility", "max_drawdown", "win_rate"]:
        display[col] = display[col].map(format_percent)
    for col in ["sharpe_ratio", "calmar_ratio", "turnover"]:
        display[col] = display[col].map(format_number)
    table = markdown_table(display)

    return f'''# 基于 QRS 的中国国债期货择时研究报告 | QRS-Based Timing Strategy Report for Chinese Government Bond Futures

<p align="center">
  <a href="#zh"><img src="https://img.shields.io/badge/LANGUAGE-%E4%B8%AD%E6%96%87-E84D3D?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE 中文"></a>
  <a href="#en"><img src="https://img.shields.io/badge/LANGUAGE-ENGLISH-2F73C9?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE ENGLISH"></a>
</p>

<a id="zh"></a>

## 简体中文

当前语言：中文 | [Switch to English](#en)

---

### 1. 项目概述

本报告展示基于 QRS 指标的中国国债期货择时研究流程。当前运行合约：`{metadata['contract']}`；输入数据：`{metadata['input_file']}`；样本区间：`{metadata['start_date']} 至 {metadata['end_date']}`。

### 2. 研究动机

国债期货价格受到利率预期、资金面、风险偏好和政策变化影响。QRS/RSRS 类指标通过价格区间中的阻力与支撑关系刻画趋势质量，可作为日频择时因子。

### 3. QRS 指标解释

本项目沿用原始 `qrs_timing.py` 的核心公式：在滚动窗口内回归 `high = alpha + beta * low + epsilon`，将斜率 beta 进行滚动 z-score 标准化，并使用 R² 的幂作为趋势拟合质量惩罚项。较高 QRS 通常代表趋势状态较强或上行动能较好，较低 QRS 代表趋势弱化或下行动能增强。QRS 是择时因子，不是完整交易系统。

### 4. 数据与预处理

数据读取支持 CSV 和 Excel，自动识别日期、OHLC、成交量和持仓量字段。若输入为 5 分钟数据，pipeline 会聚合为日频 OHLCV 后再计算日频 QRS 与回测结果。

### 5. 方法论

- 滚动窗口：`{metadata['rolling_window']}`
- z-score 窗口：`{metadata['zscore_window']}`
- R² 惩罚幂：`{metadata['r2_power']}`
- 信号列：`qrs_zscore`

### 6. 信号设计

当 `qrs_zscore > {metadata['long_threshold']}` 时，原始仓位设为 1；当 `qrs_zscore < {metadata['exit_threshold']}` 时，原始仓位设为 0；中性区域维持前一日原始仓位。

### 7. 防止未来函数

所有交易仓位均滞后一日执行，以避免未来函数。QRS 指标、滚动 z-score 与滚动分位数均只使用当日及以前信息。

### 8. 回测框架

回测采用 close-to-close 日频收益；基准为 long-only 持有；策略收益为滞后一日后的仓位乘以当日收益。

### 9. 结果展示

{table}

![QRS Price Overlay](figures/qrs_price_overlay.png)

![Strategy NAV](figures/nav_comparison.png)

![Drawdown](figures/drawdown.png)

![QRS Future Return](figures/qrs_future_return.png)

### 10. 局限性

本研究未考虑手续费、滑点、保证金占用、展期规则和真实成交约束。结果依赖输入数据质量与样本区间，不构成投资建议。

### 11. 后续改进

后续可加入合约展期处理、交易成本、参数稳定性检验、样本外验证、TF/TS/TL 多品种扩展和风险预算模块。

### 12. 免责声明

本项目仅用于量化研究与代码示例，不构成任何投资建议或收益承诺。

<a id="en"></a>

## English

Current language: English | [切换到中文](#zh)

---

### 1. Project Overview

This report presents a QRS-based timing research workflow for Chinese government bond futures. Current contract: `{metadata['contract']}`; input data: `{metadata['input_file']}`; sample period: `{metadata['start_date']} to {metadata['end_date']}`.

### 2. Research Motivation

Chinese government bond futures are driven by rate expectations, liquidity, risk appetite, and policy changes. QRS/RSRS-style indicators describe trend quality through resistance-support relationships and can be used as daily timing factors.

### 3. QRS Indicator Interpretation

This project preserves the core formula from the original `qrs_timing.py`: regress `high = alpha + beta * low + epsilon` in a rolling window, standardize beta with a rolling z-score, and penalize it by a power of R². Higher QRS indicates stronger trend quality or better upside momentum, while lower QRS indicates weaker trends or downside pressure. QRS should be treated as a timing factor, not a complete trading system.

### 4. Data and Preprocessing

The loader supports CSV and Excel files and automatically detects date, OHLC, volume, and open-interest fields. If the input is 5-minute data, the pipeline aggregates it to daily OHLCV before computing daily QRS and backtest results.

### 5. Methodology

- Rolling window: `{metadata['rolling_window']}`
- z-score window: `{metadata['zscore_window']}`
- R² penalty power: `{metadata['r2_power']}`
- Signal column: `qrs_zscore`

### 6. Signal Design

When `qrs_zscore > {metadata['long_threshold']}`, the raw position is set to 1. When `qrs_zscore < {metadata['exit_threshold']}`, the raw position is set to 0. The neutral zone carries the previous raw position.

### 7. Look-Ahead Bias Control

All trading positions are lagged by one trading day to avoid look-ahead bias. QRS, rolling z-score, and rolling percentile use only current and historical information.

### 8. Backtest Framework

The backtest uses daily close-to-close returns. The benchmark is long-only. Strategy return equals the one-day-lagged position multiplied by daily return.

### 9. Results and Outputs

{table}

![QRS Price Overlay](figures/qrs_price_overlay.png)

![Strategy NAV](figures/nav_comparison.png)

![Drawdown](figures/drawdown.png)

![QRS Future Return](figures/qrs_future_return.png)

### 10. Limitations

The study does not include transaction costs, slippage, margin usage, contract roll rules, or real execution constraints. Results depend on data quality and sample period and are not investment advice.

### 11. Future Improvements

Future work may include contract roll handling, trading costs, parameter stability checks, out-of-sample validation, TF/TS/TL expansion, and risk-budget modules.

### 12. Disclaimer

This project is for quantitative research and code demonstration only. It does not constitute investment advice or any return guarantee.
'''


def run_pipeline(args: argparse.Namespace) -> None:
    input_path = Path(args.input) if args.input else discover_input_file(args.contract)
    if not input_path.is_absolute():
        input_path = (ROOT / input_path).resolve()

    raw = load_market_data(input_path, sheet_name=_sheet_value(args.sheet_name))
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

    processed_path = project_path("data", "processed", "qrs_daily.csv")
    summary_path = project_path("results", "tables", "backtest_summary.csv")
    nav_path = project_path("results", "tables", "strategy_nav.csv")
    report_path = project_path("results", "report.md")
    figures_dir = project_path("results", "figures")
    for path in [processed_path.parent, summary_path.parent, figures_dir]:
        ensure_dir(path)

    bt.to_csv(processed_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    bt[["date", "strategy_return", "benchmark_return", "strategy_nav", "benchmark_nav", "position", "turnover"]].to_csv(
        nav_path, index=False, encoding="utf-8-sig"
    )

    plot_qrs_price_overlay(bt, figures_dir / "qrs_price_overlay.png")
    plot_nav_comparison(bt, figures_dir / "nav_comparison.png")
    plot_drawdown(bt, figures_dir / "drawdown.png")
    plot_qrs_future_return(bt, figures_dir / "qrs_future_return.png")

    metadata = {
        "contract": args.contract,
        "input_file": input_path.name,
        "start_date": pd.to_datetime(bt["date"].iloc[0]).strftime("%Y-%m-%d"),
        "end_date": pd.to_datetime(bt["date"].iloc[-1]).strftime("%Y-%m-%d"),
        "rolling_window": str(args.rolling_window),
        "zscore_window": str(args.zscore_window),
        "r2_power": str(args.r2_power),
        "long_threshold": str(args.long_threshold),
        "exit_threshold": str(args.exit_threshold),
    }
    report_path.write_text(build_report(summary, metadata), encoding="utf-8")

    print(f"Input: {input_path}")
    print(f"Rows: raw={len(raw)}, daily={len(daily)}, output={len(bt)}")
    print(f"Saved: {processed_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {nav_path}")
    print(f"Saved: {report_path}")


if __name__ == "__main__":
    run_pipeline(parse_args())
