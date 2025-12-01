import statistics
import math
from typing import List, Dict, Any
from collections import defaultdict
from .helpers import round_value


def summarize_metric(values: List[float]) -> Dict[str, float]:
    """
    Given a list of metric values, compute:
      - mean
      - standard deviation (sample)
      - 95% confidence interval
    """
    n = len(values)

    if n == 0:
        return {
            "mean": math.nan,
            "sd": math.nan,
            "ci_low": math.nan,
            "ci_high": math.nan,
            "n": 0,
        }

    mean = statistics.mean(values)

    if n > 1:
        sd = statistics.stdev(values)
        se = sd / math.sqrt(n)
        margin = 1.96 * se
        ci_low = mean - margin
        ci_high = mean + margin
    else:
        sd = math.nan
        ci_low = math.nan
        ci_high = math.nan

    return {
        "mean": round_value(mean),
        "sd": round_value(sd),
        "ci_low": round_value(ci_low),
        "ci_high": round_value(ci_high),
        "n": n,
    }


def compute_metric_stats_from_long_rows(
    rows: List[Dict[str, Any]]
) -> List[Dict[str, float]]:
    """
    Compute statistics PER PRACTICE and PER METRIC.

    Input (long format rows):
        {
            "practice_id": "A",
            "metric_name": "num_turns",
            "metric_value": 12,
            ...
        }

    Output rows (one per practice x metric):
        {
            "practice_id": "A",
            "metric_name": "num_turns",
            "n": ...,
            "mean": ...,
            "sd": ...,
            "ci_low": ...,
            "ci_high": ...
        }
    """

    # group by BOTH practice and metric
    grouped = defaultdict(list)

    for r in rows:
        practice = r["practice_id"]
        name = r["metric_name"]
        value = float(r["metric_value"])
        grouped[(practice, name)].append(value)

    stats_rows: List[Dict[str, float]] = []

    for (practice_id, metric_name), values in grouped.items():
        stats = summarize_metric(values)
        stats_rows.append({
            "practice_id": practice_id,
            "metric_name": metric_name,
            "n": stats["n"],
            "mean": round_value(stats["mean"]),
            "sd": round_value(stats["sd"]),
            "ci_low": round_value(stats["ci_low"]),
            "ci_high": round_value(stats["ci_high"]),
        })

    return stats_rows
