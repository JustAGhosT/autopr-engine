#!/usr/bin/env python3
"""
Comprehensive tests for engine module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import json
import asyncio
from pathlib import Path

# Import the modules we're testing
try:
    from autopr.actions.engine import (
        AutoPREngine, EngineConfig, EngineState, EngineManager,
        EngineRunner, EngineValidator, EngineMonitor
    )
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestEngineConfig:
    """Test EngineConfig class."""

    def test_engine_config_initialization(self):
        """Test EngineConfig initialization."""
        config = EngineConfig(
            max_workers=4,
            timeout=300,
            retry_attempts=3,
            enable_logging=True,
            log_level="INFO",
            cache_enabled=True,
            cache_size=1000,
            auto_save=True,
            save_interval=60
        )
        
        assert config.max_workers == 4
        assert config.timeout == 300
        assert config.retry_attempts == 3
        assert config.enable_logging is True
        assert config.log_level == "INFO"
        assert config.cache_enabled is True
        assert config.cache_size == 1000
        assert config.auto_save is True
        assert config.save_interval == 60

    def test_engine_config_defaults(self):
        """Test EngineConfig with default values."""
        config = EngineConfig()
        
        assert config.max_workers == 2
        assert config.timeout == 600
        assert config.retry_attempts == 2
        assert config.enable_logging is True
        assert config.log_level == "WARNING"
        assert config.cache_enabled is False
        assert config.cache_size == 100
        assert config.auto_save is False
        assert config.save_interval == 300

    def test_engine_config_to_dict(self):
        """Test EngineConfig to_dict method."""
        config = EngineConfig(
            max_workers=8,
            timeout=180,
            retry_attempts=5,
            enable_logging=False,
            log_level="DEBUG"
        )
        
        result = config.to_dict()
        assert result["max_workers"] == 8
        assert result["timeout"] == 180
        assert result["retry_attempts"] == 5
        assert result["enable_logging"] is False
        assert result["log_level"] == "DEBUG"

    def test_engine_config_from_dict(self):
        """Test EngineConfig from_dict method."""
        data = {
            "max_workers": 6,
            "timeout": 240,
            "retry_attempts": 4,
            "enable_logging": True,
            "log_level": "ERROR",
            "cache_enabled": True,
            "cache_size": 500,
            "auto_save": True,
            "save_interval": 120
        }
        
        config = EngineConfig.from_dict(data)
        assert config.max_workers == 6
        assert config.timeout == 240
        assert config.retry_attempts == 4
        assert config.enable_logging is True
        assert config.log_level == "ERROR"
        assert config.cache_enabled is True
        assert config.cache_size == 500
        assert config.auto_save is True
        assert config.save_interval == 120

    def test_engine_config_validation(self):
        """Test EngineConfig validation."""
        # Test valid config
        config = EngineConfig(max_workers=4, timeout=300)
        assert config.is_valid() is True
        
        # Test invalid config
        invalid_config = EngineConfig(max_workers=0, timeout=-1)
        assert invalid_config.is_valid() is False


class TestEngineState:
    """Test EngineState class."""

    def test_engine_state_initialization(self):
        """Test EngineState initialization."""
        state = EngineState(
            status="idle",
            current_task="test_task",
            progress=0.5,
            start_time="2023-01-01T00:00:00",
            end_time=None,
            error_count=0,
            success_count=5
        )
        
        assert state.status == "idle"
        assert state.current_task == "test_task"
        assert state.progress == 0.5
        assert state.start_time == "2023-01-01T00:00:00"
        assert state.end_time is None
        assert state.error_count == 0
        assert state.success_count == 5

    def test_engine_state_defaults(self):
        """Test EngineState with default values."""
        state = EngineState()
        
        assert state.status == "stopped"
        assert state.current_task is None
        assert state.progress == 0.0
        assert state.start_time is None
        assert state.end_time is None
        assert state.error_count == 0
        assert state.success_count == 0

    def test_engine_state_to_dict(self):
        """Test EngineState to_dict method."""
        state = EngineState(
            status="running",
            current_task="processing",
            progress=0.75,
            start_time="2023-01-01T00:00:00",
            error_count=1,
            success_count=10
        )
        
        result = state.to_dict()
        assert result["status"] == "running"
        assert result["current_task"] == "processing"
        assert result["progress"] == 0.75
        assert result["error_count"] == 1
        assert result["success_count"] == 10

    def test_engine_state_from_dict(self):
        """Test EngineState from_dict method."""
        data = {
            "status": "completed",
            "current_task": "final_task",
            "progress": 1.0,
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2023-01-01T01:00:00",
            "error_count": 2,
            "success_count": 15
        }
        
        state = EngineState.from_dict(data)
        assert state.status == "completed"
        assert state.current_task == "final_task"
        assert state.progress == 1.0
        assert state.start_time == "2023-01-01T00:00:00"
        assert state.end_time == "2023-01-01T01:00:00"
        assert state.error_count == 2
        assert state.success_count == 15

    def test_engine_state_update(self):
        """Test updating engine state."""
        state = EngineState()
        
        state.update_status("running")
        assert state.status == "running"
        
        state.update_progress(0.25)
        assert state.progress == 0.25
        
        state.increment_success()
        assert state.success_count == 1
        
        state.increment_error()
        assert state.error_count == 1


class TestEngineValidator:
    """Test EngineValidator class."""

    @pytest.fixture
    def engine_validator(self):
        """Create an EngineValidator instance for testing."""
        return EngineValidator()

    def test_engine_validator_initialization(self, engine_validator):
        """Test EngineValidator initialization."""
        assert engine_validator.validation_rules == []
        assert engine_validator.error_messages == []

    def test_add_validation_rule(self, engine_validator):
        """Test adding a validation rule."""
        def config_rule(config):
            return config.max_workers > 0
        
        engine_validator.add_validation_rule(config_rule)
        assert len(engine_validator.validation_rules) == 1

    def test_validate_config(self, engine_validator):
        """Test validating engine configuration."""
        # Valid config
        valid_config = EngineConfig(max_workers=4, timeout=300)
        result = engine_validator.validate_config(valid_config)
        assert result.is_valid is True
        
        # Invalid config
        invalid_config = EngineConfig(max_workers=0, timeout=-1)
        result = engine_validator.validate_config(invalid_config)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_state(self, engine_validator):
        """Test validating engine state."""
        # Valid state
        valid_state = EngineState(status="idle", progress=0.0)
        result = engine_validator.validate_state(valid_state)
        assert result.is_valid is True
        
        # Invalid state
        invalid_state = EngineState(status="invalid_status", progress=1.5)
        result = engine_validator.validate_state(invalid_state)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_task(self, engine_validator):
        """Test validating engine task."""
        # Valid task
        valid_task = {"name": "test_task", "priority": "high", "timeout": 60}
        result = engine_validator.validate_task(valid_task)
        assert result.is_valid is True
        
        # Invalid task
        invalid_task = {"name": "", "priority": "invalid", "timeout": -1}
        result = engine_validator.validate_task(invalid_task)
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestEngineMonitor:
    """Test EngineMonitor class."""

    @pytest.fixture
    def engine_monitor(self):
        """Create an EngineMonitor instance for testing."""
        return EngineMonitor()

    def test_engine_monitor_initialization(self, engine_monitor):
        """Test EngineMonitor initialization."""
        assert engine_monitor.monitoring_enabled is True
        assert engine_monitor.metrics == {}
        assert engine_monitor.alerts == []

    def test_start_monitoring(self, engine_monitor):
        """Test starting engine monitoring."""
        engine_monitor.start_monitoring()
        assert engine_monitor.monitoring_enabled is True
        assert engine_monitor.start_time is not None

    def test_stop_monitoring(self, engine_monitor):
        """Test stopping engine monitoring."""
        engine_monitor.start_monitoring()
        engine_monitor.stop_monitoring()
        assert engine_monitor.monitoring_enabled is False
        assert engine_monitor.end_time is not None

    def test_record_metric(self, engine_monitor):
        """Test recording engine metrics."""
        engine_monitor.record_metric("cpu_usage", 75.5)
        engine_monitor.record_metric("memory_usage", 1024)
        
        assert "cpu_usage" in engine_monitor.metrics
        assert "memory_usage" in engine_monitor.metrics
        assert engine_monitor.metrics["cpu_usage"] == 75.5
        assert engine_monitor.metrics["memory_usage"] == 1024

    def test_get_metrics_summary(self, engine_monitor):
        """Test getting metrics summary."""
        # Record some metrics
        engine_monitor.record_metric("cpu_usage", 50.0)
        engine_monitor.record_metric("memory_usage", 2048)
        engine_monitor.record_metric("task_count", 10)
        
        summary = engine_monitor.get_metrics_summary()
        
        assert "cpu_usage" in summary
        assert "memory_usage" in summary
        assert "task_count" in summary
        assert summary["cpu_usage"] == 50.0
        assert summary["memory_usage"] == 2048
        assert summary["task_count"] == 10

    def test_add_alert(self, engine_monitor):
        """Test adding engine alerts."""
        engine_monitor.add_alert("high_cpu", "CPU usage is high", "warning")
        engine_monitor.add_alert("low_memory", "Memory usage is low", "info")
        
        assert len(engine_monitor.alerts) == 2
        assert engine_monitor.alerts[0]["type"] == "high_cpu"
        assert engine_monitor.alerts[0]["message"] == "CPU usage is high"
        assert engine_monitor.alerts[0]["severity"] == "warning"

    def test_clear_alerts(self, engine_monitor):
        """Test clearing engine alerts."""
        engine_monitor.add_alert("test_alert", "Test message", "info")
        assert len(engine_monitor.alerts) == 1
        
        engine_monitor.clear_alerts()
        assert len(engine_monitor.alerts) == 0


class TestEngineRunner:
    """Test EngineRunner class."""

    @pytest.fixture
    def engine_runner(self):
        """Create an EngineRunner instance for testing."""
        config = EngineConfig(max_workers=2, timeout=60)
        return EngineRunner(config)

    def test_engine_runner_initialization(self, engine_runner):
        """Test EngineRunner initialization."""
        assert engine_runner.config is not None
        assert engine_runner.state is not None
        assert engine_runner.validator is not None
        assert engine_runner.monitor is not None

    def test_start_engine(self, engine_runner):
        """Test starting the engine."""
        result = engine_runner.start_engine()
        assert result is True
        assert engine_runner.state.status == "running"

    def test_stop_engine(self, engine_runner):
        """Test stopping the engine."""
        engine_runner.start_engine()
        result = engine_runner.stop_engine()
        assert result is True
        assert engine_runner.state.status == "stopped"

    def test_pause_engine(self, engine_runner):
        """Test pausing the engine."""
        engine_runner.start_engine()
        result = engine_runner.pause_engine()
        assert result is True
        assert engine_runner.state.status == "paused"

    def test_resume_engine(self, engine_runner):
        """Test resuming the engine."""
        engine_runner.start_engine()
        engine_runner.pause_engine()
        result = engine_runner.resume_engine()
        assert result is True
        assert engine_runner.state.status == "running"

    def test_submit_task(self, engine_runner):
        """Test submitting a task to the engine."""
        task = {"name": "test_task", "priority": "high", "timeout": 30}
        
        result = engine_runner.submit_task(task)
        assert result is True

    def test_get_task_status(self, engine_runner):
        """Test getting task status."""
        task_id = "test_task_123"
        status = engine_runner.get_task_status(task_id)
        
        assert status in ["pending", "running", "completed", "failed", "unknown"]

    def test_cancel_task(self, engine_runner):
        """Test canceling a task."""
        task_id = "test_task_123"
        result = engine_runner.cancel_task(task_id)
        assert result is True

    def test_get_engine_status(self, engine_runner):
        """Test getting engine status."""
        status = engine_runner.get_engine_status()
        
        assert "status" in status
        assert "current_task" in status
        assert "progress" in status
        assert "error_count" in status
        assert "success_count" in status

    def test_restart_engine(self, engine_runner):
        """Test restarting the engine."""
        engine_runner.start_engine()
        result = engine_runner.restart_engine()
        assert result is True
        assert engine_runner.state.status == "running"


class TestEngineManager:
    """Test EngineManager class."""

    @pytest.fixture
    def engine_manager(self):
        """Create an EngineManager instance for testing."""
        config = EngineConfig(max_workers=2, timeout=60)
        return EngineManager(config)

    def test_engine_manager_initialization(self, engine_manager):
        """Test EngineManager initialization."""
        assert engine_manager.config is not None
        assert engine_manager.runner is not None
        assert engine_manager.validator is not None
        assert engine_manager.monitor is not None

    def test_create_engine(self, engine_manager):
        """Test creating a new engine."""
        engine = engine_manager.create_engine("test_engine")
        assert engine is not None
        assert engine.name == "test_engine"

    def test_get_engine(self, engine_manager):
        """Test getting an engine by name."""
        engine_name = "test_engine"
        engine_manager.create_engine(engine_name)
        
        engine = engine_manager.get_engine(engine_name)
        assert engine is not None
        assert engine.name == engine_name

    def test_list_engines(self, engine_manager):
        """Test listing all engines."""
        engine_manager.create_engine("engine1")
        engine_manager.create_engine("engine2")
        
        engines = engine_manager.list_engines()
        assert len(engines) == 2
        assert "engine1" in engines
        assert "engine2" in engines

    def test_remove_engine(self, engine_manager):
        """Test removing an engine."""
        engine_name = "test_engine"
        engine_manager.create_engine(engine_name)
        
        result = engine_manager.remove_engine(engine_name)
        assert result is True
        
        engines = engine_manager.list_engines()
        assert engine_name not in engines

    def test_start_all_engines(self, engine_manager):
        """Test starting all engines."""
        engine_manager.create_engine("engine1")
        engine_manager.create_engine("engine2")
        
        result = engine_manager.start_all_engines()
        assert result is True

    def test_stop_all_engines(self, engine_manager):
        """Test stopping all engines."""
        engine_manager.create_engine("engine1")
        engine_manager.create_engine("engine2")
        engine_manager.start_all_engines()
        
        result = engine_manager.stop_all_engines()
        assert result is True

    def test_get_engine_status_all(self, engine_manager):
        """Test getting status of all engines."""
        engine_manager.create_engine("engine1")
        engine_manager.create_engine("engine2")
        
        status = engine_manager.get_engine_status_all()
        assert len(status) == 2
        assert "engine1" in status
        assert "engine2" in status

    def test_validate_all_engines(self, engine_manager):
        """Test validating all engines."""
        engine_manager.create_engine("engine1")
        engine_manager.create_engine("engine2")
        
        results = engine_manager.validate_all_engines()
        assert len(results) == 2
        assert all(result.is_valid for result in results.values())


class TestAutoPREngine:
    """Test AutoPREngine class."""

    @pytest.fixture
    def auto_pr_engine(self):
        """Create an AutoPREngine instance for testing."""
        config = EngineConfig(max_workers=2, timeout=60)
        return AutoPREngine(config)

    def test_auto_pr_engine_initialization(self, auto_pr_engine):
        """Test AutoPREngine initialization."""
        assert auto_pr_engine.config is not None
        assert auto_pr_engine.manager is not None
        assert auto_pr_engine.state is not None

    def test_initialize_engine(self, auto_pr_engine):
        """Test initializing the AutoPR engine."""
        result = auto_pr_engine.initialize_engine()
        assert result is True
        assert auto_pr_engine.state.status == "initialized"

    def test_start_engine(self, auto_pr_engine):
        """Test starting the AutoPR engine."""
        auto_pr_engine.initialize_engine()
        result = auto_pr_engine.start_engine()
        assert result is True
        assert auto_pr_engine.state.status == "running"

    def test_stop_engine(self, auto_pr_engine):
        """Test stopping the AutoPR engine."""
        auto_pr_engine.initialize_engine()
        auto_pr_engine.start_engine()
        result = auto_pr_engine.stop_engine()
        assert result is True
        assert auto_pr_engine.state.status == "stopped"

    def test_process_repository(self, auto_pr_engine):
        """Test processing a repository."""
        repo_config = {
            "name": "test_repo",
            "url": "https://github.com/test/repo",
            "branch": "main"
        }
        
        result = auto_pr_engine.process_repository(repo_config)
        assert result is True

    def test_analyze_code(self, auto_pr_engine):
        """Test analyzing code."""
        code_content = "def test_function():\n    return True"
        
        result = auto_pr_engine.analyze_code(code_content)
        assert result is not None
        assert "analysis" in result

    def test_generate_fixes(self, auto_pr_engine):
        """Test generating fixes."""
        issues = [
            {"type": "syntax", "message": "Missing colon", "line": 1},
            {"type": "style", "message": "Line too long", "line": 2}
        ]
        
        fixes = auto_pr_engine.generate_fixes(issues)
        assert len(fixes) > 0

    def test_apply_fixes(self, auto_pr_engine):
        """Test applying fixes."""
        code_content = "def test_function()\n    return True"  # Missing colon
        fixes = [
            {"type": "syntax", "line": 1, "fix": "def test_function():\n    return True"}
        ]
        
        result = auto_pr_engine.apply_fixes(code_content, fixes)
        assert result is True

    def test_create_pull_request(self, auto_pr_engine):
        """Test creating a pull request."""
        pr_data = {
            "title": "Fix syntax issues",
            "description": "Applied automatic fixes",
            "branch": "fix/syntax-issues",
            "files": ["test.py"]
        }
        
        result = auto_pr_engine.create_pull_request(pr_data)
        assert result is True

    def test_get_engine_status(self, auto_pr_engine):
        """Test getting engine status."""
        status = auto_pr_engine.get_engine_status()
        
        assert "status" in status
        assert "current_task" in status
        assert "progress" in status
        assert "repositories_processed" in status
        assert "pull_requests_created" in status

    def test_get_processing_summary(self, auto_pr_engine):
        """Test getting processing summary."""
        summary = auto_pr_engine.get_processing_summary()
        
        assert "total_repositories" in summary
        assert "processed_repositories" in summary
        assert "total_issues_found" in summary
        assert "total_fixes_applied" in summary
        assert "total_pull_requests" in summary

    def test_save_engine_state(self, auto_pr_engine):
        """Test saving engine state."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            result = auto_pr_engine.save_engine_state(temp_file)
            assert result is True
            assert os.path.exists(temp_file)
            
            # Verify file content
            with open(temp_file, 'r') as f:
                content = f.read()
                state_data = json.loads(content)
                assert "status" in state_data
                assert "current_task" in state_data
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_load_engine_state(self, auto_pr_engine):
        """Test loading engine state."""
        # Create a test state file
        test_state = {
            "status": "running",
            "current_task": "processing_repo",
            "progress": 0.5,
            "repositories_processed": 2,
            "pull_requests_created": 1
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(test_state, f)
            temp_file = f.name
        
        try:
            result = auto_pr_engine.load_engine_state(temp_file)
            assert result is True
            assert auto_pr_engine.state.status == "running"
            assert auto_pr_engine.state.current_task == "processing_repo"
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_validate_engine_configuration(self, auto_pr_engine):
        """Test validating engine configuration."""
        result = auto_pr_engine.validate_engine_configuration()
        assert result.is_valid is True

    def test_run_engine_tests(self, auto_pr_engine):
        """Test running engine tests."""
        results = auto_pr_engine.run_engine_tests()
        assert len(results) > 0
        assert all("test_name" in result for result in results)
        assert all("status" in result for result in results)
