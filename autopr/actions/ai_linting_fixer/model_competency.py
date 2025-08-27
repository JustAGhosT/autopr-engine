"""
Model Competency Rating System

This module handles model competency ratings and intelligent fallback logic
for the AI linting fixer.
"""

import logging
from typing import Any

from autopr.actions.ai_linting_fixer.model_configs import (
    ALL_MODEL_CONFIGS,
    update_all_availabilities,
)


logger = logging.getLogger(__name__)


class ModelCompetencyManager:
    """Manages model competency ratings and fallback strategies."""

    def __init__(self):
        """Initialize the competency manager with predefined ratings."""
        self.model_competency = self._initialize_competency_ratings()
        self.fallback_strategies = self._initialize_fallback_strategies()
        self.available_models = {}
        self._update_model_availabilities()

    def _initialize_competency_ratings(self) -> dict[str, dict[str, float]]:
        """Initialize model competency ratings for different issue types."""
        # Start with existing cloud models
        ratings = {
            "gpt-35-turbo": {
                "E501": 0.6,  # Line length - moderate competency
                "F401": 0.8,  # Unused imports - high competency
                "PTH123": 0.9,  # Path handling - very high competency
                "PTH118": 0.9,  # Path handling - very high competency
                "PTH110": 0.9,  # Path handling - very high competency
                "PTH103": 0.9,  # Path handling - very high competency
                "SIM102": 0.7,  # Code simplification - moderate competency
                "SIM117": 0.7,  # Code simplification - moderate competency
                "SIM105": 0.7,  # Code simplification - moderate competency
                "SIM103": 0.7,  # Code simplification - moderate competency
                "TRY401": 0.8,  # Exception handling - high competency
                "TRY300": 0.8,  # Exception handling - high competency
                "TRY203": 0.8,  # Exception handling - high competency
                "TRY301": 0.8,  # Exception handling - high competency
                "G004": 0.9,  # Logging - very high competency
                "ARG001": 0.9,  # Arguments - very high competency
                "ARG002": 0.9,  # Arguments - very high competency
                "TID252": 0.8,  # Import style - high competency
            },
            "gpt-4": {
                "E501": 0.8,  # Line length - high competency
                "F401": 0.9,  # Unused imports - very high competency
                "PTH123": 0.95,  # Path handling - excellent competency
                "PTH118": 0.95,  # Path handling - excellent competency
                "PTH110": 0.95,  # Path handling - excellent competency
                "PTH103": 0.95,  # Path handling - excellent competency
                "SIM102": 0.85,  # Code simplification - high competency
                "SIM117": 0.85,  # Code simplification - high competency
                "SIM105": 0.85,  # Code simplification - high competency
                "SIM103": 0.85,  # Code simplification - high competency
                "TRY401": 0.9,  # Exception handling - very high competency
                "TRY300": 0.9,  # Exception handling - very high competency
                "TRY203": 0.9,  # Exception handling - very high competency
                "TRY301": 0.9,  # Exception handling - very high competency
                "G004": 0.95,  # Logging - excellent competency
                "ARG001": 0.95,  # Arguments - excellent competency
                "ARG002": 0.95,  # Arguments - excellent competency
                "TID252": 0.9,  # Import style - very high competency
            },
            "gpt-4o": {
                "E501": 0.9,  # Line length - very high competency
                "F401": 0.95,  # Unused imports - excellent competency
                "PTH123": 0.98,  # Path handling - outstanding competency
                "PTH118": 0.98,  # Path handling - outstanding competency
                "PTH110": 0.98,  # Path handling - outstanding competency
                "PTH103": 0.98,  # Path handling - outstanding competency
                "SIM102": 0.9,  # Code simplification - very high competency
                "SIM117": 0.9,  # Code simplification - very high competency
                "SIM105": 0.9,  # Code simplification - very high competency
                "SIM103": 0.9,  # Code simplification - very high competency
                "TRY401": 0.95,  # Exception handling - excellent competency
                "TRY300": 0.95,  # Exception handling - excellent competency
                "TRY203": 0.95,  # Exception handling - excellent competency
                "TRY301": 0.95,  # Exception handling - excellent competency
                "G004": 0.98,  # Logging - outstanding competency
                "ARG001": 0.98,  # Arguments - outstanding competency
                "ARG002": 0.98,  # Arguments - outstanding competency
                "TID252": 0.95,  # Import style - excellent competency
            },
            "claude-3-sonnet-20240229": {
                "E501": 0.85,  # Line length - high competency
                "F401": 0.9,  # Unused imports - very high competency
                "PTH123": 0.95,  # Path handling - excellent competency
                "PTH118": 0.95,  # Path handling - excellent competency
                "PTH110": 0.95,  # Path handling - excellent competency
                "PTH103": 0.95,  # Path handling - excellent competency
                "SIM102": 0.9,  # Code simplification - very high competency
                "SIM117": 0.9,  # Code simplification - very high competency
                "SIM105": 0.9,  # Code simplification - very high competency
                "SIM103": 0.9,  # Code simplification - very high competency
                "TRY401": 0.9,  # Exception handling - very high competency
                "TRY300": 0.9,  # Exception handling - very high competency
                "TRY203": 0.9,  # Exception handling - very high competency
                "TRY301": 0.9,  # Exception handling - very high competency
                "G004": 0.95,  # Logging - excellent competency
                "ARG001": 0.95,  # Arguments - excellent competency
                "ARG002": 0.95,  # Arguments - excellent competency
                "TID252": 0.9,  # Import style - very high competency
            },
        }

        # Add ratings from model configurations
        for model_config in ALL_MODEL_CONFIGS:
            if model_config.competency_ratings:
                ratings[model_config.name] = model_config.competency_ratings

        return ratings

    def _initialize_fallback_strategies(self) -> dict[str, list[tuple[str, str]]]:
        """Initialize fallback strategies for different issue types."""
        return {
            "default": [
                ("gpt-5-chat", "openai"),  # Best model (when available)
                ("gpt-4o", "azure_openai"),  # Current best cloud model
                ("deepseek-v3", "local"),  # Best local model
                ("llama-3.3-70b", "local"),  # High competency local
                ("gpt-4", "azure_openai"),  # Reliable cloud fallback
                ("deepseek-r1-7b", "local"),  # Good local option
                ("claude-3-sonnet-20240229", "anthropic"),  # Alternative cloud
                ("gpt-35-turbo", "azure_openai"),  # Fast cloud fallback
                ("qwen-2.5", "local"),  # Multilingual local
                ("mistral-7b", "local"),  # Fast local
                ("phi-4-mini", "local"),  # Lightweight local
            ],
            "complex": [  # For complex issues like E501
                ("gpt-5-chat", "openai"),  # Ultimate model
                ("gpt-4o", "azure_openai"),  # Best available cloud
                ("deepseek-v3", "local"),  # Best local for complex tasks
                ("llama-3.3-70b", "local"),  # High-end local
                ("gpt-4", "azure_openai"),  # Solid cloud fallback
                ("deepseek-r1-7b", "local"),  # Good reasoning model
                ("claude-3-sonnet-20240229", "anthropic"),  # Alternative cloud
            ],
            "simple": [  # For simple issues like PTH123, F401
                ("gpt-35-turbo", "azure_openai"),  # Fast and effective
                ("mistral-7b", "local"),  # Fast local option
                ("deepseek-r1-7b", "local"),  # Good local model
                ("phi-4-mini", "local"),  # Efficient edge model
                ("qwen-2.5", "local"),  # Good general purpose
                ("gpt-4", "azure_openai"),  # High quality backup
                ("gpt-4o", "azure_openai"),  # Premium backup
            ],
            "local_preferred": [  # For privacy-sensitive environments
                ("deepseek-v3", "local"),  # Best local
                ("llama-3.3-70b", "local"),  # High competency local
                ("deepseek-r1-7b", "local"),  # Excellent reasoning
                ("qwen-2.5", "local"),  # Multilingual
                ("mistral-7b", "local"),  # Fast development
                ("phi-4-mini", "local"),  # Edge deployment
            ],
            "cloud_only": [  # For cloud-only deployments
                ("gpt-5-chat", "openai"),  # Best when available
                ("gpt-4o", "azure_openai"),  # Current best
                ("gpt-4", "azure_openai"),  # Reliable
                ("claude-3-sonnet-20240229", "anthropic"),  # Alternative
                ("gpt-35-turbo", "azure_openai"),  # Fast fallback
            ],
        }

    def get_model_competency(self, model_name: str, error_code: str) -> float:
        """Get the competency rating for a model on a specific error code."""
        return self.model_competency.get(model_name, {}).get(error_code, 0.5)

    def get_fallback_sequence(
        self, error_code: str, strategy_override: str = None
    ) -> list[tuple[str, str]]:
        """Get the optimal fallback sequence for an error code."""
        if strategy_override:
            strategy = strategy_override
        else:
            # Determine complexity based on error code
            if error_code in ["E501"]:  # Complex issues
                strategy = "complex"
            elif error_code in [
                "PTH123",
                "PTH118",
                "PTH110",
                "PTH103",
                "G004",
                "ARG001",
                "ARG002",
                "F401",
                "T201",
            ]:  # Simple issues
                strategy = "simple"
            else:
                strategy = "default"

        sequence = self.fallback_strategies[strategy]

        # Filter to only include available models
        available_sequence = []
        for model_name, provider in sequence:
            if self._is_model_available(model_name):
                available_sequence.append((model_name, provider))

        # If no models available from strategy, fall back to default available models
        if not available_sequence:
            available_sequence = [
                (model, "local") for model in self.get_available_model_names()
            ]

        return available_sequence

    def calculate_confidence(
        self, model_name: str, error_code: str, fix_successful: bool = True
    ) -> float:
        """Calculate confidence score based on model competency and fix success."""
        base_competency = self.get_model_competency(model_name, error_code)

        if fix_successful:
            # Add small boost for successful fix
            return min(0.95, base_competency + 0.1)
        else:
            # Reduce confidence for failed fixes
            return max(0.1, base_competency - 0.2)

    def get_best_model_for_issue(
        self, error_code: str, available_models: list[str] = None
    ) -> str:
        """Get the best available model for a specific issue type."""
        if available_models is None:
            available_models = self.get_available_model_names()

        fallback_sequence = self.get_fallback_sequence(error_code)

        for model_name, _ in fallback_sequence:
            if model_name in available_models:
                return model_name

        # Fallback to first available model
        return available_models[0] if available_models else "gpt-35-turbo"

    def _update_model_availabilities(self) -> None:
        """Update availability status for all models."""
        try:
            self.available_models = update_all_availabilities()
            logger.info(f"Updated model availability: {self.available_models}")
        except Exception as e:
            logger.warning(f"Error updating model availabilities: {e}")
            self.available_models = {}

    def _is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        # Always consider cloud models available (they will fail gracefully)
        cloud_models = [
            "gpt-35-turbo",
            "gpt-4",
            "gpt-4o",
            "gpt-5-chat",
            "claude-3-sonnet-20240229",
        ]
        if model_name in cloud_models:
            return True

        # Check local models from availability cache
        return self.available_models.get(model_name, False)

    def get_available_model_names(self) -> list[str]:
        """Get list of currently available model names."""
        available = []

        # Add available cloud models
        cloud_models = ["gpt-35-turbo", "gpt-4", "gpt-4o"]
        if self.available_models.get("gpt-5-chat", False):
            cloud_models.append("gpt-5-chat")
        available.extend(cloud_models)

        # Add available local models
        for model_name, is_available in self.available_models.items():
            if is_available and model_name not in cloud_models:
                available.append(model_name)

        return available

    def refresh_availability(self) -> dict[str, bool]:
        """Refresh and return current model availability."""
        self._update_model_availabilities()
        return self.available_models.copy()

    def get_model_info(self, model_name: str) -> dict[str, Any]:
        """Get detailed information about a model."""
        for config in ALL_MODEL_CONFIGS:
            if config.name == model_name:
                return {
                    "name": config.name,
                    "provider": config.provider,
                    "vram_required": config.vram_required,
                    "performance_tier": config.performance_tier,
                    "availability": self._is_model_available(model_name),
                    "competency_ratings": config.competency_ratings,
                    "use_cases": config.recommended_use_cases,
                }

        # Return info for legacy cloud models
        legacy_models = {
            "gpt-35-turbo": {"provider": "azure_openai", "performance_tier": "Fast"},
            "gpt-4": {"provider": "azure_openai", "performance_tier": "High"},
            "gpt-4o": {"provider": "azure_openai", "performance_tier": "Excellent"},
            "claude-3-sonnet-20240229": {
                "provider": "anthropic",
                "performance_tier": "High",
            },
        }

        if model_name in legacy_models:
            info = legacy_models[model_name].copy()
            info.update(
                {
                    "name": model_name,
                    "availability": True,
                    "competency_ratings": self.model_competency.get(model_name, {}),
                }
            )
            return info

        return {"name": model_name, "availability": False}


# Global instance
competency_manager = ModelCompetencyManager()
