def test_load_config_default_settings():
    """Test that load_config successfully loads and validates default configuration."""
    config = load_config()

    assert config.default_mode == "smart"
    assert "ruff" in config.tools
    assert "mypy" in config.tools
    assert config.tools["ruff"].enabled is True
    assert config.tools["mypy"].enabled is True
    assert "fast" in config.modes
    assert "comprehensive" in config.modes
    assert "ai_enhanced" in config.modes
    assert "smart" in config.modes
    assert config.modes["fast"] == ["ruff"]
    assert "ruff" in config.modes["comprehensive"]
    assert "mypy" in config.modes["comprehensive"]


def test_validate_config_raises_error_for_undefined_tool():
    """Test that validate_config raises ValueError when a tool in modes is not defined in tools section."""
    invalid_config = QualityEngineConfig(
        default_mode="smart",
        tools={
            "ruff": ToolConfig(enabled=True, config={}),
            "mypy": ToolConfig(enabled=True, config={}),
        },
        modes={"fast": ["ruff", "undefined_tool"]},
    )

    with pytest.raises(
        ValueError,
        match="Tool 'undefined_tool' in mode 'fast' is not defined in the tools section.",
    ):
        validate_config(invalid_config)


def test_validate_config_succeeds_when_all_tools_in_fast_mode_exist():
    """Test that validate_config succeeds when all tools in fast mode are defined in tools section."""
    valid_config = QualityEngineConfig(
        default_mode="smart",
        tools={
            "ruff": ToolConfig(enabled=True, config={}),
            "mypy": ToolConfig(enabled=True, config={}),
        },
        modes={"fast": ["ruff"]},
    )

    # Should not raise any exception
    validate_config(valid_config)


def test_validate_config_passes_when_all_comprehensive_tools_exist():
    """Test that validate_config passes when all tools in comprehensive mode are defined in tools section."""
    valid_config = QualityEngineConfig(
        default_mode="smart",
        tools={
            "ruff": ToolConfig(enabled=True, config={}),
            "mypy": ToolConfig(enabled=True, config={}),
            "bandit": ToolConfig(enabled=True, config={}),
            "interrogate": ToolConfig(enabled=True, config={}),
            "radon": ToolConfig(enabled=True, config={}),
            "pytest": ToolConfig(enabled=True, config={}),
        },
        modes={
            "comprehensive": [
                "ruff",
                "mypy",
                "bandit",
                "interrogate",
                "radon",
                "pytest",
            ]
        },
    )

    # Should not raise any exception
    validate_config(valid_config)


def test_validate_config_handles_empty_modes_dictionary():
    """Test that validate_config handles empty modes dictionary without raising errors."""
    config_with_empty_modes = QualityEngineConfig(
        default_mode="smart",
        tools={
            "ruff": ToolConfig(enabled=True, config={}),
            "mypy": ToolConfig(enabled=True, config={}),
        },
        modes={},
    )

    # Should not raise any exception
    validate_config(config_with_empty_modes)


def test_validate_config_raises_error_for_empty_tools_with_non_empty_modes():
    """Test that validate_config raises ValueError when tools dictionary is empty but modes contain tools."""
    invalid_config = QualityEngineConfig(
        default_mode="smart",
        tools={},
        modes={"fast": ["ruff"]},
    )

    with pytest.raises(
        ValueError,
        match="Tool 'ruff' in mode 'fast' is not defined in the tools section.",
    ):
        validate_config(invalid_config)


def test_validate_config_allows_duplicate_tool_references():
    """Test that validate_config allows duplicate tool references in modes."""
    config_with_duplicates = QualityEngineConfig(
        default_mode="smart",
        tools={
            "ruff": ToolConfig(enabled=True, config={}),
            "mypy": ToolConfig(enabled=True, config={}),
        },
        modes={"comprehensive": ["ruff", "mypy", "ruff"]},
    )

    # Should not raise any exception
    validate_config(config_with_duplicates)


def test_validate_config_raises_error_for_tool_casing_mismatch():
    """Test that validate_config raises ValueError when tools in modes have different casing than tools section."""
    invalid_config = QualityEngineConfig(
        default_mode="smart",
        tools={
            "ruff": ToolConfig(enabled=True, config={}),
            "mypy": ToolConfig(enabled=True, config={}),
        },
        modes={"fast": ["Ruff", "MyPy"]},
    )

    with pytest.raises(
        ValueError,
        match="Tool 'Ruff' in mode 'fast' is not defined in the tools section.",
    ):
        validate_config(invalid_config)


def test_validate_config_allows_extra_tools_not_used_in_modes():
    """Test that validate_config allows extra tools in tools section that are not used in any mode."""
    valid_config = QualityEngineConfig(
        default_mode="smart",
        tools={
            "ruff": ToolConfig(enabled=True, config={}),
            "mypy": ToolConfig(enabled=True, config={}),
            "extra_tool": ToolConfig(enabled=True, config={}),
        },
        modes={"fast": ["ruff", "mypy"]},
    )

    # Should not raise any exception
    validate_config(valid_config)


def test_validate_config_handles_empty_tool_lists():
    """Test that validate_config handles modes with empty tool lists without validation errors."""
    config_with_empty_mode = QualityEngineConfig(
        default_mode="smart",
        tools={
            "ruff": ToolConfig(enabled=True, config={}),
            "mypy": ToolConfig(enabled=True, config={}),
        },
        modes={"fast": ["ruff"], "empty_mode": [], "comprehensive": ["ruff", "mypy"]},
    )

    # Should not raise any exception
    validate_config(config_with_empty_mode)


async def test_execute_comprehensive_mode():
    inputs = QualityInputs(mode=Mode.COMPREHENSIVE, files=["main.py"])
    outputs = await quality_engine.execute(inputs)
    assert "ruff" in outputs.summary
    assert "mypy" in outputs.summary
    assert "bandit" in outputs.summary


async def test_execute_ai_enhanced_mode():
    inputs = QualityInputs(mode=Mode.AI_ENHANCED, files=["main.py"])
    outputs = await quality_engine.execute(inputs)
    assert "ai_feedback" in outputs.summary


async def test_execute_smart_mode():
    inputs = QualityInputs(mode=Mode.SMART, files=["main.py", "README.md"])
    outputs = await quality_engine.execute(inputs)
    assert "ruff" in outputs.summary
    assert "interrogate" in outputs.summary
