"""
Quality Metrics - Backward Compatibility Module
===============================================

This module provides backward compatibility for the quality metrics system
that was moved from templates.discovery.quality_metrics to the new modular structure.

This file maintains the same API as the original quality_metrics.py file
while importing from the new modular components.
"""

from autopr.quality.template_metrics.quality_analyzer import QualityAnalyzer
from autopr.quality.template_metrics.quality_models import (
    DEFAULT_CATEGORY_WEIGHTS,
    DEFAULT_SEVERITY_WEIGHTS,
    QUALITY_GRADES,
    QualityMetrics,
)
from autopr.quality.template_metrics.quality_scorer import QualityScorer


# Global instances for backward compatibility
_scorer_instance: QualityScorer | None = None
_analyzer_instance: QualityAnalyzer | None = None


def get_quality_scorer() -> QualityScorer:
    """Get a global QualityScorer instance."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = QualityScorer()
    return _scorer_instance


def get_quality_analyzer() -> QualityAnalyzer:
    """Get a global QualityAnalyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = QualityAnalyzer()
    return _analyzer_instance


# Factory functions for easy instantiation
def create_quality_scorer(severity_weights=None, category_weights=None) -> QualityScorer:
    """Create a new quality scorer with optional custom weights."""
    scorer = QualityScorer()
    if severity_weights or category_weights:
        scorer.update_weights(severity_weights, category_weights)
    return scorer


def create_quality_analyzer() -> QualityAnalyzer:
    """Create a new quality analyzer instance."""
    return QualityAnalyzer()


# Convenience functions
def calculate_quality_metrics(issues, total_checks, template_path="") -> QualityMetrics:
    """Calculate quality metrics using the global scorer."""
    scorer = get_quality_scorer()
    return scorer.calculate_metrics(issues, total_checks, template_path)


def analyze_template_quality(metrics: QualityMetrics):
    """Analyze template quality using the global analyzer."""
    analyzer = get_quality_analyzer()
    return analyzer.analyze_template_quality(metrics)


def batch_analyze_templates(template_metrics):
    """Batch analyze multiple templates using the global analyzer."""
    analyzer = get_quality_analyzer()
    return analyzer.batch_analyze_templates(template_metrics)


# Export all public classes and functions
__all__ = [
    "DEFAULT_CATEGORY_WEIGHTS",
    "DEFAULT_SEVERITY_WEIGHTS",
    # Constants
    "QUALITY_GRADES",
    "QualityAnalyzer",
    # Core classes
    "QualityMetrics",
    "QualityScorer",
    "analyze_template_quality",
    "batch_analyze_templates",
    # Convenience functions
    "calculate_quality_metrics",
    "create_quality_analyzer",
    "create_quality_scorer",
    "get_quality_analyzer",
    # Factory functions
    "get_quality_scorer",
]
