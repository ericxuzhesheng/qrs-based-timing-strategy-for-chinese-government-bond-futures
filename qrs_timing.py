from __future__ import annotations

from scripts.run_qrs_pipeline import parse_args, run_pipeline


if __name__ == "__main__":
    run_pipeline(parse_args())
