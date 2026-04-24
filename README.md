# QRS-Based Timing Strategy for Chinese Government Bond Futures

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Asset-CGB%20Futures-gold.svg" alt="Asset">
  <img src="https://img.shields.io/badge/Strategy-Trend%20Timing-green.svg" alt="Strategy">
</p>

本项目提供基于 QRS（Quantified Resistance/Support）指标的中国国债期货择时研究框架。通过 5 分钟高频 OHLC 数据构建 QRS 因子，并结合日频趋势过滤（Trend Filter）与网格搜索（Grid Search）优化，实现在国债期货市场中的多空择时。

---

## 1. 核心模型逻辑

### 1.1 QRS 因子构建
QRS 类指标（源自 RSRS 改进）通过价格区间中的阻力与支撑关系刻画趋势质量：
1. **阻力支撑回归**：在滚动窗口 $N$ 内，对 5 分钟 bar 执行回归：$high_t = \alpha + \beta \cdot low_t + \varepsilon_t$。
2. **标准化**：对斜率 $\beta$ 进行 $M$ 期滚动 Z-Score 处理。
3. **趋势惩罚**：使用回归拟合优度 $R^2$ 的 $n$ 次幂作为惩罚项，抑制震荡市中的假信号。
4. **计算公式**：$qrs = zscore(\beta, M) \times (R^2)^n$。

### 1.2 趋势判断与信号生成
本项目引入了**日频趋势过滤机制**，有效避免了单纯高频信号带来的频繁调仓：
- **趋势判断**：支持均线比较（MA Compare）、均线交叉（MA Cross）和价格均线比较（Price Compare）三种方法。
- **状态机信号**：
  - **做多**：$qrs > +S$ 且日频趋势向上。
  - **做空**：$qrs < -S$ 且日频趋势向下（若允许做空）。
  - **维持**：若信号不触发，则维持上一时刻仓位，减少滑点。
- **未来函数规避**：所有交易信号均滞后一根 5 分钟 bar 执行。

---

## 2. 回测表现 (10年国债期货 T)

基于最新网格搜索优化的最佳参数（$S=0.2$, `price_compare`, $MA=3$），在 5 分钟级别上的回测表现如下：

| 指标 | 策略表现 (QRS Strategy) | 基准 (Buy & Hold) |
| :--- | :--- | :--- |
| **年化收益率** | **12.23%** | -0.11% |
| **夏普比率** | **5.08** | -0.04 |
| **最大回撤** | **-0.97%** | -2.27% |
| **卡玛比率** | **12.55** | -0.05 |
| **胜率** | **52.76%** | 50.03% |

*注：回测未计入手续费与滑点，仅供学术研究参考。*

---

## 3. 快速上手

### 环境安装
```bash
pip install -r requirements.txt
```

### 运行全流程管线
自动执行数据加载、QRS 计算、参数网格搜索、最佳参数回测及报告生成：
```bash
python scripts/run_qrs_pipeline.py --mode intraday --run-grid-search
```

### 参数说明
- `--mode`: `intraday` (默认主策略) 或 `daily_baseline` (日频对照)。
- `--run-grid-search`: 是否运行参数网格搜索。
- `--allow-short`: 是否允许做空 (默认 True)。

---

## 4. 项目结构

```text
├── scripts/
│   ├── run_qrs_pipeline.py   # 主运行入口
│   └── run_backtest.py       # 仅运行回测（使用预处理数据）
├── src/
│   ├── qrs_calculator.py     # QRS 因子计算逻辑
│   ├── trend_filter.py       # 日频趋势过滤机制
│   ├── signal_generator.py   # 多空状态机信号生成
│   ├── grid_search.py        # 参数空间搜索优化
│   └── backtest.py           # 向量化回测引擎
├── data/
│   ├── raw/                  # 原始 OHLC 存放
│   └── processed/            # 预处理后的因子与信号
└── results/
    ├── report.md             # 自动生成的研究报告
    └── figures/              # 净值曲线与信号热力图
```

---

## 5. 免责声明
本项目仅用于量化研究与代码示例，不构成任何投资建议。投资者需独立承担市场风险。
