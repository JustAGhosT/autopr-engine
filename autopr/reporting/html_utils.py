from __future__ import annotations


"""
Shared HTML report helpers for consistent styling and status coloring.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthTheme:
    good: str = "#28a745"
    warning: str = "#ffc107"
    danger: str = "#dc3545"


def health_color_from_score(score: float, *, theme: HealthTheme | None = None) -> str:
    theme = theme or HealthTheme()
    if score >= 80:
        return theme.good
    if score >= 60:
        return theme.warning
    return theme.danger


def status_color_name(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"
