"""
Deterministic aggregation of validator results into a hygiene score and rating.

This module is intentionally independent from validator internals and relies
only on the presence of a severity value for each result item. It exposes a
single pure function, ``aggregate_validator_results``, which accepts an
iterable of validator outputs and returns an explainable score, rating, and
severity counts.
"""
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping, MutableMapping, Optional

# Default weights used to penalize findings by severity.
DEFAULT_SEVERITY_WEIGHTS: Mapping[str, int] = {
    "critical": 25,
    "high": 10,
    "medium": 3,
    "low": 1,
}

CRITICAL_SEVERITY = "critical"

# Fallback penalty applied when a result has an unrecognized severity label.
UNKNOWN_SEVERITY_WEIGHT = 3

MAX_SCORE = 100


def _extract_severity(result: Any) -> str:
    """
    Pull a severity label from a validator result without depending on
    validator-specific shapes.

    Accepted patterns:
    - Mapping with a "severity" key
    - Object with a ``severity`` attribute
    - A bare string interpreted directly as the severity label
    """
    severity_value: Optional[str] = None

    if isinstance(result, Mapping) and "severity" in result:
        severity_value = str(result["severity"])

    if severity_value is None and hasattr(result, "severity"):
        severity_value = str(getattr(result, "severity"))

    if severity_value is None and isinstance(result, str):
        severity_value = result

    return (severity_value or "unknown").lower()


def _rating_from_score(score: int) -> str:
    """
    Convert a hygiene score into a qualitative rating.
    """
    if score >= 90:
        return "clean"

    if score >= 70:
        return "needs_attention"

    if score >= 40:
        return "high_risk"

    return "unsafe"


def _build_summary(rating: str, counts: Mapping[str, int]) -> Iterable[str]:
    """
    Provide short, deterministic summary messages derived from findings.
    """
    primary_messages = {
        "critical": "Critical issues detected",
        "high": "High-severity issues detected",
        "medium": "Medium-severity issues detected",
        "low": "Low-severity findings detected",
    }

    secondary_messages = {
        "clean": "Data appears ready for use",
        "needs_attention": "Data suitable for internal use only",
        "high_risk": "Remediation recommended before broader use",
        "unsafe": "Data unsafe for processing until remediated",
    }

    for severity in ("critical", "high", "medium", "low"):
        if counts.get(severity, 0) > 0:
            yield primary_messages[severity]
            break
    else:
        yield "No issues detected"

    yield secondary_messages[rating]


def aggregate_validator_results(
    results: Iterable[Any],
    severity_weights: Optional[Mapping[str, int]] = None,
) -> Mapping[str, Any]:
    """
    Aggregate validator results into a deterministic hygiene score and rating.

    Parameters
    ----------
    results:
        Iterable of validator outputs. Each item should expose a severity label
        via a ``severity`` attribute, ``severity`` mapping key, or be a string
        representing the severity directly.
    severity_weights:
        Optional overrides for the default severity weighting table.

    Returns
    -------
    dict with keys:
        - hygiene_score: int in [0, 100]
        - rating: str, one of {"clean", "needs_attention", "high_risk", "unsafe"}
        - severity_counts: dict of severities observed
        - penalties: explainable penalty breakdown
        - summary: short human-readable statements derived from findings
    """
    weights = dict(DEFAULT_SEVERITY_WEIGHTS)
    if severity_weights:
        weights.update(severity_weights)

    severity_counts: Counter[str] = Counter()
    penalty_by_severity: MutableMapping[str, int] = defaultdict(
        int, {severity: 0 for severity in weights}
    )

    total_penalty = 0

    for result in results:
        severity = _extract_severity(result)
        weight = weights.get(severity, UNKNOWN_SEVERITY_WEIGHT)

        severity_counts[severity] += 1
        penalty_by_severity[severity] += weight
        total_penalty += weight

    hygiene_score = max(0, MAX_SCORE - total_penalty)
    rating = _rating_from_score(hygiene_score)

    severity_counts_output = dict(severity_counts)
    for severity in weights:
        severity_counts_output.setdefault(severity, 0)

    return {
        "hygiene_score": hygiene_score,
        "rating": rating,
        "severity_counts": severity_counts_output,
        "penalties": {
            "total_penalty": total_penalty,
            "by_severity": dict(penalty_by_severity),
            "weights": dict(weights),
            "unknown_weight": UNKNOWN_SEVERITY_WEIGHT,
        },
        "max_score": MAX_SCORE,
        "summary": list(_build_summary(rating, severity_counts_output)),
    }
