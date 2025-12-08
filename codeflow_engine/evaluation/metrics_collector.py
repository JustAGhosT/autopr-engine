"""Shim module: re-export canonical metrics collector from codeflow_engine.quality.metrics_collector."""

from codeflow_engine.quality.metrics_collector import (
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
