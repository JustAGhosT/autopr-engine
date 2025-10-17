"""
Unit tests for code review changes.

Tests for bug fixes, refactorings, and enhancements implemented in the comprehensive code review.
"""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

# Test Bug Fix #1: IntegrationRegistry Import
def test_integration_registry_import():
    """Test that IntegrationRegistry can be imported from engine module."""
    from autopr.engine import AutoPREngine
    from autopr.integrations.registry import IntegrationRegistry
    
    # Should not raise ImportError
    assert IntegrationRegistry is not None


# Test Bug Fix #4: AutoPRPermissionError
def test_permission_error_renamed():
    """Test that AutoPRPermissionError exists and doesn't shadow built-in."""
    from autopr.exceptions import AutoPRPermissionError
    
    # Custom exception should exist
    assert AutoPRPermissionError is not None
    
    # Built-in PermissionError should still be accessible
    assert PermissionError is not None
    
    # They should be different classes
    assert AutoPRPermissionError is not PermissionError


# Test Bug Fix #5: Type conversions in get_provider_config
def test_provider_config_types():
    """Test that get_provider_config returns proper types."""
    from autopr.config.settings import AutoPRSettings, LLMProvider
    
    settings = AutoPRSettings()
    config = settings.get_provider_config(LLMProvider.OPENAI)
    
    # Verify types are preserved (not converted to strings)
    assert isinstance(config.get("max_tokens"), int), "max_tokens should be int"
    assert isinstance(config.get("temperature"), float), "temperature should be float"
    assert isinstance(config.get("timeout"), int), "timeout should be int"
    assert isinstance(config.get("max_retries"), int), "max_retries should be int"


# Test Refactoring #2: Provider configuration consolidation
def test_get_provider_specific_config():
    """Test the new _get_provider_specific_config helper method."""
    from autopr.config.settings import AutoPRSettings, LLMProvider
    
    settings = AutoPRSettings()
    
    # Test that the helper method works for different providers
    openai_config = settings._get_provider_specific_config(LLMProvider.OPENAI)
    assert "api_key" in openai_config
    assert "base_url" in openai_config
    assert "default_model" in openai_config
    
    anthropic_config = settings._get_provider_specific_config(LLMProvider.ANTHROPIC)
    assert "api_key" in anthropic_config
    assert "base_url" in anthropic_config
    assert "default_model" in anthropic_config


# Test Refactoring #3: Split initialization helpers
def test_get_config_file_paths():
    """Test _get_config_file_paths helper method."""
    from autopr.config.settings import AutoPRSettings
    
    settings = AutoPRSettings()
    paths = settings._get_config_file_paths()
    
    # Should return a list of Path objects
    assert isinstance(paths, list)
    assert len(paths) > 0
    assert all(isinstance(p, Path) for p in paths)
    
    # Should include expected paths
    path_strs = [str(p) for p in paths]
    assert any("autopr.yaml" in p for p in path_strs)
    assert any("autopr.yml" in p for p in path_strs)


def test_load_yaml_config():
    """Test _load_yaml_config helper method."""
    from autopr.config.settings import AutoPRSettings
    import tempfile
    import yaml
    
    settings = AutoPRSettings()
    
    # Test with valid YAML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({"test_key": "test_value"}, f)
        temp_path = Path(f.name)
    
    try:
        result = settings._load_yaml_config(temp_path)
        assert result is not None
        assert result.get("test_key") == "test_value"
    finally:
        temp_path.unlink()
    
    # Test with non-existent file
    non_existent = Path("/tmp/non_existent_config.yaml")
    result = settings._load_yaml_config(non_existent)
    assert result is None


# Test Refactoring #4: Magic numbers extraction
def test_max_workflow_history_constant():
    """Test that MAX_WORKFLOW_HISTORY constant is defined."""
    from autopr.workflows.engine import MAX_WORKFLOW_HISTORY
    
    assert MAX_WORKFLOW_HISTORY == 1000
    assert isinstance(MAX_WORKFLOW_HISTORY, int)


# Test Refactoring #5: Standardized error handling
def test_handle_operation_error():
    """Test handle_operation_error helper function."""
    from autopr.engine import handle_operation_error
    from autopr.exceptions import AutoPRException
    
    test_exception = ValueError("Test error")
    
    # Test that it raises the correct exception type
    with pytest.raises(AutoPRException) as exc_info:
        handle_operation_error("test_operation", test_exception)
    
    assert "test_operation failed" in str(exc_info.value)
    assert "Test error" in str(exc_info.value)


def test_handle_workflow_error():
    """Test handle_workflow_error helper function."""
    from autopr.workflows.engine import handle_workflow_error
    from autopr.exceptions import WorkflowError
    
    test_exception = ValueError("Test workflow error")
    
    # Test that it raises the correct exception type
    with pytest.raises(WorkflowError) as exc_info:
        handle_workflow_error("test_workflow", "execution", test_exception)
    
    assert "Workflow execution failed" in str(exc_info.value)


# Test Enhancement #1: LRU caching for Action Registry
def test_action_registry_caching():
    """Test that action instances are cached."""
    from autopr.actions.registry import ActionRegistry
    
    registry = ActionRegistry()
    
    # Register a test action
    from autopr.actions.base.action import Action
    
    class TestAction(Action):
        def __init__(self, name, description):
            super().__init__(name, description)
    
    registry.register("test_action", TestAction)
    
    # Get the action twice
    action1 = registry.get_action("test_action")
    action2 = registry.get_action("test_action")
    
    # Should return the same cached instance
    assert action1 is action2


def test_create_action_instance_helper():
    """Test _create_action_instance helper method."""
    from autopr.actions.registry import ActionRegistry
    from autopr.actions.base.action import Action
    
    registry = ActionRegistry()
    
    class TestAction(Action):
        def __init__(self, name, description):
            super().__init__(name, description)
        
        async def execute(self, context):
            return {"success": True}
        
        def validate_inputs(self, context):
            return True
    
    registry.register("test_action", TestAction)
    
    # First, verify action is registered
    assert "test_action" in registry._actions
    
    # Test the helper creates instances
    instance = registry._create_action_instance("test_action")
    assert instance is not None, "Instance should not be None"
    assert instance.name == "test_action", f"Expected 'test_action', got '{instance.name}'"


# Test Enhancement #2: Async context manager
@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager support for AutoPREngine."""
    from autopr.engine import AutoPREngine
    from autopr.config import AutoPRConfig
    
    config = AutoPRConfig()
    config.github_token = "test_token"
    config.openai_api_key = "test_key"
    
    engine = AutoPREngine(config)
    
    # Mock the methods on the instance
    with patch.object(engine, 'start', new_callable=AsyncMock) as mock_start, \
         patch.object(engine, 'stop', new_callable=AsyncMock) as mock_stop:
        
        async with engine as eng:
            assert eng is engine
            mock_start.assert_called_once()
        
        # Stop should be called when exiting context
        mock_stop.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_manager_aenter():
    """Test __aenter__ method."""
    from autopr.engine import AutoPREngine
    from autopr.config import AutoPRConfig
    
    config = AutoPRConfig()
    engine = AutoPREngine(config)
    
    with patch.object(engine, 'start', new_callable=AsyncMock) as mock_start:
        result = await engine.__aenter__()
        assert result is engine
        mock_start.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_manager_aexit():
    """Test __aexit__ method."""
    from autopr.engine import AutoPREngine
    from autopr.config import AutoPRConfig
    
    config = AutoPRConfig()
    engine = AutoPREngine(config)
    
    with patch.object(engine, 'stop', new_callable=AsyncMock) as mock_stop:
        await engine.__aexit__(None, None, None)
        mock_stop.assert_called_once()


# Test Enhancement #3: Workflow execution metrics
def test_workflow_metrics_initialization():
    """Test that workflow metrics are properly initialized."""
    from autopr.workflows.engine import WorkflowEngine
    from autopr.config import AutoPRConfig
    
    config = AutoPRConfig()
    engine = WorkflowEngine(config)
    
    # Verify metrics dictionary is initialized
    assert hasattr(engine, 'metrics')
    assert isinstance(engine.metrics, dict)
    assert "total_executions" in engine.metrics
    assert "successful_executions" in engine.metrics
    assert "failed_executions" in engine.metrics
    assert "timeout_executions" in engine.metrics
    assert "total_execution_time" in engine.metrics
    assert "average_execution_time" in engine.metrics


def test_update_metrics():
    """Test _update_metrics method."""
    from autopr.workflows.engine import WorkflowEngine
    from autopr.config import AutoPRConfig
    
    config = AutoPRConfig()
    engine = WorkflowEngine(config)
    
    # Test updating metrics for success
    engine._update_metrics("success", 1.5)
    assert engine.metrics["total_executions"] == 1
    assert engine.metrics["successful_executions"] == 1
    assert engine.metrics["failed_executions"] == 0
    assert engine.metrics["total_execution_time"] == 1.5
    assert engine.metrics["average_execution_time"] == 1.5
    
    # Test updating metrics for failure
    engine._update_metrics("failed", 2.0)
    assert engine.metrics["total_executions"] == 2
    assert engine.metrics["successful_executions"] == 1
    assert engine.metrics["failed_executions"] == 1
    assert engine.metrics["total_execution_time"] == 3.5
    assert engine.metrics["average_execution_time"] == 1.75


def test_get_metrics():
    """Test get_metrics method."""
    from autopr.workflows.engine import WorkflowEngine
    from autopr.config import AutoPRConfig
    
    config = AutoPRConfig()
    engine = WorkflowEngine(config)
    
    # Add some test data
    engine._update_metrics("success", 1.0)
    engine._update_metrics("success", 2.0)
    engine._update_metrics("failed", 1.5)
    
    metrics = engine.get_metrics()
    
    # Verify metrics structure
    assert "total_executions" in metrics
    assert "successful_executions" in metrics
    assert "success_rate_percent" in metrics
    
    # Verify success rate calculation
    assert metrics["total_executions"] == 3
    assert metrics["successful_executions"] == 2
    assert metrics["success_rate_percent"] == pytest.approx(66.67, rel=0.01)


# Test Enhancement #4: Exponential backoff retry logic
def test_retry_configuration():
    """Test that retry configuration is properly set."""
    from autopr.config import AutoPRConfig
    
    config = AutoPRConfig()
    
    # Verify retry configuration exists
    assert hasattr(config, 'workflow_retry_attempts')
    assert hasattr(config, 'workflow_retry_delay')
    
    # Verify default values
    assert config.workflow_retry_attempts == 3
    assert config.workflow_retry_delay == 5


@pytest.mark.asyncio
async def test_exponential_backoff_calculation():
    """Test that exponential backoff retry configuration is available."""
    from autopr.workflows.engine import WorkflowEngine
    from autopr.config import AutoPRConfig
    
    config = AutoPRConfig()
    config.workflow_retry_attempts = 3
    config.workflow_retry_delay = 2
    
    engine = WorkflowEngine(config)
    
    # Verify the config is accessible
    assert hasattr(config, 'workflow_retry_attempts')
    assert hasattr(config, 'workflow_retry_delay')
    assert config.workflow_retry_attempts == 3
    assert config.workflow_retry_delay == 2
    
    # The actual retry logic with exponential backoff is tested
    # through the workflow execution, but that requires complex setup.
    # This test verifies the configuration is in place.


# Test Enhancement #5: Startup configuration validation
@pytest.mark.asyncio
async def test_startup_validation():
    """Test that startup configuration validation is performed."""
    from autopr.engine import AutoPREngine
    from autopr.config import AutoPRConfig
    from autopr.exceptions import ConfigurationError
    
    # Create config
    config = AutoPRConfig()
    
    engine = AutoPREngine(config)
    
    # Mock config.validate() to return False
    with patch.object(config, 'validate', return_value=False):
        # Starting the engine should raise ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            await engine.start()
        
        assert "Invalid configuration" in str(exc_info.value)


def test_config_validate_method():
    """Test the config.validate() method."""
    from autopr.config import AutoPRConfig
    
    # Create config - validate should work with defaults
    config = AutoPRConfig()
    
    # Test that validate method exists
    assert hasattr(config, 'validate')
    assert callable(config.validate)
    
    # The actual validation logic depends on what keys are set
    # Just verify the method returns a boolean
    result = config.validate()
    assert isinstance(result, bool)


# Integration test for all changes
@pytest.mark.asyncio
async def test_comprehensive_integration():
    """Integration test covering multiple enhancements."""
    from autopr.engine import AutoPREngine
    from autopr.config import AutoPRConfig
    from autopr.workflows.engine import WorkflowEngine
    
    # Create valid config
    config = AutoPRConfig()
    config.github_token = "test_token"
    config.openai_api_key = "test_key"
    
    # Test that engine can be created with all enhancements
    engine = AutoPREngine(config)
    
    # Verify components are initialized
    assert engine.config is not None
    assert engine.workflow_engine is not None
    assert engine.action_registry is not None
    assert engine.integration_registry is not None
    
    # Verify workflow engine has metrics
    assert hasattr(engine.workflow_engine, 'metrics')
    
    # Test get_status includes metrics
    with patch.object(engine.workflow_engine, 'start', new_callable=AsyncMock), \
         patch.object(engine.integration_registry, 'initialize', new_callable=AsyncMock), \
         patch.object(engine.llm_manager, 'initialize', new_callable=AsyncMock), \
         patch.object(engine.workflow_engine, 'stop', new_callable=AsyncMock), \
         patch.object(engine.integration_registry, 'cleanup', new_callable=AsyncMock), \
         patch.object(engine.llm_manager, 'cleanup', new_callable=AsyncMock):
        await engine.start()
        
        status = engine.get_status()
        assert "workflow_engine" in status
        assert "metrics" in status["workflow_engine"]
        assert "engine" in status
        
        await engine.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
