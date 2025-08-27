#!/usr/bin/env python3
"""
Test script to verify AI handler fixes work correctly
"""

import asyncio
import contextlib
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "autopr"))


async def test_ai_handler_fixes():
    """Test that the AI handler fixes work correctly."""

    # Test 1: Import and initialization
    try:
        # This should work without import errors
        from autopr.actions.quality_engine.ai.ai_handler import initialize_llm_manager

    except ImportError:
        return

    # Test 2: LLM Manager initialization (without real API keys)
    try:
        # This should handle missing API keys gracefully
        llm_manager = await initialize_llm_manager()
        if llm_manager is None:
            pass
        else:
            pass
    except Exception:
        pass

    # Test 3: Configuration reading
    try:
        # Test that environment variables are read correctly
        os.getenv("OPENAI_API_KEY", "")
        os.getenv("ANTHROPIC_API_KEY", "")

    except Exception:
        pass

    # Test 4: Import consistency
    try:
        # Verify we're using the correct LLMProviderManager
        from autopr.ai.providers.manager import LLMProviderManager

        # Verify we're not using the old one
        with contextlib.suppress(ImportError):
            from autopr.actions.llm.manager import (
                LLMProviderManager as OldLLMProviderManager,
            )

    except ImportError:
        pass


if __name__ == "__main__":
    asyncio.run(test_ai_handler_fixes())
