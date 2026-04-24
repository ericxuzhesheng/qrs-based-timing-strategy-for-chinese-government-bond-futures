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

### QRS 因子构建逻辑

#### 1. 截面/局部回归思想

在一个滚动窗口内，将最高价 high 视为阶段性阻力，将最低价 low 视为阶段性支撑，建立局部线性回归：

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t, \quad t \in \{1,2,\ldots,N\}
$$

其中，斜率 $\beta$ 用于衡量支撑与阻力的相对强度。

- $\beta$ 越大，说明价格上沿相对低点扩张更明显，趋势强度更高，偏多信号更强；
- $\beta$ 越小，说明价格上行动能弱化，趋势质量下降，偏空或防御信号更强。

#### 2. 降噪与标准化处理

为解决不同时间段 $\beta$ 的量纲差异，并降低噪声和无效拟合影响，引入标准化信号项与 $R^2$ 惩罚项。

$$
Signal = zscore(\beta, M) = \frac{\beta - \mu_{\beta}}{\sigma_{\beta}}
$$

$$
Penalty = \frac{(R^2)^n}{Mean((R^2)^n, M)}
$$

$$
RSP = Signal \times Penalty
= zscore(\beta, M) \times \frac{(R^2)^n}{Mean((R^2)^n, M)}
$$

| 变量 | 含义 |
| --- | --- |
| $\beta$ | 滚动窗口内 high 对 low 回归得到的斜率；代码中保存为 `qrs_raw` |
| $R^2$ | 回归拟合优度；代码中保存为 `qrs_r2` |
| $M$ | 标准化窗口；代码参数为 `zscore_window` |
| $n$ | 惩罚项指数，基准值通常取 2；代码参数为 `r2_power` |
| $RSP$ | 经过标准化和拟合优度修正后的 QRS / RSP 信号；代码中对应 `qrs_adjusted` |

当前代码默认计算 `qrs_adjusted = qrs_zscore * (R^2)^n`；若启用 `normalize_penalty=True`，则使用上式中的均值归一化惩罚项。当前默认交易信号使用 `qrs_zscore`，`qrs_adjusted` 作为增强版 QRS / RSP 字段保留用于研究扩展。

#### 3. 双周期共振状态机

为降低日内或短周期信号的噪声，QRS / RSP 因子可以与日频均线趋势过滤结合，形成状态机映射。

- 做多信号：$RSP > S$ 且 $Trend_{up} = True$，仓位 $Pos = 1$；
- 做空或防御信号：$RSP < -S$ 且 $Trend_{down} = True$，仓位 $Pos = -1$ 或 $0$；
- 持仓维持：不满足上述条件时，维持上一期仓位。

其中，$S$ 为触发阈值，$Trend$ 可由日频均线比较、均线交叉或价格与均线关系判断。当前仓库的主 pipeline 实现为日频 long / cash 策略：默认以 `qrs_zscore` 判断入场与防御，防御仓位为 $Pos=0$；$Pos=-1$ 是可扩展的 long-short 设计，并未在当前默认回测中启用。

### 参数搜索空间

| 参数模块 | 参数名称 | 物理意义与逻辑设定 | 搜索空间 / 取值范围 |
| --- | --- | --- | --- |
| 信号触发 | 触发阈值 $S$ | 衡量 RSP 因子做多 / 做空信号的临界权值；当前 pipeline 对应 `long_threshold` 与 `exit_threshold` | 例如：0.1 至 0.5，步长 0.1；当前默认 long/cash 阈值为 0.7 / -0.7 |
| 趋势过滤 | 过滤方法 `trend_method` | 判定日频主趋势方向的核心机制；当前模块化 pipeline 暂未默认启用趋势过滤 | `ma_compare`：均线比较；`ma_cross`：均线交叉；`price_compare`：价格均线比较 |
| 均线周期 | 均线长度 `ma_len_days` | 设定日频趋势跟踪的敏锐度，仅适用于均线比较与价格均线比较 | 例如：3 日至 10 日，步长 1 日 |
| 均线周期 | 均线滞后期 `compare_lag_days` | 平滑短期波动，规避频繁伪信号，仅适用于均线比较 | 例如：1 日至 5 日，步长 1 日 |
| 均线周期 | 长短均线窗口 `ma_short`, `ma_long` | 捕捉长短周期的动能共振交叉点，仅适用于均线交叉 | 短期：3、5、7；长期：10、15、20 |

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

### QRS Factor Construction

#### 1. Local regression

Within a rolling window, the high price is treated as a local resistance level and the low price is treated as a local support level. The factor starts from the local linear regression:

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t, \quad t \in \{1,2,\ldots,N\}
$$

The slope $\beta$ measures the relative relationship between resistance and support levels. A larger $\beta$ indicates stronger upside expansion and better trend quality, while a smaller $\beta$ indicates weaker trend quality or a more defensive regime.

#### 2. Standardization and penalty adjustment

To remove scale differences across time and reduce noisy or weak regressions, the slope is standardized and adjusted by an $R^2$-based penalty term.

$$
Signal = zscore(\beta, M) = \frac{\beta - \mu_{\beta}}{\sigma_{\beta}}
$$

$$
Penalty = \frac{(R^2)^n}{Mean((R^2)^n, M)}
$$

$$
RSP = Signal \times Penalty
= zscore(\beta, M) \times \frac{(R^2)^n}{Mean((R^2)^n, M)}
$$

| Variable | Meaning |
| --- | --- |
| $\beta$ | Rolling regression slope of high on low; stored as `qrs_raw` in code |
| $R^2$ | Regression goodness of fit; stored as `qrs_r2` in code |
| $M$ | Standardization window; code parameter `zscore_window` |
| $n$ | Penalty exponent, usually 2 as a baseline; code parameter `r2_power` |
| $RSP$ | Standardized and fit-quality-adjusted QRS / RSP signal; mapped to `qrs_adjusted` in code |

The current implementation computes `qrs_adjusted = qrs_zscore * (R^2)^n` by default. When `normalize_penalty=True` is enabled, it uses the mean-normalized penalty shown above. The default trading signal currently uses `qrs_zscore`, while `qrs_adjusted` is kept as the enhanced QRS / RSP field for research extensions.

#### 3. Dual-horizon regime filter

To reduce intraday or short-horizon noise, the QRS / RSP factor can be combined with a daily moving-average trend filter as a regime-state machine.

- Long signal: $RSP > S$ and $Trend_{up} = True$, position $Pos = 1$;
- Defensive / short signal: $RSP < -S$ and $Trend_{down} = True$, position $Pos = -1$ or $0$;
- Otherwise: keep previous position.

Here, $S$ is the trigger threshold, and $Trend$ can be defined by daily moving-average comparison, moving-average crossover, or price-vs-moving-average comparison. The current repository's main pipeline implements a daily long / cash strategy: it uses `qrs_zscore` by default for entry and defensive signals, uses $Pos=0$ as the defensive state, and reserves $Pos=-1$ for future long-short extension.

### Parameter Search Space

| Parameter Module | Parameter Name | Economic / Strategy Meaning | Search Space / Candidate Range |
| --- | --- | --- | --- |
| Signal Trigger | Threshold $S$ | Critical threshold for long / short QRS signals; current pipeline maps this to `long_threshold` and `exit_threshold` | Example: 0.1 to 0.5, step 0.1; current long/cash defaults are 0.7 / -0.7 |
| Trend Filter | `trend_method` | Core mechanism for identifying the daily trend direction; not enabled by default in the current modular pipeline | `ma_compare`: MA comparison; `ma_cross`: MA crossover; `price_compare`: price-MA comparison |
| Moving Average Window | `ma_len_days` | Sensitivity of daily trend tracking, used for MA comparison and price-MA comparison | Example: 3 to 10 days, step 1 day |
| Moving Average Window | `compare_lag_days` | Smooths short-term noise and reduces frequent false signals, used for MA comparison | Example: 1 to 5 days, step 1 day |
| Moving Average Window | `ma_short`, `ma_long` | Captures momentum resonance between short-term and long-term moving averages, used for MA crossover | Short: 3, 5, 7; Long: 10, 15, 20 |

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
