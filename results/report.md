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

本报告展示基于 QRS 指标的中国国债期货择时研究流程。当前运行模式：`intraday_v4`；当前运行合约：`T`；输入数据：`10年国债期货_5min_3年.xlsx`；样本区间：`2025-01-02 09:35:00 至 2026-04-24 11:30:00`。

### 2. 当前模式说明

仓库包含两个模式：

- `daily_baseline`：先将 5 分钟数据聚合为日频，再计算 QRS 和日频 long/cash 回测，适合作为稳健 baseline，但不等价于旧 v4。
- `intraday_v4`：默认主策略，复现旧 v4 的核心逻辑，包括 5 分钟 QRS、日频趋势过滤映射回 5 分钟、long/short 状态机、可选 grid search。

本次结果来自 `intraday_v4`，数据频率为 `5-minute intraday`，`allow_short=True`，`periods_per_year=13608`，是否运行 grid search：`True`。

### 3. QRS 指标解释

QRS/RSRS 类指标通过价格区间中的阻力与支撑关系刻画趋势质量。本项目 v4 兼容模式在 5 分钟 OHLC 上回归 `high = alpha + beta * low + epsilon`，将 beta 进行滚动 z-score 标准化，并使用 $R^2$ 的幂作为趋势拟合质量惩罚项。

### 4. QRS 因子构建逻辑

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t, \quad t \in \{1,2,\ldots,N\}
$$

$$
qrs = zscore(\beta, M) \times (R^2)^n
$$

当前 v4 参数：`N=16`，`M=600`，`n=2.0`。当 `normalize_penalty=True` 时，可进一步使用滚动均值归一化惩罚项；本次默认保持 v4 主流程的未归一化惩罚项。

### 5. 信号设计与趋势过滤

v4 兼容状态机规则：

- 做多：`qrs > +S` 且日频趋势向上，仓位设为 1；
- 做空/防御：`qrs < -S` 且日频趋势向下，`allow_short=True` 时仓位设为 -1，否则设为 0；
- 其他：维持上一根 5 分钟 bar 的原始仓位。

趋势过滤从 5 分钟 close 聚合为日频 close 后计算，再映射回 5 分钟 bar。同一天所有 5 分钟 bar 共用当天趋势条件。本次趋势方法：`price_compare`。

### 6. 防止未来函数

所有交易仓位均滞后一根 5 分钟 bar 执行，以避免未来函数。具体实现为 `position = raw_position.shift(1).fillna(0)`，策略收益使用该滞后仓位乘以当前 bar 收益。

### 7. 参数搜索空间与最佳参数

默认搜索空间包括 `S=[0.2,0.3,0.4,0.5,0.6,0.7]`、`trend_method=[ma_compare, ma_cross, price_compare]`、`ma_len_days=[3,5,10,20]`、`compare_lag_days=[1,2,3]`、`ma_short=[3,5,10]`、`ma_long=[10,20,30]`。

本次使用参数：

```json
{
  "S": 0.2,
  "trend_method": "price_compare",
  "ma_len_days": 3.0,
  "compare_lag_days": null,
  "ma_short": null,
  "ma_long": null,
  "cumulative_return": 0.15402056132022213,
  "annualized_return": 0.12225561834188291,
  "annualized_volatility": 0.024072513170350657,
  "sharpe_ratio": 5.07863958684884,
  "max_drawdown": -0.009742789231778737,
  "calmar_ratio": 12.548318087710777,
  "win_rate": 0.5275846768229552,
  "turnover": 217.0,
  "grid_search": true
}
```

### 8. 回测结果

| Metric                | QRS Strategy   | Long-only Benchmark   |
|:----------------------|:---------------|:----------------------|
| Cumulative Return     | 15.40%         | -0.16%                |
| Annualized Return     | 12.23%         | -0.11%                |
| Annualized Volatility | 2.41%          | 2.43%                 |
| Sharpe Ratio          | 5.0786         | -0.0441               |
| Max Drawdown          | -0.97%         | -2.27%                |
| Calmar Ratio          | 12.5483        | -0.0472               |
| Win Rate              | 52.76%         | 50.03%                |
| Turnover              | 217.0000       | 0.0000                |

### 9. Debug 对比信息

| Metric                  | Value               |
|:------------------------|:--------------------|
| sample_start            | 2025-01-02 09:35:00 |
| sample_end              | 2026-04-24 11:30:00 |
| bar_count               | 15983               |
| average_position        | 0.0810              |
| long_ratio              | 53.73%              |
| short_ratio             | 45.63%              |
| cash_ratio              | 0.64%               |
| turnover_count          | 217.0000            |
| benchmark_annual_return | -0.11%              |
| strategy_annual_return  | 12.23%              |
| strategy_sharpe         | 5.0786              |
| max_drawdown            | -0.97%              |

### 10. 图表

![QRS Price Overlay](figures/qrs_price_overlay.png)

![Strategy NAV](figures/nav_comparison.png)

![Drawdown](figures/drawdown.png)

![Best Strategy Position](figures/best_strategy_position.png)

![QRS Future Return](figures/qrs_future_return.png)

### 11. 局限性

本研究未考虑手续费、滑点、保证金占用、展期规则和真实成交约束。结果依赖输入数据质量与样本区间，不构成投资建议。

### 12. 免责声明

本项目仅用于量化研究与代码示例，不构成任何投资建议或收益承诺。

<a id="en"></a>

## English

Current language: English | [切换到中文](#zh)

---

### 1. Project Overview

This report presents a QRS-based timing workflow for Chinese government bond futures. Current mode: `intraday_v4`; contract: `T`; input data: `10年国债期货_5min_3年.xlsx`; sample period: `2025-01-02 09:35:00 to 2026-04-24 11:30:00`.

### 2. Mode Description

The repository contains two modes:

- `daily_baseline`: aggregates 5-minute data to daily bars before QRS calculation and daily long/cash backtesting. It is a robust baseline but is not equivalent to the old v4 strategy.
- `intraday_v4`: the default main strategy, restoring the old v4 core logic: 5-minute QRS, daily trend filter mapped back to intraday bars, long/short state machine, and optional grid search.

This run uses `intraday_v4`, data frequency `5-minute intraday`, `allow_short=True`, `periods_per_year=13608`, and grid search status `True`.

### 3. QRS Indicator Interpretation

QRS/RSRS-style indicators describe trend quality through resistance-support relationships. The v4-compatible mode regresses `high = alpha + beta * low + epsilon` on 5-minute OHLC bars, standardizes beta with a rolling z-score, and penalizes it by a power of $R^2$.

### 4. QRS Factor Construction

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t, \quad t \in \{1,2,\ldots,N\}
$$

$$
qrs = zscore(\beta, M) \times (R^2)^n
$$

Current v4 parameters: `N=16`, `M=600`, `n=2.0`. When `normalize_penalty=True`, the penalty can be normalized by its rolling mean; this run keeps the original v4 default without mean-normalizing the penalty.

### 5. Signal Design and Trend Filter

The v4-compatible state machine is:

- Long: `qrs > +S` and the daily trend is up, position becomes 1;
- Short / defensive: `qrs < -S` and the daily trend is down, position becomes -1 if `allow_short=True`, otherwise 0;
- Otherwise: carry the previous raw position.

The trend filter is computed from daily closes aggregated from 5-minute closes, then mapped back to every 5-minute bar. All bars in the same day share the same daily trend condition. Trend method for this run: `price_compare`.

### 6. Look-Ahead Bias Control

All trading positions are lagged by one 5-minute bar to avoid look-ahead bias. The implementation uses `position = raw_position.shift(1).fillna(0)` and multiplies that lagged position by the current bar return.

### 7. Parameter Search Space and Best Parameters

The default search space includes `S=[0.2,0.3,0.4,0.5,0.6,0.7]`, `trend_method=[ma_compare, ma_cross, price_compare]`, `ma_len_days=[3,5,10,20]`, `compare_lag_days=[1,2,3]`, `ma_short=[3,5,10]`, and `ma_long=[10,20,30]`.

Parameters used in this run:

```json
{
  "S": 0.2,
  "trend_method": "price_compare",
  "ma_len_days": 3.0,
  "compare_lag_days": null,
  "ma_short": null,
  "ma_long": null,
  "cumulative_return": 0.15402056132022213,
  "annualized_return": 0.12225561834188291,
  "annualized_volatility": 0.024072513170350657,
  "sharpe_ratio": 5.07863958684884,
  "max_drawdown": -0.009742789231778737,
  "calmar_ratio": 12.548318087710777,
  "win_rate": 0.5275846768229552,
  "turnover": 217.0,
  "grid_search": true
}
```

### 8. Backtest Results

| Metric                | QRS Strategy   | Long-only Benchmark   |
|:----------------------|:---------------|:----------------------|
| Cumulative Return     | 15.40%         | -0.16%                |
| Annualized Return     | 12.23%         | -0.11%                |
| Annualized Volatility | 2.41%          | 2.43%                 |
| Sharpe Ratio          | 5.0786         | -0.0441               |
| Max Drawdown          | -0.97%         | -2.27%                |
| Calmar Ratio          | 12.5483        | -0.0472               |
| Win Rate              | 52.76%         | 50.03%                |
| Turnover              | 217.0000       | 0.0000                |

### 9. Debug Comparison

| Metric                  | Value               |
|:------------------------|:--------------------|
| sample_start            | 2025-01-02 09:35:00 |
| sample_end              | 2026-04-24 11:30:00 |
| bar_count               | 15983               |
| average_position        | 0.0810              |
| long_ratio              | 53.73%              |
| short_ratio             | 45.63%              |
| cash_ratio              | 0.64%               |
| turnover_count          | 217.0000            |
| benchmark_annual_return | -0.11%              |
| strategy_annual_return  | 12.23%              |
| strategy_sharpe         | 5.0786              |
| max_drawdown            | -0.97%              |

### 10. Figures

![QRS Price Overlay](figures/qrs_price_overlay.png)

![Strategy NAV](figures/nav_comparison.png)

![Drawdown](figures/drawdown.png)

![Best Strategy Position](figures/best_strategy_position.png)

![QRS Future Return](figures/qrs_future_return.png)

### 11. Limitations

The study does not include transaction costs, slippage, margin usage, contract roll rules, or real execution constraints. Results depend on data quality and sample period and are not investment advice.

### 12. Disclaimer

This project is for quantitative research and code demonstration only. It does not constitute investment advice or any return guarantee.
