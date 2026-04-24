from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .utils import ensure_dir


def setup_style() -> None:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def plot_qrs_price_overlay(data: pd.DataFrame, output: str | Path) -> Path:
    setup_style()
    path = Path(output)
    ensure_dir(path.parent)
    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax2 = ax1.twinx()
    qrs_col = "qrs" if "qrs" in data.columns else "qrs_zscore"
    ax1.plot(data["date"], data["close"], label="Close", color="#1f77b4", linewidth=1.4)
    ax2.plot(data["date"], data[qrs_col], label=qrs_col, color="#d62728", linewidth=1.0, alpha=0.8)
    ax2.axhline(0.5, color="#2ca02c", linestyle="--", linewidth=0.9)
    ax2.axhline(-0.5, color="#9467bd", linestyle="--", linewidth=0.9)
    ax1.set_title("QRS Indicator and Futures Close Price")
    ax1.set_ylabel("Close")
    ax2.set_ylabel("QRS z-score")
    ax1.grid(alpha=0.25)
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], loc="upper left", frameon=False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_nav_comparison(data: pd.DataFrame, output: str | Path) -> Path:
    setup_style()
    path = Path(output)
    ensure_dir(path.parent)
    fig, ax = plt.subplots(figsize=(14, 6))
    strategy_col = "nav_strategy" if "nav_strategy" in data.columns else "strategy_nav"
    benchmark_col = "nav_benchmark" if "nav_benchmark" in data.columns else "benchmark_nav"
    ax.plot(data["date"], data[strategy_col], label="QRS Strategy", linewidth=1.6)
    ax.plot(data["date"], data[benchmark_col], label="Long-only Benchmark", linewidth=1.6)
    ax.set_title("Strategy NAV vs Benchmark")
    ax.set_ylabel("NAV")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_drawdown(data: pd.DataFrame, output: str | Path) -> Path:
    setup_style()
    path = Path(output)
    ensure_dir(path.parent)
    fig, ax = plt.subplots(figsize=(14, 5))
    strategy_col = "drawdown_strategy" if "drawdown_strategy" in data.columns else "strategy_drawdown"
    benchmark_col = "drawdown_benchmark" if "drawdown_benchmark" in data.columns else "benchmark_drawdown"
    ax.fill_between(data["date"], data[strategy_col], 0, label="QRS Strategy", alpha=0.45)
    ax.fill_between(data["date"], data[benchmark_col], 0, label="Benchmark", alpha=0.35)
    ax.set_title("Drawdown")
    ax.set_ylabel("Drawdown")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_qrs_future_return(data: pd.DataFrame, output: str | Path, horizon: int = 5) -> Path:
    setup_style()
    path = Path(output)
    ensure_dir(path.parent)
    qrs_col = "qrs" if "qrs" in data.columns else "qrs_zscore"
    plot_df = data[[qrs_col, "close"]].copy()
    plot_df["future_return"] = plot_df["close"].shift(-int(horizon)) / plot_df["close"] - 1.0
    plot_df = plot_df.dropna(subset=[qrs_col, "future_return"])
    fig, ax = plt.subplots(figsize=(8, 6))
    if not plot_df.empty:
        ax.scatter(plot_df[qrs_col], plot_df["future_return"], s=14, alpha=0.55)
        grouped = plot_df.assign(bucket=pd.qcut(plot_df[qrs_col], q=10, duplicates="drop"))
        bucket_mean = grouped.groupby("bucket", observed=False).agg(qrs=(qrs_col, "mean"), future_return=("future_return", "mean"))
        ax.plot(bucket_mean["qrs"], bucket_mean["future_return"], color="#d62728", marker="o", label="Decile mean")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title(f"QRS z-score vs {horizon}-day Future Return")
    ax.set_xlabel("QRS z-score")
    ax.set_ylabel("Future return")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_best_strategy_position(data: pd.DataFrame, output: str | Path) -> Path:
    setup_style()
    path = Path(output)
    ensure_dir(path.parent)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(data["date"], data["close"], color="#1f77b4", linewidth=1.3, label="Close")
    y_min = data["close"].min()
    y_max = data["close"].max()
    long_mask = data["position"].fillna(0.0) > 0
    short_mask = data["position"].fillna(0.0) < 0
    ax.fill_between(data["date"], y_min, y_max, where=long_mask, color="#d62728", alpha=0.12, label="Long")
    ax.fill_between(data["date"], y_min, y_max, where=short_mask, color="#1f77b4", alpha=0.12, label="Short")
    ax.set_title("Best Strategy Position Regimes")
    ax.set_ylabel("Close")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path
