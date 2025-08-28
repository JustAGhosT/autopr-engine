#!/usr/bin/env python3
"""
Comprehensive tests for LLM manager module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the modules we're testing
try:
    from autopr.actions.llm_manager import (LLMCache, LLMConfig, LLMManager,
                                            LLMProvider, LLMRequest,
                                            LLMResponse)
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestLLMConfig:
    """Test LLMConfig class."""

    def test_llm_config_initialization(self):
        """Test LLMConfig initialization."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test_key",
            max_tokens=1000,
            temperature=0.7,
            timeout=30
        )
        
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == "test_key"
        assert config.max_tokens == 1000
        assert config.temperature == 0.7
        assert config.timeout == 30

    def test_llm_config_defaults(self):
        """Test LLMConfig with default values."""
        config = LLMConfig(provider="test", api_key="key")
        
        assert config.provider == "test"
        assert config.api_key == "key"
        assert config.model == "gpt-3.5-turbo"
        assert config.max_tokens == 500
        assert config.temperature == 0.0
        assert config.timeout == 60

    def test_llm_config_to_dict(self):
        """Test LLMConfig to_dict method."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3",
            api_key="claude_key",
            max_tokens=2000
        )
        
        result = config.to_dict()
        assert result["provider"] == "anthropic"
        assert result["model"] == "claude-3"
        assert result["api_key"] == "claude_key"
        assert result["max_tokens"] == 2000

    def test_llm_config_from_dict(self):
        """Test LLMConfig from_dict method."""
        data = {
            "provider": "local",
            "model": "llama-2",
            "api_key": "local_key",
            "max_tokens": 1500,
            "temperature": 0.5,
            "timeout": 45
        }
        
        config = LLMConfig.from_dict(data)
        assert config.provider == "local"
        assert config.model == "llama-2"
        assert config.api_key == "local_key"
        assert config.max_tokens == 1500
        assert config.temperature == 0.5
        assert config.timeout == 45


class TestLLMRequest:
    """Test LLMRequest class."""

    def test_llm_request_initialization(self):
        """Test LLMRequest initialization."""
        request = LLMRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=1000,
            temperature=0.7
        )
        
        assert request.prompt == "Test prompt"
        assert request.model == "gpt-4"
        assert request.max_tokens == 1000
        assert request.temperature == 0.7

    def test_llm_request_defaults(self):
        """Test LLMRequest with default values."""
        request = LLMRequest(prompt="Test")
        
        assert request.prompt == "Test"
        assert request.model == "gpt-3.5-turbo"
        assert request.max_tokens == 500
        assert request.temperature == 0.0

    def test_llm_request_to_dict(self):
        """Test LLMRequest to_dict method."""
        request = LLMRequest(
            prompt="Generate text",
            model="claude-3",
            max_tokens=2000,
            temperature=0.8
        )
        
        result = request.to_dict()
        assert result["prompt"] == "Generate text"
        assert result["model"] == "claude-3"
        assert result["max_tokens"] == 2000
        assert result["temperature"] == 0.8

    def test_llm_request_from_dict(self):
        """Test LLMRequest from_dict method."""
        data = {
            "prompt": "Complete this",
            "model": "llama-2",
            "max_tokens": 1500,
            "temperature": 0.6
        }
        
        request = LLMRequest.from_dict(data)
        assert request.prompt == "Complete this"
        assert request.model == "llama-2"
        assert request.max_tokens == 1500
        assert request.temperature == 0.6


class TestLLMResponse:
    """Test LLMResponse class."""

    def test_llm_response_initialization(self):
        """Test LLMResponse initialization."""
        response = LLMResponse(
            text="Generated response",
            model="gpt-4",
            usage={"tokens": 100},
            finish_reason="stop"
        )
        
        assert response.text == "Generated response"
        assert response.model == "gpt-4"
        assert response.usage == {"tokens": 100}
        assert response.finish_reason == "stop"

    def test_llm_response_defaults(self):
        """Test LLMResponse with default values."""
        response = LLMResponse(text="Test response")
        
        assert response.text == "Test response"
        assert response.model == "unknown"
        assert response.usage == {}
        assert response.finish_reason == "unknown"

    def test_llm_response_to_dict(self):
        """Test LLMResponse to_dict method."""
        response = LLMResponse(
            text="Claude response",
            model="claude-3",
            usage={"tokens": 200},
            finish_reason="length"
        )
        
        result = response.to_dict()
        assert result["text"] == "Claude response"
        assert result["model"] == "claude-3"
        assert result["usage"] == {"tokens": 200}
        assert result["finish_reason"] == "length"

    def test_llm_response_from_dict(self):
        """Test LLMResponse from_dict method."""
        data = {
            "text": "Local response",
            "model": "llama-2",
            "usage": {"tokens": 150},
            "finish_reason": "stop"
        }
        
        response = LLMResponse.from_dict(data)
        assert response.text == "Local response"
        assert response.model == "llama-2"
        assert response.usage == {"tokens": 150}
        assert response.finish_reason == "stop"


class TestLLMProvider:
    """Test LLMProvider class."""

    @pytest.fixture
    def llm_provider(self):
        """Create a mock LLMProvider instance for testing."""
        config = LLMConfig(provider="test", api_key="test_key")
        return LLMProvider(config)

    def test_llm_provider_initialization(self, llm_provider):
        """Test LLMProvider initialization."""
        assert llm_provider.config is not None
        assert llm_provider.config.provider == "test"

    def test_llm_provider_generate(self, llm_provider):
        """Test LLMProvider generate method."""
        request = LLMRequest(prompt="Test prompt")
        
        # This should raise NotImplementedError for base class
        with pytest.raises(NotImplementedError):
            llm_provider.generate(request)

    def test_llm_provider_validate_request(self, llm_provider):
        """Test LLMProvider validate_request method."""
        request = LLMRequest(prompt="Valid prompt")
        result = llm_provider.validate_request(request)
        assert result.is_valid is True
        
        invalid_request = LLMRequest(prompt="")
        result = llm_provider.validate_request(invalid_request)
        assert result.is_valid is False


class TestLLMCache:
    """Test LLMCache class."""

    @pytest.fixture
    def llm_cache(self):
        """Create an LLMCache instance for testing."""
        return LLMCache(max_size=100)

    def test_llm_cache_initialization(self, llm_cache):
        """Test LLMCache initialization."""
        assert llm_cache.max_size == 100
        assert llm_cache.cache == {}

    def test_llm_cache_get(self, llm_cache):
        """Test LLMCache get method."""
        request = LLMRequest(prompt="Test prompt")
        response = LLMResponse(text="Cached response")
        
        # Add to cache
        llm_cache.set(request, response)
        
        # Get from cache
        cached_response = llm_cache.get(request)
        assert cached_response is not None
        assert cached_response.text == "Cached response"

    def test_llm_cache_get_miss(self, llm_cache):
        """Test LLMCache get method with cache miss."""
        request = LLMRequest(prompt="Not cached")
        
        cached_response = llm_cache.get(request)
        assert cached_response is None

    def test_llm_cache_set(self, llm_cache):
        """Test LLMCache set method."""
        request = LLMRequest(prompt="Test prompt")
        response = LLMResponse(text="Test response")
        
        llm_cache.set(request, response)
        assert len(llm_cache.cache) == 1

    def test_llm_cache_clear(self, llm_cache):
        """Test LLMCache clear method."""
        request = LLMRequest(prompt="Test prompt")
        response = LLMResponse(text="Test response")
        
        llm_cache.set(request, response)
        assert len(llm_cache.cache) == 1
        
        llm_cache.clear()
        assert len(llm_cache.cache) == 0

    def test_llm_cache_size_limit(self, llm_cache):
        """Test LLMCache size limit enforcement."""
        # Add more items than max_size
        for i in range(110):
            request = LLMRequest(prompt=f"Prompt {i}")
            response = LLMResponse(text=f"Response {i}")
            llm_cache.set(request, response)
        
        # Should not exceed max_size
        assert len(llm_cache.cache) <= llm_cache.max_size


class TestLLMManager:
    """Test LLMManager class."""

    @pytest.fixture
    def llm_manager(self):
        """Create an LLMManager instance for testing."""
        config = LLMConfig(provider="test", api_key="test_key")
        return LLMManager(config)

    def test_llm_manager_initialization(self, llm_manager):
        """Test LLMManager initialization."""
        assert llm_manager.config is not None
        assert llm_manager.provider is not None
        assert llm_manager.cache is not None

    def test_llm_manager_generate_text(self, llm_manager):
        """Test LLMManager generate_text method."""
        prompt = "Test prompt"
        
        with patch.object(llm_manager.provider, 'generate') as mock_generate:
            mock_response = LLMResponse(text="Generated text")
            mock_generate.return_value = mock_response
            
            result = llm_manager.generate_text(prompt)
            
            assert result == "Generated text"
            mock_generate.assert_called_once()

    def test_llm_manager_generate_with_cache(self, llm_manager):
        """Test LLMManager generate with caching."""
        prompt = "Cached prompt"
        request = LLMRequest(prompt=prompt)
        response = LLMResponse(text="Cached response")
        
        # Add to cache first
        llm_manager.cache.set(request, response)
        
        # Generate should use cache
        result = llm_manager.generate_text(prompt)
        assert result == "Cached response"

    def test_llm_manager_generate_without_cache(self, llm_manager):
        """Test LLMManager generate without cache."""
        prompt = "Uncached prompt"
        
        with patch.object(llm_manager.provider, 'generate') as mock_generate:
            mock_response = LLMResponse(text="Fresh response")
            mock_generate.return_value = mock_response
            
            result = llm_manager.generate_text(prompt, use_cache=False)
            
            assert result == "Fresh response"
            mock_generate.assert_called_once()

    def test_llm_manager_validate_config(self, llm_manager):
        """Test LLMManager validate_config method."""
        result = llm_manager.validate_config()
        assert result.is_valid is True

    def test_llm_manager_get_cache_stats(self, llm_manager):
        """Test LLMManager get_cache_stats method."""
        # Add some items to cache
        for i in range(3):
            request = LLMRequest(prompt=f"Prompt {i}")
            response = LLMResponse(text=f"Response {i}")
            llm_manager.cache.set(request, response)
        
        stats = llm_manager.get_cache_stats()
        
        assert "cache_size" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert stats["cache_size"] == 3

    def test_llm_manager_clear_cache(self, llm_manager):
        """Test LLMManager clear_cache method."""
        # Add some items to cache
        request = LLMRequest(prompt="Test prompt")
        response = LLMResponse(text="Test response")
        llm_manager.cache.set(request, response)
        
        assert len(llm_manager.cache.cache) == 1
        
        llm_manager.clear_cache()
        assert len(llm_manager.cache.cache) == 0
