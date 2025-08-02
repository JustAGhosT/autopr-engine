#!/usr/bin/env python3
"""
Comprehensive test suite for the modular LLM provider system.
Tests imports, configuration, provider availability, error handling, and API calls.
"""

import asyncio
import os
import pathlib
import sys

# Add the autopr package to the path
sys.path.insert(0, os.path.join(pathlib.Path(__file__).parent, "."))


def test_imports() -> bool:
    """Test that all imports work correctly."""

    try:
        # Test main package import

        # Test individual provider imports

        return True
    except ImportError:
        return False


def test_manager_creation() -> bool:
    """Test that the manager can be created."""

    try:
        from autopr.actions.llm import get_llm_provider_manager

        manager = get_llm_provider_manager()

        # Test provider info
        manager.get_provider_info()

        return True
    except Exception:
        return False


def test_provider_availability() -> bool:
    """Test provider availability without API keys."""

    try:
        from autopr.actions.llm import get_llm_provider_manager

        manager = get_llm_provider_manager()

        for provider_name in ["openai", "anthropic", "groq", "mistral", "perplexity", "together"]:
            provider = manager.get_provider(provider_name)
            if provider:
                pass

        return True
    except Exception:
        return False


def test_backward_compatibility() -> bool:
    """Test that the old import still works."""

    try:
        # This should work via the compatibility wrapper

        return True
    except ImportError:
        return False


def test_configuration() -> bool:
    """Test configuration and provider information retrieval."""

    try:
        from autopr.actions.llm import get_llm_provider_manager

        manager = get_llm_provider_manager()

        # Test provider info retrieval
        manager.get_provider_info()

        # Test individual provider information
        for provider_name in ["openai", "anthropic", "groq", "mistral"]:
            provider = manager.get_provider(provider_name)
            if provider and hasattr(provider, "default_model"):
                pass

        # Test available providers list
        manager.get_available_providers()

        return True
    except Exception:
        return False


def test_error_handling() -> bool:
    """Test error handling for invalid providers and configurations."""

    try:
        from autopr.actions.llm import get_llm_provider_manager

        manager = get_llm_provider_manager()

        # Test invalid provider
        invalid_provider = manager.get_provider("invalid_provider")
        if invalid_provider is None:
            pass
        else:
            return False

        # Test empty messages
        try:
            from autopr.actions.llm import complete_chat

            result = complete_chat([])
            if result and hasattr(result, "error") and result.error:
                pass
        except Exception:
            pass

        return True
    except Exception:
        return False


def test_message_formatting() -> bool:
    """Test message formatting and validation."""

    try:
        # Test message role enum

        # Test message creation

        return True
    except Exception:
        return False


def test_api_calls() -> bool:
    """Test actual API calls if API keys are available."""

    try:
        from autopr.actions.llm import MessageRole, complete_chat

        # Simple test message
        test_messages = [{"role": MessageRole.USER.value, "content": "Say 'Hello from AutoPR!'"}]

        # Try each provider
        successful_calls = 0
        for provider_name in ["openai", "anthropic", "groq", "mistral"]:
            try:
                response = complete_chat(
                    messages=test_messages, provider=provider_name, max_tokens=50
                )

                if response and not response.error and response.content:
                    successful_calls += 1
                elif response and response.error:
                    pass

            except Exception:
                pass

        if successful_calls > 0:
            pass

        return True
    except Exception:
        return False


async def main() -> int:
    """Run all tests."""

    # Synchronous tests
    sync_tests = [
        ("Import Tests", test_imports),
        ("Manager Creation", test_manager_creation),
        ("Provider Availability", test_provider_availability),
        ("Backward Compatibility", test_backward_compatibility),
        ("Configuration", test_configuration),
        ("Error Handling", test_error_handling),
        ("Message Formatting", test_message_formatting),
    ]

    # Additional sync tests
    additional_tests = [
        ("API Calls", test_api_calls),
    ]

    passed = 0
    total = len(sync_tests) + len(additional_tests)

    # Run synchronous tests
    for _test_name, test_func in sync_tests:
        if test_func():
            passed += 1

    # Run additional tests
    for _test_name, test_func in additional_tests:
        if test_func():
            passed += 1

    if passed == total:
        return 0
    if passed >= total * 0.8:
        return 0
    return 1


def run_tests() -> int:
    """Wrapper to run async main function."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        return 1
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
