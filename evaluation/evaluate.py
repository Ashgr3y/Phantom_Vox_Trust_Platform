"""Compute transparent binary anti-spoofing metrics from a labeled score CSV.

The script never invents predictions. Every row must contain a ground-truth
label (genuine or spoof) and an uncalibrated or calibrated score in [0, 1].
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("The manifest contains no labeled samples")
    for number, row in enumerate(rows, start=2):
        label = row.get("label", "").strip().lower()
        if label not in {"genuine", "spoof"}:
            raise ValueError(f"Row {number}: label must be genuine or spoof")
        try:
            score = float(row.get("score", ""))
        except ValueError as exc:
            raise ValueError(f"Row {number}: score is not numeric") from exc
        if not 0 <= score <= 1:
            raise ValueError(f"Row {number}: score must be between 0 and 1")
        row["score"] = score
        row["target"] = 1 if label == "spoof" else 0
    return rows


def confusion(rows: list[dict], threshold: float) -> dict[str, int]:
    result = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    for row in rows:
        prediction = 1 if row["score"] >= threshold else 0
        key = "tp" if prediction == 1 and row["target"] == 1 else "tn" if prediction == 0 and row["target"] == 0 else "fp" if prediction == 1 else "fn"
        result[key] += 1
    return result


def safe_ratio(numerator: float, denominator: float) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def metrics(rows: list[dict], threshold: float) -> dict:
    counts = confusion(rows, threshold)
    tp, tn, fp, fn = counts["tp"], counts["tn"], counts["fp"], counts["fn"]
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    f1 = None if precision is None or recall is None or precision + recall == 0 else round(2 * precision * recall / (precision + recall), 6)
    return {
        "threshold": threshold,
        "samples": len(rows),
        "confusion_matrix": counts,
        "accuracy": safe_ratio(tp + tn, len(rows)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_acceptance_rate": safe_ratio(fn, tp + fn),
        "false_rejection_rate": safe_ratio(fp, tn + fp),
    }


def approximate_eer(rows: list[dict]) -> dict:
    best = None
    for step in range(1001):
        threshold = step / 1000
        counts = confusion(rows, threshold)
        far = safe_ratio(counts["fn"], counts["tp"] + counts["fn"])
        frr = safe_ratio(counts["fp"], counts["tn"] + counts["fp"])
        if far is None or frr is None:
            continue
        candidate = (abs(far - frr), (far + frr) / 2, threshold)
        if best is None or candidate < best:
            best = candidate
    if best is None:
        return {"eer": None, "eer_threshold": None}
    return {"eer": round(best[1], 6), "eer_threshold": best[2]}


def subgroup_metrics(rows: list[dict], column: str, threshold: float) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row.get(column, "unspecified") or "unspecified"].append(row)
    return {name: metrics(group, threshold) for name, group in sorted(groups.items())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--output", type=Path, default=Path("reports/evaluation-report.json"))
    args = parser.parse_args()
    rows = read_rows(args.manifest)
    if not 0 <= args.threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    report = {
        "name": "Phantom Vox labeled evaluation",
        "dataset_name": args.manifest.stem,
        "verified": False,
        "metrics": {**metrics(rows, args.threshold), **approximate_eer(rows)},
        "coverage": {
            column: subgroup_metrics(rows, column, args.threshold)
            for column in ("attack_type", "generator", "language", "accent", "gender", "codec", "noise_condition")
        },
        "notes": "Set verified=true only after independent protocol and label review.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
