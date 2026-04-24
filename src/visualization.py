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
    ax1.plot(data["date"], data["close"], label="Close", color="#1f77b4", linewidth=1.4)
    ax2.plot(data["date"], data["qrs_zscore"], label="QRS z-score", color="#d62728", linewidth=1.0, alpha=0.8)
    ax2.axhline(0.7, color="#2ca02c", linestyle="--", linewidth=0.9)
    ax2.axhline(-0.7, color="#9467bd", linestyle="--", linewidth=0.9)
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
    ax.plot(data["date"], data["strategy_nav"], label="QRS Strategy", linewidth=1.6)
    ax.plot(data["date"], data["benchmark_nav"], label="Long-only Benchmark", linewidth=1.6)
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
    ax.fill_between(data["date"], data["strategy_drawdown"], 0, label="QRS Strategy", alpha=0.45)
    ax.fill_between(data["date"], data["benchmark_drawdown"], 0, label="Benchmark", alpha=0.35)
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
    plot_df = data[["qrs_zscore", "close"]].copy()
    plot_df["future_return"] = plot_df["close"].shift(-int(horizon)) / plot_df["close"] - 1.0
    plot_df = plot_df.dropna(subset=["qrs_zscore", "future_return"])
    fig, ax = plt.subplots(figsize=(8, 6))
    if not plot_df.empty:
        ax.scatter(plot_df["qrs_zscore"], plot_df["future_return"], s=14, alpha=0.55)
        grouped = plot_df.assign(bucket=pd.qcut(plot_df["qrs_zscore"], q=10, duplicates="drop"))
        bucket_mean = grouped.groupby("bucket", observed=False).agg(qrs=("qrs_zscore", "mean"), future_return=("future_return", "mean"))
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
