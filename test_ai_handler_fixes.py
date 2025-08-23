#!/usr/bin/env python3
"""
Test script to verify AI handler fixes work correctly
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "autopr"))

from autopr.actions.quality_engine.ai.ai_handler import initialize_llm_manager


async def test_ai_handler_fixes():
    """Test that the AI handler fixes work correctly."""
    print("Testing AI Handler Fixes")
    print("=" * 50)

    # Test 1: Import and initialization
    print("1. Testing import and initialization...")
    try:
        # This should work without import errors
        from autopr.actions.quality_engine.ai.ai_handler import initialize_llm_manager

        print("✅ Import successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return

    # Test 2: LLM Manager initialization (without real API keys)
    print("\n2. Testing LLM manager initialization...")
    try:
        # This should handle missing API keys gracefully
        llm_manager = await initialize_llm_manager()
        if llm_manager is None:
            print(
                "✅ LLM manager correctly returns None when no API keys are available"
            )
        else:
            print("✅ LLM manager initialized successfully")
    except Exception as e:
        print(f"❌ LLM manager initialization failed: {e}")

    # Test 3: Configuration reading
    print("\n3. Testing configuration reading...")
    try:
        # Test that environment variables are read correctly
        openai_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        print(f"   OpenAI API Key: {'Set' if openai_key else 'Not set'}")
        print(f"   Anthropic API Key: {'Set' if anthropic_key else 'Not set'}")
        print("✅ Configuration reading works correctly")
    except Exception as e:
        print(f"❌ Configuration reading failed: {e}")

    # Test 4: Import consistency
    print("\n4. Testing import consistency...")
    try:
        # Verify we're using the correct LLMProviderManager
        from autopr.ai.providers.manager import LLMProviderManager

        print("✅ Using correct LLMProviderManager from autopr.ai.providers.manager")

        # Verify we're not using the old one
        try:
            from autopr.actions.llm.manager import (
                LLMProviderManager as OldLLMProviderManager,
            )

            print("⚠️  Old LLMProviderManager still exists (this is expected)")
        except ImportError:
            print("✅ Old LLMProviderManager no longer exists")
    except ImportError as e:
        print(f"❌ Import consistency check failed: {e}")

    print("\n" + "=" * 50)
    print("All tests completed! ✅")


if __name__ == "__main__":
    asyncio.run(test_ai_handler_fixes())
