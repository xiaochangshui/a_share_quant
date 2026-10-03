"""Orchestration and artifact output for a repeatable research run."""

from dataclasses import dataclass
import json
from pathlib import Path

import pandas as pd

from .backtest import BacktestResult, run_backtest
from .config import load_research_config
from .data import load_daily_data
from .factor import calculate_momentum
from .metrics import calculate_metrics
from .signal import generate_top_n_targets


@dataclass
class ResearchArtifacts:
    factors: pd.DataFrame
    targets: pd.DataFrame
    backtest: BacktestResult
    metrics: dict[str, float]
    output_dir: Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_research(config_path: str | Path) -> ResearchArtifacts:
    """Run the configured momentum research and overwrite deterministic outputs."""
    config = load_research_config(config_path)
    market = load_daily_data(config.data_path)
    factors = calculate_momentum(market, window=config.momentum_window)
    targets = generate_top_n_targets(factors, top_n=config.top_n)
    backtest = run_backtest(
        market,
        targets,
        initial_cash=config.initial_cash,
        cost_config=config.costs,
    )
    metrics = calculate_metrics(backtest)

    output = config.output_dir
    output.mkdir(parents=True, exist_ok=True)
    tables = {
        "factors": factors,
        "targets": targets,
        "equity": backtest.equity,
        "positions": backtest.positions,
        "trades": backtest.trades,
    }
    for name, table in tables.items():
        table.to_csv(output / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    _write_json(output / "report.json", {
        "metrics": metrics,
        "row_counts": {name: len(table) for name, table in tables.items()},
    })
    _write_json(output / "config_snapshot.json", config.as_dict())
    return ResearchArtifacts(factors, targets, backtest, metrics, output)
