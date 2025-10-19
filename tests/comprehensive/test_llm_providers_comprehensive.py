#!/usr/bin/env python3
"""
Comprehensive tests for LLM providers module.
"""

from unittest.mock import Mock, patch

import pytest


# Import the modules we're testing
try:
    from autopr.actions.llm_providers import (
        AnthropicProvider,
        LLMProvider,
        LocalProvider,
        OpenAIProvider,
        ProviderConfig,
        ProviderManager,
    )
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestProviderConfig:
    """Test ProviderConfig class."""

    def test_provider_config_initialization(self):
        """Test ProviderConfig initialization."""
        config = ProviderConfig(
            provider_name="openai",
            api_key="test_key",
            model_name="gpt-4",
            max_tokens=1000,
            temperature=0.7,
            timeout=30,
            retry_attempts=3
        )

        assert config.provider_name == "openai"
        assert config.api_key == "test_key"
        assert config.model_name == "gpt-4"
        assert config.max_tokens == 1000
        assert config.temperature == 0.7
        assert config.timeout == 30
        assert config.retry_attempts == 3

    def test_provider_config_defaults(self):
        """Test ProviderConfig with default values."""
        config = ProviderConfig(provider_name="test", api_key="key")

        assert config.provider_name == "test"
        assert config.api_key == "key"
        assert config.model_name == "gpt-3.5-turbo"
        assert config.max_tokens == 500
        assert config.temperature == 0.0
        assert config.timeout == 60
        assert config.retry_attempts == 2

    def test_provider_config_to_dict(self):
        """Test ProviderConfig to_dict method."""
        config = ProviderConfig(
            provider_name="anthropic",
            api_key="claude_key",
            model_name="claude-3",
            max_tokens=2000
        )

        result = config.to_dict()
        assert result["provider_name"] == "anthropic"
        assert result["api_key"] == "claude_key"
        assert result["model_name"] == "claude-3"
        assert result["max_tokens"] == 2000

    def test_provider_config_from_dict(self):
        """Test ProviderConfig from_dict method."""
        data = {
            "provider_name": "local",
            "api_key": "local_key",
            "model_name": "llama-2",
            "max_tokens": 1500,
            "temperature": 0.5,
            "timeout": 45,
            "retry_attempts": 4
        }

        config = ProviderConfig.from_dict(data)
        assert config.provider_name == "local"
        assert config.api_key == "local_key"
        assert config.model_name == "llama-2"
        assert config.max_tokens == 1500
        assert config.temperature == 0.5
        assert config.timeout == 45
        assert config.retry_attempts == 4

    def test_provider_config_validation(self):
        """Test ProviderConfig validation."""
        valid_config = ProviderConfig(provider_name="test", api_key="key", max_tokens=1000)
        assert valid_config.is_valid() is True

        invalid_config = ProviderConfig(provider_name="", api_key="", max_tokens=0)
        assert invalid_config.is_valid() is False


class TestLLMProvider:
    """Test LLMProvider base class."""

    @pytest.fixture
    def llm_provider(self):
        """Create a mock LLMProvider instance for testing."""
        config = ProviderConfig(provider_name="test", api_key="test_key")
        return LLMProvider(config)

    def test_llm_provider_initialization(self, llm_provider):
        """Test LLMProvider initialization."""
        assert llm_provider.config is not None
        assert llm_provider.provider_name == "test"

    def test_llm_provider_generate_text(self, llm_provider):
        """Test LLMProvider generate_text method."""
        prompt = "Test prompt"

        # This should raise NotImplementedError for base class
        with pytest.raises(NotImplementedError):
            llm_provider.generate_text(prompt)

    def test_llm_provider_generate_completion(self, llm_provider):
        """Test LLMProvider generate_completion method."""
        prompt = "Complete this sentence:"

        # This should raise NotImplementedError for base class
        with pytest.raises(NotImplementedError):
            llm_provider.generate_completion(prompt)

    def test_llm_provider_validate_config(self, llm_provider):
        """Test LLMProvider validate_config method."""
        result = llm_provider.validate_config()
        assert result.is_valid is True

    def test_llm_provider_get_provider_info(self, llm_provider):
        """Test LLMProvider get_provider_info method."""
        info = llm_provider.get_provider_info()

        assert "provider_name" in info
        assert "model_name" in info
        assert "max_tokens" in info
        assert info["provider_name"] == "test"


class TestOpenAIProvider:
    """Test OpenAIProvider class."""

    @pytest.fixture
    def openai_provider(self):
        """Create an OpenAIProvider instance for testing."""
        config = ProviderConfig(
            provider_name="openai",
            api_key="test_openai_key",
            model_name="gpt-4"
        )
        return OpenAIProvider(config)

    def test_openai_provider_initialization(self, openai_provider):
        """Test OpenAIProvider initialization."""
        assert openai_provider.config.provider_name == "openai"
        assert openai_provider.config.model_name == "gpt-4"

    @patch('autopr.actions.llm_providers.openai')
    def test_openai_provider_generate_text(self, mock_openai, openai_provider):
        """Test OpenAIProvider generate_text method."""
        mock_response = Mock()
        mock_response.choices = [Mock(text="Generated text response")]
        mock_openai.ChatCompletion.create.return_value = mock_response

        prompt = "Test prompt"
        result = openai_provider.generate_text(prompt)

        assert result == "Generated text response"
        mock_openai.ChatCompletion.create.assert_called_once()

    @patch('autopr.actions.llm_providers.openai')
    def test_openai_provider_generate_completion(self, mock_openai, openai_provider):
        """Test OpenAIProvider generate_completion method."""
        mock_response = Mock()
        mock_response.choices = [Mock(text="Completion text")]
        mock_openai.Completion.create.return_value = mock_response

        prompt = "Complete this:"
        result = openai_provider.generate_completion(prompt)

        assert result == "Completion text"
        mock_openai.Completion.create.assert_called_once()

    def test_openai_provider_validate_config(self, openai_provider):
        """Test OpenAIProvider validate_config method."""
        result = openai_provider.validate_config()
        assert result.is_valid is True

    def test_openai_provider_get_available_models(self, openai_provider):
        """Test OpenAIProvider get_available_models method."""
        models = openai_provider.get_available_models()

        assert isinstance(models, list)
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models


class TestAnthropicProvider:
    """Test AnthropicProvider class."""

    @pytest.fixture
    def anthropic_provider(self):
        """Create an AnthropicProvider instance for testing."""
        config = ProviderConfig(
            provider_name="anthropic",
            api_key="test_anthropic_key",
            model_name="claude-3"
        )
        return AnthropicProvider(config)

    def test_anthropic_provider_initialization(self, anthropic_provider):
        """Test AnthropicProvider initialization."""
        assert anthropic_provider.config.provider_name == "anthropic"
        assert anthropic_provider.config.model_name == "claude-3"

    @patch('autopr.actions.llm_providers.anthropic')
    def test_anthropic_provider_generate_text(self, mock_anthropic, anthropic_provider):
        """Test AnthropicProvider generate_text method."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Claude generated text")]
        mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_response

        prompt = "Test prompt"
        result = anthropic_provider.generate_text(prompt)

        assert result == "Claude generated text"
        mock_anthropic.Anthropic.return_value.messages.create.assert_called_once()

    @patch('autopr.actions.llm_providers.anthropic')
    def test_anthropic_provider_generate_completion(self, mock_anthropic, anthropic_provider):
        """Test AnthropicProvider generate_completion method."""
        mock_response = Mock()
        mock_response.completion = "Claude completion"
        mock_anthropic.Anthropic.return_value.completions.create.return_value = mock_response

        prompt = "Complete this:"
        result = anthropic_provider.generate_completion(prompt)

        assert result == "Claude completion"
        mock_anthropic.Anthropic.return_value.completions.create.assert_called_once()

    def test_anthropic_provider_validate_config(self, anthropic_provider):
        """Test AnthropicProvider validate_config method."""
        result = anthropic_provider.validate_config()
        assert result.is_valid is True

    def test_anthropic_provider_get_available_models(self, anthropic_provider):
        """Test AnthropicProvider get_available_models method."""
        models = anthropic_provider.get_available_models()

        assert isinstance(models, list)
        assert "claude-3" in models
        assert "claude-2" in models


class TestLocalProvider:
    """Test LocalProvider class."""

    @pytest.fixture
    def local_provider(self):
        """Create a LocalProvider instance for testing."""
        config = ProviderConfig(
            provider_name="local",
            api_key="local_key",
            model_name="llama-2"
        )
        return LocalProvider(config)

    def test_local_provider_initialization(self, local_provider):
        """Test LocalProvider initialization."""
        assert local_provider.config.provider_name == "local"
        assert local_provider.config.model_name == "llama-2"

    @patch('autopr.actions.llm_providers.requests')
    def test_local_provider_generate_text(self, mock_requests, local_provider):
        """Test LocalProvider generate_text method."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Local generated text"}
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        prompt = "Test prompt"
        result = local_provider.generate_text(prompt)

        assert result == "Local generated text"
        mock_requests.post.assert_called_once()

    @patch('autopr.actions.llm_providers.requests')
    def test_local_provider_generate_completion(self, mock_requests, local_provider):
        """Test LocalProvider generate_completion method."""
        mock_response = Mock()
        mock_response.json.return_value = {"completion": "Local completion"}
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        prompt = "Complete this:"
        result = local_provider.generate_completion(prompt)

        assert result == "Local completion"
        mock_requests.post.assert_called_once()

    def test_local_provider_validate_config(self, local_provider):
        """Test LocalProvider validate_config method."""
        result = local_provider.validate_config()
        assert result.is_valid is True

    def test_local_provider_get_available_models(self, local_provider):
        """Test LocalProvider get_available_models method."""
        models = local_provider.get_available_models()

        assert isinstance(models, list)
        assert "llama-2" in models
        assert "gpt4all" in models


class TestProviderManager:
    """Test ProviderManager class."""

    @pytest.fixture
    def provider_manager(self):
        """Create a ProviderManager instance for testing."""
        return ProviderManager()

    def test_provider_manager_initialization(self, provider_manager):
        """Test ProviderManager initialization."""
        assert provider_manager.providers == {}
        assert provider_manager.default_provider is None

    def test_register_provider(self, provider_manager):
        """Test registering a provider."""
        config = ProviderConfig(provider_name="test", api_key="test_key")
        provider = Mock(spec=LLMProvider)
        provider.config = config

        provider_manager.register_provider("test_provider", provider)
        assert "test_provider" in provider_manager.providers
        assert provider_manager.providers["test_provider"] == provider

    def test_get_provider(self, provider_manager):
        """Test getting a provider."""
        config = ProviderConfig(provider_name="test", api_key="test_key")
        provider = Mock(spec=LLMProvider)
        provider.config = config

        provider_manager.register_provider("test_provider", provider)
        retrieved_provider = provider_manager.get_provider("test_provider")

        assert retrieved_provider == provider

    def test_get_provider_not_found(self, provider_manager):
        """Test getting a non-existent provider."""
        provider = provider_manager.get_provider("non_existent")
        assert provider is None

    def test_list_providers(self, provider_manager):
        """Test listing all providers."""
        # Register some providers
        for i in range(3):
            config = ProviderConfig(provider_name=f"test_{i}", api_key=f"key_{i}")
            provider = Mock(spec=LLMProvider)
            provider.config = config
            provider_manager.register_provider(f"provider_{i}", provider)

        providers = provider_manager.list_providers()
        assert len(providers) == 3
        assert "provider_0" in providers
        assert "provider_1" in providers
        assert "provider_2" in providers

    def test_set_default_provider(self, provider_manager):
        """Test setting the default provider."""
        config = ProviderConfig(provider_name="test", api_key="test_key")
        provider = Mock(spec=LLMProvider)
        provider.config = config

        provider_manager.register_provider("test_provider", provider)
        provider_manager.set_default_provider("test_provider")

        assert provider_manager.default_provider == "test_provider"

    def test_get_default_provider(self, provider_manager):
        """Test getting the default provider."""
        config = ProviderConfig(provider_name="test", api_key="test_key")
        provider = Mock(spec=LLMProvider)
        provider.config = config

        provider_manager.register_provider("test_provider", provider)
        provider_manager.set_default_provider("test_provider")

        default_provider = provider_manager.get_default_provider()
        assert default_provider == provider

    def test_generate_text_with_default_provider(self, provider_manager):
        """Test generating text with default provider."""
        config = ProviderConfig(provider_name="test", api_key="test_key")
        provider = Mock(spec=LLMProvider)
        provider.config = config
        provider.generate_text.return_value = "Generated text"

        provider_manager.register_provider("test_provider", provider)
        provider_manager.set_default_provider("test_provider")

        result = provider_manager.generate_text("Test prompt")
        assert result == "Generated text"
        provider.generate_text.assert_called_once_with("Test prompt")

    def test_generate_text_with_specific_provider(self, provider_manager):
        """Test generating text with specific provider."""
        config = ProviderConfig(provider_name="test", api_key="test_key")
        provider = Mock(spec=LLMProvider)
        provider.config = config
        provider.generate_text.return_value = "Generated text"

        provider_manager.register_provider("test_provider", provider)

        result = provider_manager.generate_text("Test prompt", provider_name="test_provider")
        assert result == "Generated text"
        provider.generate_text.assert_called_once_with("Test prompt")

    def test_remove_provider(self, provider_manager):
        """Test removing a provider."""
        config = ProviderConfig(provider_name="test", api_key="test_key")
        provider = Mock(spec=LLMProvider)
        provider.config = config

        provider_manager.register_provider("test_provider", provider)
        assert "test_provider" in provider_manager.providers

        provider_manager.remove_provider("test_provider")
        assert "test_provider" not in provider_manager.providers

    def test_get_provider_statistics(self, provider_manager):
        """Test getting provider statistics."""
        # Register some providers
        for i in range(2):
            config = ProviderConfig(provider_name=f"test_{i}", api_key=f"key_{i}")
            provider = Mock(spec=LLMProvider)
            provider.config = config
            provider_manager.register_provider(f"provider_{i}", provider)

        stats = provider_manager.get_provider_statistics()

        assert "total_providers" in stats
        assert "default_provider" in stats
        assert "provider_names" in stats
        assert stats["total_providers"] == 2
        assert "provider_0" in stats["provider_names"]
        assert "provider_1" in stats["provider_names"]
