"""
Platform Detection Utilities

Helper functions for platform detection and analysis.
"""

import re
from pathlib import Path
from typing import Any, Dict, List


def calculate_confidence_score(
    file_score: float,
    dependency_score: float,
    folder_score: float,
    commit_score: float,
    content_score: float
) -> float:
    """Calculate overall confidence score using weighted factors."""
    weights = {
        'files': 0.40,
        'dependencies': 0.25,
        'folder_patterns': 0.20,
        'commit_messages': 0.15,
        'content_patterns': 0.10
    }
    
    # Normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    normalized_weights = {k: v / total_weight for k, v in weights.items()}
    
    # Calculate weighted score using all factors
    total_score = (
        file_score * normalized_weights['files'] +
        dependency_score * normalized_weights['dependencies'] +
        folder_score * normalized_weights['folder_patterns'] +
        commit_score * normalized_weights['commit_messages'] +
        content_score * normalized_weights['content_patterns']
    )
    
    return min(1.0, max(0.0, total_score))


def get_confidence_level(score: float) -> str:
    """Get confidence level based on score."""
    if score > 0.8:
        return "high"
    elif score > 0.5:
        return "medium"
    else:
        return "low"


def extract_platform_config(platform: str, workspace_path: str) -> Dict[str, Any]:
    """Extract platform-specific configuration."""
    # Implementation would go here
    return {}


def generate_migration_suggestions(platform: str) -> List[str]:
    """Generate migration suggestions for detected platform."""
    # Implementation would go here
    return []
