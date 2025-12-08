"""
Model Configurations Package

This package contains individual model configurations for AI linting with
availability detection and performance characteristics.
"""

import logging
from functools import partial

from codeflow_engine.actions.ai_linting_fixer.model_configs.deepseek_r1_7b import \
    DEEPSEEK_R1_7B_CONFIG
from codeflow_engine.actions.ai_linting_fixer.model_configs.deepseek_r1_7b import \
    update_availability as update_deepseek_r1_availability
from codeflow_engine.actions.ai_linting_fixer.model_configs.deepseek_v3 import \
    DEEPSEEK_V3_CONFIG
from codeflow_engine.actions.ai_linting_fixer.model_configs.deepseek_v3 import \
    update_availability as update_deepseek_v3_availability
from codeflow_engine.actions.ai_linting_fixer.model_configs.gpt_5_chat import \
    GPT_5_CHAT_CONFIG
from codeflow_engine.actions.ai_linting_fixer.model_configs.llama_3_3_70b import \
    LLAMA_3_3_70B_CONFIG
from codeflow_engine.actions.ai_linting_fixer.model_configs.llama_3_3_70b import \
    update_availability as update_llama_availability
from codeflow_engine.actions.ai_linting_fixer.model_configs.mistral_7b import \
    MISTRAL_7B_CONFIG
from codeflow_engine.actions.ai_linting_fixer.model_configs.mistral_7b import \
    update_availability as update_mistral_availability
from codeflow_engine.actions.ai_linting_fixer.model_configs.phi_4_mini import \
    PHI_4_MINI_CONFIG
from codeflow_engine.actions.ai_linting_fixer.model_configs.phi_4_mini import \
    update_availability as update_phi_mini_availability
from codeflow_engine.actions.ai_linting_fixer.model_configs.qwen_2_5 import \
    QWEN_2_5_CONFIG
from codeflow_engine.actions.ai_linting_fixer.model_configs.qwen_2_5 import \
    update_availability as update_qwen_availability
from codeflow_engine.actions.ai_linting_fixer.shared.gpt5_helper import \
    update_availability as update_gpt5_availability

logger = logging.getLogger(__name__)

# All model configurations
ALL_MODEL_CONFIGS = [
    GPT_5_CHAT_CONFIG,
    MISTRAL_7B_CONFIG,
    DEEPSEEK_R1_7B_CONFIG,
    LLAMA_3_3_70B_CONFIG,
    DEEPSEEK_V3_CONFIG,
    PHI_4_MINI_CONFIG,
    QWEN_2_5_CONFIG,
]

# Availability update functions
AVAILABILITY_UPDATERS = {
    # Do not overwrite release flag; update endpoint only
    "gpt-5-chat": partial(update_gpt5_availability, GPT_5_CHAT_CONFIG, update_endpoint_only=True),
    "mistral-7b": update_mistral_availability,
    "deepseek-r1-7b": update_deepseek_r1_availability,
    "llama-3.3-70b": update_llama_availability,
    "deepseek-v3": update_deepseek_v3_availability,
    "phi-4-mini": update_phi_mini_availability,
    "qwen-2.5": update_qwen_availability,
}


def update_all_availabilities():
    """Update availability status for all models."""
    results = {}
    for model_name, updater in AVAILABILITY_UPDATERS.items():
        try:
            results[model_name] = updater()
        except Exception:
            logger.exception("Failed to update availability for model %s", model_name)
            results[model_name] = False
    return results


def get_available_models():
    """Get list of currently available models."""
    return [config for config in ALL_MODEL_CONFIGS if config.availability]


def get_model_by_name(name: str):
    """Get model configuration by name."""
    for config in ALL_MODEL_CONFIGS:
        if config.name == name:
            return config
    return None


__all__ = [
    "ALL_MODEL_CONFIGS",
    "AVAILABILITY_UPDATERS",
    "update_all_availabilities",
    "get_available_models",
    "get_model_by_name",
    "GPT_5_CHAT_CONFIG",
    "MISTRAL_7B_CONFIG",
    "DEEPSEEK_R1_7B_CONFIG",
    "LLAMA_3_3_70B_CONFIG",
    "DEEPSEEK_V3_CONFIG",
    "PHI_4_MINI_CONFIG",
    "QWEN_2_5_CONFIG",
]
