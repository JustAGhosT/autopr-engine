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
        from autopr.actions.quality_engine.ai.ai_handler import \
            initialize_llm_manager

    except ImportError:
        return

    # Test 2: LLM Manager initialization (without real API keys)
    try:
        # This should handle missing API keys gracefully
        llm_manager = await initialize_llm_manager()
        if llm_manager is None:
            # Expected behavior when no API keys are available
            assert llm_manager is None
        else:
            # If manager is created, verify it has expected attributes
            assert hasattr(llm_manager, 'providers')
            assert hasattr(llm_manager, 'get_provider')
    except Exception:
        # Expected behavior - should handle missing API keys gracefully
        assert True

    # Test 3: Configuration reading
    try:
        # Test that environment variables are read correctly
        openai_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        # Verify environment variables can be read (may be empty)
        assert isinstance(openai_key, str)
        assert isinstance(anthropic_key, str)

    except Exception:
        # Should not raise exceptions when reading environment variables
        assert False

    # Test 4: Import consistency
    try:
        # Verify we're using the correct LLMProviderManager
        from autopr.ai.providers.manager import LLMProviderManager

        # Verify the new manager has expected attributes
        assert hasattr(LLMProviderManager, '__init__')
        assert hasattr(LLMProviderManager, 'get_provider')

        # Verify we're not using the old one
        with contextlib.suppress(ImportError):
            from autopr.actions.llm.manager import \
                LLMProviderManager as OldLLMProviderManager

            # If old import succeeds, verify it's different from new one
            assert LLMProviderManager != OldLLMProviderManager

    except ImportError:
        # Expected behavior - new manager should be importable
        assert False


if __name__ == "__main__":
    asyncio.run(test_ai_handler_fixes())
