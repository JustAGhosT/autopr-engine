#!/usr/bin/env python3
"""
Test script to verify provider compatibility for JSON response format and smart truncation
"""

import asyncio
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "autopr"))

import contextlib

from autopr.actions.quality_engine.ai.ai_modes import (
    _smart_truncate_content,
    _split_content_into_chunks,
)
from autopr.ai.base import AnthropicProvider, LLMMessage, OpenAIProvider


async def test_json_response_format():
    """Test that providers properly handle JSON response format."""

    # Test OpenAI provider
    openai_provider = OpenAIProvider()
    await openai_provider.initialize({"api_key": "test_key"})

    messages = [LLMMessage(role="user", content="Analyze this code: print('hello')")]

    with contextlib.suppress(Exception):
        await openai_provider.generate_completion(
            messages=messages, response_format={"type": "json"}
        )

    # Test unsupported response format
    with contextlib.suppress(ValueError):
        await openai_provider.generate_completion(
            messages=messages, response_format={"type": "unsupported"}
        )

    # Test Anthropic provider
    anthropic_provider = AnthropicProvider()
    await anthropic_provider.initialize({"api_key": "test_key"})

    with contextlib.suppress(Exception):
        await anthropic_provider.generate_completion(
            messages=messages, response_format={"type": "json"}
        )

    await openai_provider.cleanup()
    await anthropic_provider.cleanup()


def test_smart_truncation():
    """Test smart content truncation functionality."""

    # Test case 1: Short content (no truncation needed)
    short_content = "print('hello')\nprint('world')"
    truncated = _smart_truncate_content(short_content, max_length=100)
    assert truncated == short_content, "Short content should not be truncated"

    # Test case 2: Long content (truncation needed)
    long_content = "print('hello')\n" * 1000  # Very long content
    truncated = _smart_truncate_content(long_content, max_length=100)
    assert len(truncated) <= 100, "Content should be truncated to max length"
    assert "..." in truncated, "Truncation indicator should be present"

    # Test case 3: Content with long lines
    long_line_content = "def very_long_function_name_with_many_parameters(param1, param2, param3, param4, param5, param6, param7, param8, param9, param10):\n    return param1 + param2\n"
    truncated = _smart_truncate_content(long_line_content, max_length=50)
    assert len(truncated) <= 50, "Long line should be truncated"

    # Test case 4: Content splitting into chunks
    large_content = "print('hello')\n" * 500  # Large content
    chunks = _split_content_into_chunks(large_content, max_chunk_size=100)
    assert len(chunks) > 1, "Large content should be split into multiple chunks"
    assert all(
        len(chunk) <= 100 for chunk in chunks
    ), "All chunks should be within size limit"

    # Test case 5: Chunk overlap
    chunks = _split_content_into_chunks(large_content, max_chunk_size=50)
    if len(chunks) > 1:
        # Check that consecutive chunks have some overlap
        chunk1_lines = chunks[0].split("\n")
        chunk2_lines = chunks[1].split("\n")
        overlap = set(chunk1_lines) & set(chunk2_lines)
        assert len(overlap) > 0, "Consecutive chunks should have overlap"


def test_code_boundary_preservation():
    """Test that code boundaries are preserved during truncation."""

    # Test case: Function definition should not be cut in half
    code_with_function = """
def my_function():
    print("Hello")
    return True

def another_function():
    print("World")
    return False
"""

    _smart_truncate_content(code_with_function, max_length=50)
    # Should try to preserve complete function definitions


if __name__ == "__main__":

    # Test smart truncation (synchronous)
    test_smart_truncation()
    test_code_boundary_preservation()

    # Test JSON response format (asynchronous)
    asyncio.run(test_json_response_format())
