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

### QRS 因子构建逻辑

#### 1. 截面/局部回归思想

在一个滚动窗口内，将最高价 high 视为阶段性阻力，将最低价 low 视为阶段性支撑，建立局部线性回归：

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t, \quad t \in \{1,2,\ldots,N\}
$$

其中，斜率 $\beta$ 用于衡量支撑与阻力的相对强度。直观上，若低点抬升时高点扩张更充分，回归斜率会更高，说明价格区间上沿的扩张能力更强；反之，若高点对低点抬升反应不足，则趋势质量下降。

| 方向 | 解释 |
| --- | --- |
| $\beta$ 越大 | 价格上沿相对低点扩张更明显，趋势强度更高，偏多信号更强 |
| $\beta$ 越小 | 价格上行动能弱化，趋势质量下降，偏空或防御信号更强 |

#### 2. 降噪与标准化处理

为解决不同时间段 $\beta$ 的量纲差异，并降低噪声和无效拟合影响，引入标准化信号项与 $R^2$ 归一化惩罚项。

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

| 变量 | 含义 | 当前代码对应 |
| --- | --- | --- |
| $\beta$ | 滚动窗口内 high 对 low 回归得到的斜率 | `qrs_raw` |
| $R^2$ | 回归拟合优度 | `qrs_r2` |
| $M$ | 标准化窗口 | `zscore_window` |
| $n$ | 惩罚项指数，基准值通常取 2 | `r2_power` |
| $RSP$ | 经过标准化和拟合优度修正后的 QRS / RSP 信号 | `qrs_adjusted` |

代码一致性说明：当前 `src/qrs_calculator.py` 默认计算 `qrs_adjusted = qrs_zscore * (R^2)^n`，即未开启均值归一化惩罚项；当 `normalize_penalty=True` 时，才使用上式中的 `Mean((R^2)^n, M)` 归一化。当前 `scripts/run_qrs_pipeline.py` 默认交易信号列为 `qrs_zscore`，`qrs_adjusted` 作为增强版 QRS / RSP 研究字段输出。

#### 3. 双周期共振状态机

为降低日内或短周期信号的噪声，策略可以将 QRS / RSP 因子与日频均线趋势过滤结合，形成状态机映射。

- 做多信号：$RSP > S$ 且 $Trend_{up} = True$，仓位 $Pos = 1$；
- 做空或防御信号：$RSP < -S$ 且 $Trend_{down} = True$，仓位 $Pos = -1$ 或 $0$；
- 持仓维持：不满足上述条件时，维持上一期仓位。

其中，$S$ 为触发阈值；$Trend$ 可由日频均线比较、均线交叉或价格与均线关系判断。当前模块化主 pipeline 实现为日频 long / cash 策略：当 `qrs_zscore > 0.7` 时进入多头，当 `qrs_zscore < -0.7` 时进入防御仓位 $Pos=0$，中性区域维持上一期原始仓位，最终交易仓位再滞后一日执行。$Pos=-1$ 属于可扩展的 long-short 设计，当前默认回测未启用。

### 参数搜索空间

| 参数模块 | 参数名称 | 物理意义与逻辑设定 | 搜索空间 / 取值范围 |
| --- | --- | --- | --- |
| 信号触发 | 触发阈值 $S$ | 衡量 RSP 因子做多 / 做空信号的临界权值；当前 pipeline 映射为 `long_threshold` 与 `exit_threshold` | 例如：0.1 至 0.5，步长 0.1；当前默认 long/cash 阈值为 0.7 / -0.7 |
| 趋势过滤 | 过滤方法 `trend_method` | 判定日频主趋势方向的核心机制；当前模块化 pipeline 暂未默认启用趋势过滤 | `ma_compare`：均线比较；`ma_cross`：均线交叉；`price_compare`：价格均线比较 |
| 均线周期 | 均线长度 `ma_len_days` | 设定日频趋势跟踪的敏锐度，仅适用于均线比较与价格均线比较 | 例如：3 日至 10 日，步长 1 日 |
| 均线周期 | 均线滞后期 `compare_lag_days` | 平滑短期波动，规避频繁伪信号，仅适用于均线比较 | 例如：1 日至 5 日，步长 1 日 |
| 均线周期 | 长短均线窗口 `ma_short`, `ma_long` | 捕捉长短周期的动能共振交叉点，仅适用于均线交叉 | 短期：3、5、7；长期：10、15、20 |

该搜索空间来自原始研究脚本中的趋势过滤和阈值设计思路。当前仓库的可复现实证输出未重新进行网格搜索，因此本文不会将上述搜索空间表述为已优化参数结果，也不会据此伪造回测绩效。

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

### QRS Factor Construction

#### 1. Local regression

Within a rolling window, the high price is treated as a local resistance level and the low price is treated as a local support level. The factor starts from the local linear regression:

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t, \quad t \in \{1,2,\ldots,N\}
$$

The slope $\beta$ measures the relative relationship between resistance and support levels. A larger $\beta$ indicates stronger upside expansion and better trend quality, while a smaller $\beta$ indicates weaker trend quality or a more defensive regime.

| Direction | Interpretation |
| --- | --- |
| Larger $\beta$ | Stronger expansion of the upper price range relative to lows, implying stronger trend quality and a more bullish signal |
| Smaller $\beta$ | Weaker upside momentum and deteriorating trend quality, implying a defensive or bearish signal |

#### 2. Standardization and penalty adjustment

To remove scale differences across time and reduce noisy or weak regressions, the slope is standardized and adjusted by a mean-normalized $R^2$ penalty term.

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

| Variable | Meaning | Current Code Mapping |
| --- | --- | --- |
| $\beta$ | Rolling regression slope of high on low | `qrs_raw` |
| $R^2$ | Regression goodness of fit | `qrs_r2` |
| $M$ | Standardization window | `zscore_window` |
| $n$ | Penalty exponent, usually 2 as a baseline | `r2_power` |
| $RSP$ | Standardized and fit-quality-adjusted QRS / RSP signal | `qrs_adjusted` |

Implementation consistency note: `src/qrs_calculator.py` currently computes `qrs_adjusted = qrs_zscore * (R^2)^n` by default, without mean-normalizing the penalty. When `normalize_penalty=True` is enabled, the implementation uses the `Mean((R^2)^n, M)` denominator shown above. The default trading signal in `scripts/run_qrs_pipeline.py` currently uses `qrs_zscore`, while `qrs_adjusted` is exported as the enhanced QRS / RSP field for research extensions.

#### 3. Dual-horizon regime filter

To reduce intraday or short-horizon noise, the QRS / RSP factor can be combined with a daily moving-average trend filter as a regime-state machine.

- Long signal: $RSP > S$ and $Trend_{up} = True$, position $Pos = 1$;
- Defensive / short signal: $RSP < -S$ and $Trend_{down} = True$, position $Pos = -1$ or $0$;
- Otherwise: keep previous position.

Here, $S$ is the trigger threshold, and $Trend$ can be defined by daily moving-average comparison, moving-average crossover, or price-vs-moving-average comparison. The current modular main pipeline implements a daily long / cash strategy: it enters long exposure when `qrs_zscore > 0.7`, moves to the defensive state $Pos=0$ when `qrs_zscore < -0.7`, carries the previous raw position in the neutral zone, and then lags the final trading position by one day. $Pos=-1$ is reserved for future long-short extension and is not enabled in the default backtest.

### Parameter Search Space

| Parameter Module | Parameter Name | Economic / Strategy Meaning | Search Space / Candidate Range |
| --- | --- | --- | --- |
| Signal Trigger | Threshold $S$ | Critical threshold for long / short QRS signals; current pipeline maps this to `long_threshold` and `exit_threshold` | Example: 0.1 to 0.5, step 0.1; current long/cash defaults are 0.7 / -0.7 |
| Trend Filter | `trend_method` | Core mechanism for identifying the daily trend direction; not enabled by default in the current modular pipeline | `ma_compare`: MA comparison; `ma_cross`: MA crossover; `price_compare`: price-MA comparison |
| Moving Average Window | `ma_len_days` | Sensitivity of daily trend tracking, used for MA comparison and price-MA comparison | Example: 3 to 10 days, step 1 day |
| Moving Average Window | `compare_lag_days` | Smooths short-term noise and reduces frequent false signals, used for MA comparison | Example: 1 to 5 days, step 1 day |
| Moving Average Window | `ma_short`, `ma_long` | Captures momentum resonance between short-term and long-term moving averages, used for MA crossover | Short: 3, 5, 7; Long: 10, 15, 20 |

This search space follows the threshold and trend-filter design in the original research script. The reproducible outputs in the current repository did not rerun a full grid search, so these ranges are documented as candidate research settings rather than optimized performance results.

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
