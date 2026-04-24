# 基于 QRS 的中国国债期货择时框架 | QRS-Based Timing Strategy for Chinese Government Bond Futures

<p align="center">
  <a href="#zh"><img src="https://img.shields.io/badge/LANGUAGE-%E4%B8%AD%E6%96%87-E84D3D?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE 中文"></a>
  <a href="#en"><img src="https://img.shields.io/badge/LANGUAGE-ENGLISH-2F73C9?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE ENGLISH"></a>
</p>

<a id="zh"></a>

## 简体中文

当前语言：中文 | [Switch to English](#en)

---

### 1. 项目简介

本仓库是一个基于 QRS 指标的中国国债期货择时研究框架，优先支持 10 年国债期货 T，并保留扩展到 TL、TF、TS 等品种的接口。

### 2. QRS 指标解释

QRS 沿用 RSRS/阻力支撑相对强度思想：在滚动窗口内回归 `high = alpha + beta * low + epsilon`，将 beta 进行滚动 z-score 标准化，并使用 R² 对趋势拟合质量进行惩罚。较高 QRS 通常代表趋势状态较强或上行动能较好，较低 QRS 代表趋势弱化或下行动能增强。QRS 应被视为择时因子，而不是完整交易系统。

### 3. 核心功能

- CSV/Excel 数据读取与中英文字段自动识别；
- 5 分钟数据自动聚合为日频 OHLCV；
- QRS、滚动 z-score、调整后 QRS、斜率和分位数计算；
- 滞后一日执行的信号生成；
- 策略与 long-only 基准回测；
- 自动生成 processed data、结果表、图表和研究报告。

### 4. 仓库结构

```text
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── src/
├── scripts/
├── results/
│   ├── figures/
│   ├── tables/
│   └── report.md
└── notebooks/
```

### 5. 快速开始

```bash
pip install -r requirements.txt
python scripts/run_qrs_pipeline.py --input data/raw/qrs_timing_latest.xlsx --contract T
```

### 6. 运行命令

```bash
python scripts/run_qrs_pipeline.py --input data/raw/qrs_timing_latest.xlsx --contract T
python scripts/run_backtest.py --input data/processed/qrs_daily.csv --contract T
```

如果不传入 `--input`，脚本会在 `data/raw/` 和仓库根目录中自动寻找 CSV/Excel 数据文件。

### 7. 输出文件说明

- `data/processed/qrs_daily.csv`：日频 QRS、信号、收益和净值数据；
- `results/tables/backtest_summary.csv`：策略与基准绩效汇总；
- `results/tables/strategy_nav.csv`：策略与基准净值序列；
- `results/figures/`：QRS、净值、回撤和未来收益关系图；
- `[查看完整研究报告](results/report.md)`。

### 8. 防止未来函数说明

所有交易仓位均滞后一日执行，以避免未来函数。QRS 指标、滚动 z-score 和滚动分位数均只使用当日及以前的历史窗口数据。

### 9. 研究报告链接

[查看完整研究报告](results/report.md)

### 10. 免责声明

本项目仅用于量化研究和代码示例，不构成任何投资建议或收益承诺。历史回测结果不代表未来表现。

<a id="en"></a>

## English

Current language: English | [切换到中文](#zh)

---

### 1. Project Introduction

This repository provides a QRS-based timing research framework for Chinese government bond futures. It prioritizes the 10-year CGB futures contract T and keeps interfaces extensible to TL, TF, TS, and other contracts.

### 2. QRS Indicator Explanation

QRS follows the RSRS/resistance-support relative strength idea: regress `high = alpha + beta * low + epsilon` in a rolling window, standardize beta with a rolling z-score, and penalize it by R² as trend-fit quality. Higher QRS usually indicates stronger trend quality or better upside momentum, while lower QRS indicates trend weakening or downside pressure. QRS should be treated as a timing factor, not a complete trading system.

### 3. Key Features

- CSV/Excel loader with automatic Chinese/English field recognition;
- automatic aggregation from 5-minute data to daily OHLCV;
- QRS, rolling z-score, adjusted QRS, slope, and percentile calculation;
- one-day-lagged signal generation;
- strategy and long-only benchmark backtest;
- automatic processed data, result tables, figures, and research report generation.

### 4. Repository Structure

```text
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── src/
├── scripts/
├── results/
│   ├── figures/
│   ├── tables/
│   └── report.md
└── notebooks/
```

### 5. Quick Start

```bash
pip install -r requirements.txt
python scripts/run_qrs_pipeline.py --input data/raw/qrs_timing_latest.xlsx --contract T
```

### 6. Example Commands

```bash
python scripts/run_qrs_pipeline.py --input data/raw/qrs_timing_latest.xlsx --contract T
python scripts/run_backtest.py --input data/processed/qrs_daily.csv --contract T
```

If `--input` is omitted, the script searches `data/raw/` and the repository root for CSV/Excel files.

### 7. Output Files

- `data/processed/qrs_daily.csv`: daily QRS, signal, return, and NAV data;
- `results/tables/backtest_summary.csv`: performance summary for the strategy and benchmark;
- `results/tables/strategy_nav.csv`: strategy and benchmark NAV series;
- `results/figures/`: QRS, NAV, drawdown, and future-return figures;
- `[Read the full research report](results/report.md)`.

### 8. Look-Ahead Bias Control

All trading positions are lagged by one trading day to avoid look-ahead bias. QRS, rolling z-score, and rolling percentile use only current and historical window data.

### 9. Research Report Link

[Read the full research report](results/report.md)

### 10. Disclaimer

This project is for quantitative research and code demonstration only. It does not constitute investment advice or any return guarantee. Historical backtest results do not indicate future performance.
