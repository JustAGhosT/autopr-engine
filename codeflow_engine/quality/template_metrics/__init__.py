"""
Template Quality Metrics Package
================================

A comprehensive package for template quality assessment, scoring, and analysis.

This package provides modular components for evaluating template quality,
including scoring algorithms, trend analysis, and improvement recommendations.

Components:
- QualityMetrics: Core dataclass for quality metrics and calculations
- QualityScorer: Scoring algorithms and quality calculations
- QualityAnalyzer: Advanced analysis and insights
- Factory functions: Convenient access to global instances

Usage:
    from codeflow_engine.quality.template_metrics import QualityMetrics, QualityScorer, QualityAnalyzer
    from codeflow_engine.quality.template_metrics import get_quality_scorer, get_quality_analyzer
"""

from codeflow_engine.quality.template_metrics.quality_analyzer import QualityAnalyzer
from codeflow_engine.quality.template_metrics.quality_models import QualityMetrics
from codeflow_engine.quality.template_metrics.quality_scorer import QualityScorer


# Factory functions for global instances
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


# Public API
__all__ = [
    "QualityAnalyzer",
    "QualityMetrics",
    "QualityScorer",
    "get_quality_analyzer",
    "get_quality_scorer",
]

__version__ = "1.0.0"
