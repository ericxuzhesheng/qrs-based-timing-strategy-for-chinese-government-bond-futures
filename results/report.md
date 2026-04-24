# 基于 QRS 的中国国债期货择时研究报告 | QRS-Based Timing Strategy Report for Chinese Government Bond Futures

<p align="center">
  <a href="#zh"><img src="https://img.shields.io/badge/LANGUAGE-%E4%B8%AD%E6%96%87-E84D3D?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE 中文"></a>
  <a href="#en"><img src="https://img.shields.io/badge/LANGUAGE-ENGLISH-2F73C9?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE ENGLISH"></a>
</p>

<a id="zh"></a>

## 简体中文

当前语言：中文 | [Switch to English](#en)

---

### 1. 项目概述

本报告展示基于 QRS 指标的中国国债期货择时研究流程。当前运行合约：`T`；输入数据：`10年国债期货_5min_3年.xlsx`；样本区间：`2022-12-16 至 2026-04-24`。

### 2. 研究动机

国债期货价格受到利率预期、资金面、风险偏好和政策变化影响。QRS/RSRS 类指标通过价格区间中的阻力与支撑关系刻画趋势质量，可作为日频择时因子。

### 3. QRS 指标解释

本项目沿用原始 `qrs_timing.py` 的核心公式：在滚动窗口内回归 `high = alpha + beta * low + epsilon`，将斜率 beta 进行滚动 z-score 标准化，并使用 R² 的幂作为趋势拟合质量惩罚项。较高 QRS 通常代表趋势状态较强或上行动能较好，较低 QRS 代表趋势弱化或下行动能增强。QRS 是择时因子，不是完整交易系统。

### 4. 数据与预处理

数据读取支持 CSV 和 Excel，自动识别日期、OHLC、成交量和持仓量字段。若输入为 5 分钟数据，pipeline 会聚合为日频 OHLCV 后再计算日频 QRS 与回测结果。

### 5. 方法论

- 滚动窗口：`18`
- z-score 窗口：`120`
- R² 惩罚幂：`2.0`
- 信号列：`qrs_zscore`

### 6. 信号设计

当 `qrs_zscore > 0.7` 时，原始仓位设为 1；当 `qrs_zscore < -0.7` 时，原始仓位设为 0；中性区域维持前一日原始仓位。

### 7. 防止未来函数

所有交易仓位均滞后一日执行，以避免未来函数。QRS 指标、滚动 z-score 与滚动分位数均只使用当日及以前信息。

### 8. 回测框架

回测采用 close-to-close 日频收益；基准为 long-only 持有；策略收益为滞后一日后的仓位乘以当日收益。

### 9. 结果展示

| portfolio           | cumulative_return   | annualized_return   | annualized_volatility   |   sharpe_ratio | max_drawdown   |   calmar_ratio | win_rate   |   turnover |
|:--------------------|:--------------------|:--------------------|:------------------------|---------------:|:---------------|---------------:|:-----------|-----------:|
| QRS Strategy        | 0.88%               | 0.27%               | 1.59%                   |         0.1716 | -2.34%         |         0.117  | 54.00%     |         25 |
| Long-only Benchmark | 8.83%               | 2.67%               | 2.42%                   |         1.1027 | -2.25%         |         1.1893 | 56.55%     |          0 |

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

This report presents a QRS-based timing research workflow for Chinese government bond futures. Current contract: `T`; input data: `10年国债期货_5min_3年.xlsx`; sample period: `2022-12-16 to 2026-04-24`.

### 2. Research Motivation

Chinese government bond futures are driven by rate expectations, liquidity, risk appetite, and policy changes. QRS/RSRS-style indicators describe trend quality through resistance-support relationships and can be used as daily timing factors.

### 3. QRS Indicator Interpretation

This project preserves the core formula from the original `qrs_timing.py`: regress `high = alpha + beta * low + epsilon` in a rolling window, standardize beta with a rolling z-score, and penalize it by a power of R². Higher QRS indicates stronger trend quality or better upside momentum, while lower QRS indicates weaker trends or downside pressure. QRS should be treated as a timing factor, not a complete trading system.

### 4. Data and Preprocessing

The loader supports CSV and Excel files and automatically detects date, OHLC, volume, and open-interest fields. If the input is 5-minute data, the pipeline aggregates it to daily OHLCV before computing daily QRS and backtest results.

### 5. Methodology

- Rolling window: `18`
- z-score window: `120`
- R² penalty power: `2.0`
- Signal column: `qrs_zscore`

### 6. Signal Design

When `qrs_zscore > 0.7`, the raw position is set to 1. When `qrs_zscore < -0.7`, the raw position is set to 0. The neutral zone carries the previous raw position.

### 7. Look-Ahead Bias Control

All trading positions are lagged by one trading day to avoid look-ahead bias. QRS, rolling z-score, and rolling percentile use only current and historical information.

### 8. Backtest Framework

The backtest uses daily close-to-close returns. The benchmark is long-only. Strategy return equals the one-day-lagged position multiplied by daily return.

### 9. Results and Outputs

| portfolio           | cumulative_return   | annualized_return   | annualized_volatility   |   sharpe_ratio | max_drawdown   |   calmar_ratio | win_rate   |   turnover |
|:--------------------|:--------------------|:--------------------|:------------------------|---------------:|:---------------|---------------:|:-----------|-----------:|
| QRS Strategy        | 0.88%               | 0.27%               | 1.59%                   |         0.1716 | -2.34%         |         0.117  | 54.00%     |         25 |
| Long-only Benchmark | 8.83%               | 2.67%               | 2.42%                   |         1.1027 | -2.25%         |         1.1893 | 56.55%     |          0 |

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
