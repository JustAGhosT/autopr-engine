"""Shim module: re-export canonical metrics collector from autopr.quality.metrics_collector."""

from autopr.quality.metrics_collector import (
    EvaluationMetrics,
    MetricPoint,
    MetricsCollector,
    collect_autopr_metrics,
)


__all__ = [
    "EvaluationMetrics",
    "MetricPoint",
    "MetricsCollector",
    "collect_autopr_metrics",
]
