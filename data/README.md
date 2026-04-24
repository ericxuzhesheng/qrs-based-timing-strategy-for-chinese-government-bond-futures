# Data

- `data/raw/`: place local raw CSV/Excel files here. Raw data is ignored by git to avoid committing large or proprietary files.
- `data/processed/qrs_daily.csv`: generated daily QRS, signal, and backtest data from `scripts/run_qrs_pipeline.py`.

The loader supports CSV and Excel files with common English/Chinese market-data fields such as `date`, `time`, `open`, `high`, `low`, `close`, `volume`, `open_interest`, `日期`, `开盘价`, `最高价`, `最低价`, `收盘价`, `成交量`, and `持仓量`.
