# 基于 QRS 的中国国债期货择时框架 | QRS-Based Timing Strategy for Chinese Government Bond Futures

<p align="center">
  <a href="#zh"><img src="https://img.shields.io/badge/LANGUAGE-%E4%B8%AD%E6%96%87-E84D3D?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE 中文"></a>
  <a href="#en"><img src="https://img.shields.io/badge/LANGUAGE-ENGLISH-2F73C9?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE ENGLISH"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Asset-CGB%20Futures-F2C94C?style=for-the-badge" alt="CGB Futures">
  <img src="https://img.shields.io/badge/Strategy-Intraday%20QRS%20Timing-7AC943?style=for-the-badge" alt="Intraday QRS Timing">
</p>

<a id="zh"></a>

## 简体中文

当前语言：中文 | [Switch to English](#en)

---

## 1. 项目简介

本项目是基于 **QRS（Quantified Resistance/Support）** 指标的中国国债期货择时研究框架。

- **核心策略**：当前主策略为 `intraday` 模式。
- **数据基础**：使用 5 分钟级别的高频 OHLC 数据计算 QRS 因子。
- **技术栈**：结合日频趋势过滤、阈值触发信号、状态机仓位管理及自动化的参数网格搜索。
- **研究对象**：重点针对国债期货 T（10年期）、TL（30年期）等活跃合约。
- **免责声明**：本项目仅作为量化研究框架展示，不构成任何投资建议。

## 2. 核心模型逻辑

### 2.1 QRS 因子构建

QRS 类指标源自对 RSRS 指标的改进，核心思想是通过价格区间中的支撑与阻力关系来刻画趋势的“纯度”和“质量”。在滚动窗口 $N$ 内，对 5 分钟 Bar 的最高价和最低价进行局部线性回归：

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t
$$

- **$\beta$ (斜率)**：反映了支撑与阻力关系的动态变化。$\beta$ 越大，表示价格上沿相对于低点的扩张越明显，上行趋势质量更强。
- **拟合优度 $R^2$**：用于衡量趋势拟合的可靠性。

### 2.2 标准化与惩罚项

为消除不同市场环境下 $\beta$ 的量纲差异，并过滤低拟合质量下的噪声信号，我们对 $\beta$ 进行滚动 Z-score 标准化，并引入 $R^2$ 的幂函数作为惩罚项：

$$
Signal_t = zscore(\beta_t, M) = \frac{\beta_t - \mu_{\beta,t}}{\sigma_{\beta,t}}
$$

$$
Penalty_t = (R_t^2)^n
$$

$$
QRS_t = Signal_t \times Penalty_t
$$

本项目在 `intraday` 模式下默认使用该调整后的 QRS 指标作为核心择时信号。

### 2.3 趋势过滤与状态机

为了控制高频交易的过激行为，本项目引入了日频级别的趋势过滤机制：
1. **跨周期映射**：从 5 分钟 Close 聚合出日频 Close，并计算均线或价格趋势。
2. **趋势对齐**：将日频趋势状态映射回当天的所有 5 分钟 Bar。
3. **状态机仓位**：
   $$
   Pos_t =
   \begin{cases}
   1, & QRS_t > S \text{ and } Trend_{up,t} = True \\
   -1, & QRS_t < -S \text{ and } Trend_{down,t} = True \\
   Pos_{t-1}, & \text{otherwise}
   \end{cases}
   $$

### 3. 策略模式

| 模式 | 数据频率 | 核心逻辑 | 用途 |
| --- | --- | --- | --- |
| `intraday` | 5 分钟 | 5min QRS + 日频趋势过滤 + Long/Short 状态机 + 可选网格搜索 | **主策略** |
| `daily_baseline` | 日频 | 日频 QRS + Long/Cash 策略 | 对照 Baseline |

## 4. 参数搜索空间

| 参数模块 | 参数名称 | 作用 | 默认搜索空间 |
| --- | --- | --- | --- |
| QRS 构建 | $N$ | 回归窗口长度 | 16 |
| QRS 构建 | $M$ | $\beta$ 标准化窗口 | 600 |
| QRS 构建 | $n$ | $R^2$ 惩罚项指数 | 2.0 |
| 信号触发 | $S$ | 多空信号阈值 | 0.2, 0.3, 0.4, 0.5, 0.6, 0.7 |
| 趋势过滤 | `trend_method` | 趋势判断方式 | `ma_compare`, `ma_cross`, `price_compare` |
| 趋势过滤 | `ma_len_days` | 日频均线长度 | 3, 5, 10, 20 |
| 趋势过滤 | `compare_lag_days`| 均线滞后期 | 1, 2, 3 |

## 5. 结果展示

以下是基于最新运行结果的绩效统计（样本区间：2024-01-02 至 2026-04-24）：

### 5.1 绩效汇总

| 指标 | QRS Strategy (主策略) | Long-only Benchmark |
| --- | ---: | ---: |
| 累计收益 | 31.18% | 5.63% |
| 年化收益 | 13.06% | 2.66% |
| 年化波动率 | 2.63% | 2.63% |
| 夏普比率 | 4.9656 | 1.0112 |
| 最大回撤 | -0.97% | -2.27% |
| Calmar Ratio | 13.4047 | 1.1721 |
| 胜率 | 52.76% | 50.73% |
| 换手次数 | 379 | 0 |

### 5.2 最佳参数组合

| 参数 | 优化结果 |
| --- | --- |
| 触发阈值 $S$ | 0.2 |
| 趋势过滤方法 | `price_compare` |
| 日频均线长度 | 3 |
| 允许做空 | True |

## 6. 图表展示

### 6.1 因子与价格叠加图
> 展示 QRS 指标与期货价格的动态对应关系。
![QRS Price Overlay](results/figures/qrs_price_overlay.png)

### 6.2 策略净值曲线对比
> 策略净值 vs 基准净值 vs 超额净值。
![Strategy NAV](results/figures/nav_comparison.png)

### 6.3 回撤分析图
> 策略在回测区间内的回撤分布。
![Drawdown](results/figures/drawdown.png)

### 6.4 最佳参数仓位图
> 展示最优参数组合下的持仓状态分布。
![Best Strategy Position](results/figures/best_strategy_position.png)

### 6.5 因子择时能力分析
> 展示 QRS 因子在不同分位点下的预测能力。
![QRS Future Return](results/figures/qrs_future_return.png)

## 7. 快速开始

### 7.1 安装环境
```bash
git clone https://github.com/ericxuzhesheng/QRS-Based-Timing-Strategy-for-Chinese-Government-Bond-Futures.git
cd QRS-Based-Timing-Strategy-for-Chinese-Government-Bond-Futures
pip install -r requirements.txt
```

### 7.2 运行 Pipeline
```bash
# 运行主管线：包含 QRS 计算、网格搜索、回测及报告生成
python scripts/run_qrs_pipeline.py --mode intraday --run-grid-search
```

---

<a id="en"></a>

## English

Current language: English | [切换到中文](#zh)

---

## 1. Project Overview

This project provides a research framework for **QRS (Quantified Resistance/Support)** based timing strategies in the Chinese government bond futures market.

- **Main Strategy**: The current primary mode is `intraday`.
- **Data Foundation**: Computes QRS factors using 5-minute high-frequency OHLC data.
- **Features**: Includes daily trend filtering, threshold-based signals, state-machine position management, and automated grid search optimization.
- **Assets**: Targeted at active contracts like T (10-year) and TL (30-year).
- **Disclaimer**: This is for quantitative research only and does not constitute investment advice.

## 2. Core Model Logic

### 2.1 QRS Factor Construction

QRS indicators, improved from the RSRS concept, describe trend "purity" and quality by examining the resistance-support relationship within a price range. Over a rolling window $N$, a local linear regression is performed on 5-minute OHLC bars:

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t
$$

- **$\beta$ (Slope)**: Reflects the dynamics of resistance and support. A larger $\beta$ indicates that the upper price boundary is expanding significantly relative to the low, representing stronger trend quality.
- **$R^2$ (R-Squared)**: Measures the reliability of the trend fitting.

### 2.2 Standardization and Penalty

To eliminate the scale differences of $\beta$ across different market environments and filter noisy signals during poor fitting, we apply a rolling Z-score to $\beta$ and introduce a power function of $R^2$ as a penalty term:

$$
Signal_t = zscore(\beta_t, M) = \frac{\beta_t - \mu_{\beta,t}}{\sigma_{\beta,t}}
$$

$$
Penalty_t = (R_t^2)^n
$$

$$
QRS_t = Signal_t \times Penalty_t
$$

The `intraday` mode uses this adjusted QRS indicator as the core timing signal.

### 2.3 Trend Filter and State Machine

A daily trend filter is implemented to mitigate excessive high-frequency trading:
1. **Cross-period Mapping**: Daily close prices are aggregated from 5-minute bars to compute moving averages or price trends.
2. **Alignment**: Daily trend states are mapped back to every 5-minute bar within that day.
3. **Position Rule**:
   $$
   Pos_t =
   \begin{cases}
   1, & QRS_t > S \text{ and } Trend_{up,t} = True \\
   -1, & QRS_t < -S \text{ and } Trend_{down,t} = True \\
   Pos_{t-1}, & \text{otherwise}
   \end{cases}
   $$

## 3. Strategy Modes

| Mode | Frequency | Core Logic | Purpose |
| --- | --- | --- | --- |
| `intraday` | 5-Minute | 5min QRS + Daily Trend Filter + Long/Short State Machine + Grid Search | **Main Strategy** |
| `daily_baseline` | Daily | Daily QRS + Long/Cash strategy | Benchmark Baseline |

## 4. Parameter Search Space

| Module | Parameter | Description | Default Search Space |
| --- | --- | --- | --- |
| QRS Construction | $N$ | Regression window length | 16 |
| QRS Construction | $M$ | $\beta$ standardization window | 600 |
| QRS Construction | $n$ | $R^2$ penalty exponent | 2.0 |
| Signal Trigger | $S$ | Signal threshold | 0.2, 0.3, 0.4, 0.5, 0.6, 0.7 |
| Trend Filter | `trend_method` | Trend identification method | `ma_compare`, `ma_cross`, `price_compare` |
| Trend Filter | `ma_len_days` | Daily MA length | 3, 5, 10, 20 |
| Trend Filter | `compare_lag_days`| MA comparison lag | 1, 2, 3 |

## 5. Results and Performance

Current performance metrics based on the latest sample period (2024-01-02 to 2026-04-24):

### 5.1 Performance Summary

| Metric | QRS Strategy (Main) | Long-only Benchmark |
| --- | ---: | ---: |
| Cumulative Return | 31.18% | 5.63% |
| Annualized Return | 13.06% | 2.66% |
| Annualized Volatility | 2.63% | 2.63% |
| Sharpe Ratio | 4.9656 | 1.0112 |
| Max Drawdown | -0.97% | -2.27% |
| Calmar Ratio | 13.4047 | 1.1721 |
| Win Rate | 52.76% | 50.73% |
| Turnover Count | 379 | 0 |

### 5.2 Best Parameter Set

| Parameter | Optimized Value |
| --- | --- |
| Threshold $S$ | 0.2 |
| Trend Method | `price_compare` |
| Daily MA Length | 3 |
| Allow Short | True |

## 6. Visualization

### 6.1 Factor & Price Overlay
![QRS Price Overlay](results/figures/qrs_price_overlay.png)

### 6.2 Strategy NAV Comparison
![Strategy NAV](results/figures/nav_comparison.png)

### 6.3 Drawdown Analysis
![Drawdown](results/figures/drawdown.png)

### 6.4 Best Strategy Position
![Best Strategy Position](results/figures/best_strategy_position.png)

### 6.5 Timing Coefficient (QRS Future Return)
![QRS Future Return](results/figures/qrs_future_return.png)

## 7. Quick Start

### 7.1 Installation
```bash
git clone https://github.com/ericxuzhesheng/QRS-Based-Timing-Strategy-for-Chinese-Government-Bond-Futures.git
cd QRS-Based-Timing-Strategy-for-Chinese-Government-Bond-Futures
pip install -r requirements.txt
```

### 7.2 Run Pipeline
```bash
# Main pipeline: includes QRS calculation, grid search, backtesting, and report generation
python scripts/run_qrs_pipeline.py --mode intraday --run-grid-search
```
