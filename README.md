# 基于 QRS 的中国国债期货择时框架 | QRS-Based Timing Strategy for Chinese Government Bond Futures

<p align="center">
  <a href="#zh"><img src="https://img.shields.io/badge/LANGUAGE-%E4%B8%AD%E6%96%87-E84D3D?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE 中文"></a>
  <a href="#en"><img src="https://img.shields.io/badge/LANGUAGE-ENGLISH-2F73C9?style=for-the-badge&labelColor=3B3F47" alt="LANGUAGE ENGLISH"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Asset-CGB%20Futures-F2C94C?style=for-the-badge" alt="CGB Futures">
  <img src="https://img.shields.io/badge/Strategy-Dynamic%20QRS%20Timing-7AC943?style=for-the-badge" alt="Dynamic QRS Timing">
</p>

<a id="zh"></a>

## 简体中文

当前语言：中文 | [Switch to English](#en)

---

## 1. 项目简介

本项目是基于 **QRS（Quantified Resistance/Support）** 指标的中国国债期货择时研究框架。

- **核心策略**：动态参数选择与样本外 Walk-Forward 回测。
- **理论来源**：本项目核心思路参考自中金公司（CICC）量化研究报告 **《金融工程视角下的技术择时艺术》** 以及浙商证券的相关研究。
- **数据基础**：使用 5 分钟级别的高频 OHLC 数据计算 QRS 因子。
- **技术栈**：因子预测能力评价 (IC/Rank IC)、滚动窗口参数优化、动态趋势过滤、状态机仓位管理。
- **研究对象**：重点针对国债期货 T（10年期）、TL（30年期）等活跃合约。
- **免责声明**：本项目仅作为量化研究框架展示，不构成任何投资建议。

## 2. 核心模型逻辑

### 2.1 QRS 因子构建

QRS 类指标源自对 RSRS 指标的改进，核心思想是通过价格区间中的支撑与阻力关系来刻画趋势的“纯度”和“质量”。在滚动窗口 $N$ 内，对 5 分钟 Bar 的最高价和最低价进行局部线性回归：

$$
high_t = \alpha + \beta \cdot low_t + \varepsilon_t
$$

- **$\beta$ (斜率)**：反映了支撑与阻力关系的动态变化。
- **拟合优度 $R^2$**：用于衡量趋势拟合的可靠性。

### 2.2 动态参数优化框架

传统静态 Grid Search 容易陷入过拟合。本项目升级为动态参数选择框架：

1. **因子预测能力评价 (Predictive Power)**：使用 IC、Rank IC 和未来收益分位差 (Future Return Spread) 评价 QRS 因子对未来 $h$ 个 Bar 收益的解释力。
2. **滚动训练窗口 (Rolling Train Window)**：每次取过去 $W_{train}$ 天作为训练集。
3. **两步法参数选择**：
   - 第一步：在训练集内选择 Rank IC 最高的 QRS 因子参数 $(N, M, n)$。
   - 第二步：基于最优因子，选择训练集内 Sharpe Ratio 最高的信号参数 $(S, \text{trend\_method})$。
4. **样本外执行 (Walk-Forward)**：将选出的参数用于下一段 $W_{test}$ 天的样本外区间。

## 3. 策略模式

| 模式 | 命令参数 | 说明 |
| --- | --- | --- |
| `static` | `--mode static` | 传统全样本 Grid Search Baseline (In-sample)。 |
| `dynamic` | `--mode dynamic` | 滚动窗口动态参数选择 + Walk-Forward 样本外回测。 |
| `full` | `--mode full` | 同时运行 Static 与 Dynamic 模式并生成对比报告。 |

## 4. 结果展示 (示例)

### 4.1 Static vs Dynamic 绩效对比 (T 合约)

| 模式 | 年化收益 | 夏普比率 | 最大回撤 | 换手率 |
| --- | ---: | ---: | ---: | ---: |
| Static Baseline | 13.06% | 4.97 | -0.97% | 379 |
| Dynamic WF | 11.24% | 3.85 | -1.25% | 452 |

> 注：Dynamic 模式下参数随市场环境动态调整，虽然回测收益可能略低于全样本最优的 Static 结果，但其样本外表现更具鲁棒性。

### 4.2 动态参数轨迹
![Dynamic Param Timeline](results/figures/dynamic_param_timeline_T.png)

### 4.3 静态与动态净值对比
![Static vs Dynamic NAV](results/figures/static_vs_dynamic_nav_T.png)

## 5. 快速开始

### 5.1 安装环境
```bash
git clone https://github.com/ericxuzhesheng/QRS-Based-Timing-Strategy-for-Chinese-Government-Bond-Futures.git
cd QRS-Based-Timing-Strategy-for-Chinese-Government-Bond-Futures
pip install -r requirements.txt
```

### 5.2 运行 Pipeline
```bash
# 运行完整研究管线 (T 和 TL 合约)
python scripts/run_qrs_pipeline.py --mode full --contract ALL --fast-mode

# 运行完整网格搜索 (计算量较大)
python scripts/run_qrs_pipeline.py --mode full --contract ALL --full-grid
```

## 6. 参考文献 (References)

1. **中金公司**：《金融工程视角下的技术择时艺术》 —— 提供了 QRS 指标的理论原型与参数化择时思路。
2. **浙商证券**：《基于 QRS 因子的双周期共振日内择时与“每日一图”体系更新》 —— 提供了 QRS 在高频场景下的应用参考。

---

<a id="en"></a>

## English

Current language: English | [切换到中文](#zh)

---

## 1. Project Overview

This project provides a research framework for **QRS (Quantified Resistance/Support)** based timing strategies with **Dynamic Parameter Selection** and **Walk-Forward Backtesting**.

- **Core Strategy**: Dynamic parameter optimization based on predictive power.
- **Source**: Inspired by CICC's report ***The Art of Technical Timing from a Financial Engineering Perspective*** and research from Zheshang Securities.
- **Data Foundation**: 5-minute high-frequency OHLC data.
- **Key Features**: Factor predictive evaluation (IC/Rank IC), rolling window optimization, dynamic trend filtering, state-machine position management.

## 2. Core Model Logic

### 2.1 QRS Factor
Local linear regression on 5-minute bars: $high_t = \alpha + \beta \cdot low_t + \varepsilon_t$. The slope $\beta$ represents trend quality, adjusted by $R^2$ penalty.

### 2.2 Dynamic Optimization Framework
1. **Predictive Power Evaluation**: Measures factor effectiveness using IC, Rank IC, and Quantile Spreads.
2. **Two-Step Selection**: 
   - Optimize QRS factor parameters via Rank IC in the training window.
   - Optimize signal parameters via Sharpe Ratio given the selected factor.
3. **Walk-Forward Execution**: Apply optimized parameters to the subsequent out-of-sample test window.

## 3. Usage Modes

| Mode | Command | Description |
| --- | --- | --- |
| `static` | `--mode static` | Traditional full-sample grid search (In-sample baseline). |
| `dynamic` | `--mode dynamic` | Rolling window dynamic selection + Walk-forward backtest. |
| `full` | `--mode full` | Runs both modes and generates comparative reports. |

## 4. Visualizations

### 4.1 Static vs Dynamic NAV
![Static vs Dynamic NAV](results/figures/static_vs_dynamic_nav_T.png)

### 4.2 Parameter Selection Timeline
![Dynamic Param Timeline](results/figures/dynamic_param_timeline_T.png)

## 5. Quick Start

### 5.1 Installation
```bash
git clone https://github.com/ericxuzhesheng/QRS-Based-Timing-Strategy-for-Chinese-Government-Bond-Futures.git
cd QRS-Based-Timing-Strategy-for-Chinese-Government-Bond-Futures
pip install -r requirements.txt
```

### 5.2 Run Pipeline
```bash
# Run full research pipeline for T and TL contracts
python scripts/run_qrs_pipeline.py --mode full --contract ALL --fast-mode
```
