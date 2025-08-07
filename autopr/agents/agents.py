"""
Agent definitions for the AutoPR Agent Framework.

This module defines the specialized agents used in the AutoPR code analysis pipeline.
"""
from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
from pathlib import Path
from dataclasses import dataclass

from crewai import Agent
from autopr.actions.llm import get_llm_provider_manager
from autopr.actions.quality_engine import QualityEngine
from autopr.utils.volume_utils import QualityMode
from autopr.actions.platform_detection import PlatformDetector
from autopr.actions.ai_linting_fixer import AILintingFixer
from autopr.utils.volume_utils import (
    volume_to_quality_mode,
    get_volume_config,
    get_volume_level_name
)
from autopr.agents.models import IssueSeverity

# Import models using full path to avoid circular imports
from autopr.agents.models import CodeIssue, PlatformAnalysis, CodeAnalysisReport

T = TypeVar('T')

@dataclass
class VolumeConfig:
    """Configuration for volume-based quality control.
    
    This class handles configuration that varies based on a volume level (0-1000),
    where 0 is the lowest strictness and 1000 is the highest. It supports automatic
    conversion of various boolean-like values for configuration parameters.
    
    Boolean Conversion Rules:
    - True values: True, 'true', 'True', '1', 1, 'yes', 'y', 'on' (case-insensitive)
    - False values: False, 'false', 'False', '0', 0, 'no', 'n', 'off', '' (empty string)
    - None values: Will raise ValueError as they are not valid for boolean fields
    - Any other value will be treated as False with a warning
    
    Attributes:
        volume: Integer between 0-1000 representing the volume level
        quality_mode: The quality mode derived from the volume level
        config: Dictionary of configuration parameters
    """
    volume: int = 500  # Default to moderate level (500/1000)
    quality_mode: Optional[QualityMode] = None
    config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        """Initialize volume configuration with validation and defaults."""
        # Import here to avoid circular imports
        from autopr.utils.volume_utils import volume_to_quality_mode
        from autopr.utils.volume_utils import QualityMode
        
        # Store user-provided config to preserve it
        user_config = self.config.copy() if self.config else {}
        
        # Ensure volume is an integer between 0-1000
        try:
            self.volume = max(0, min(1000, int(self.volume)))
        except (TypeError, ValueError) as e:
            raise ValueError(f"Volume must be an integer between 0-1000, got {self.volume}") from e
            
        # Initialize config if not provided
        if self.config is None:
            self.config = {}
            
        # If quality_mode is not provided, determine it from volume
        if self.quality_mode is None:
            try:
                # Get the default mode and config based on volume
                mode, default_config = volume_to_quality_mode(self.volume)
                self.quality_mode = mode
                # Merge default config with any provided config
                self.config = {**default_config, **user_config}
            except Exception as e:
                # Fall back to default values if volume_to_quality_mode fails
                self.quality_mode = QualityMode.BALANCED
                self.config = {
                    "max_fixes": 25,
                    "max_issues": 100,
                    "enable_ai_agents": True,
                    **user_config
                }
        
        # Ensure all boolean values in config are properly typed
        if self.config:
            for key, value in list(self.config.items()):
                # Only process fields that look like boolean flags
                if not isinstance(key, str) or not key.lower().startswith(('is_', 'has_', 'enable_', 'allow_')):
                    continue
                    
                # Raise ValueError for None values in boolean fields
                if value is None:
                    raise ValueError(f"Boolean field '{key}' cannot be None")
                    
                # Convert to bool based on type
                if isinstance(value, str):
                    self.config[key] = self._convert_to_bool(value)
                elif isinstance(value, (int, bool)):
                    self.config[key] = bool(value)
    
    @staticmethod
    def _convert_to_bool(value: Any) -> bool:
        """Convert various boolean-like values to Python bool.
        
        Args:
            value: The value to convert to boolean
            
        Returns:
            bool: The converted boolean value
            
        Raises:
            ValueError: If the value is None or an empty string (when strict=True)
        """
        if value is None:
            raise ValueError("Cannot convert None to boolean")
            
        if isinstance(value, bool):
            return value
            
        if isinstance(value, str):
            value = value.strip().lower()
            if not value:  # Empty string
                return False
            if value in ('true', 't', 'yes', 'y', 'on', '1'):
                return True
            if value in ('false', 'f', 'no', 'n', 'off', '0'):
                return False
            # For any other non-empty string that's not a recognized boolean value
            # We'll treat it as False but log a warning
            import warnings
            warnings.warn(
                f"Could not convert value '{value}' to boolean, defaulting to False",
                UserWarning,
                stacklevel=2
            )
            return False
                
        if isinstance(value, (int, float)):
            return bool(value)
            
        # For any other type, treat as False with a warning
        import warnings
        warnings.warn(
            f"Could not convert value '{value}' to boolean, defaulting to False",
            UserWarning,
            stacklevel=2
        )
        return False


class BaseAgent(Agent):
    """Base agent with common configuration and volume control."""
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        llm_model: str = "gpt-4",
        volume: int = 500,  # Default to moderate level
        **kwargs
    ):
        """Initialize the base agent with common settings.
        
        Args:
            role: The role of the agent
            goal: The goal of the agent
            backstory: The backstory of the agent
            llm_model: The LLM model to use (default: 'gpt-4')
            volume: Volume level (0-1000) controlling quality strictness
            **kwargs: Additional arguments to pass to the base Agent
        """
        # Initialize the base Agent class first to ensure all attributes are set up
        # We'll update the backstory after initialization
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,  # Will be updated after initialization
            llm=get_llm_provider_manager().get_provider(llm_model),
            allow_delegation=True,
            **kwargs
        )
        
        # Now set up our custom attributes after parent initialization
        self._volume = max(0, min(1000, volume))  # Clamp to 0-1000 range
        self._volume_config = VolumeConfig(volume=self._volume)
        
        # Update the backstory with volume context
        volume_level = get_volume_level_name(self._volume)
        self.backstory = f"""{backstory}
        
        You are currently operating at volume level {self._volume} ({volume_level}). 
        This affects the strictness of your analysis and the depth of your checks.
        """
        
    @property
    def volume(self) -> int:
        """Get the current volume level (0-1000)."""
        return self._volume
        
    @property
    def volume_config(self) -> VolumeConfig:
        """Get the volume configuration."""
        return self._volume_config
    
    def get_volume_context(self) -> Dict[str, Any]:
        """Get context about the current volume level for agent tasks."""
        return {
            "volume": self._volume,
            "volume_level": get_volume_level_name(self._volume),
            "quality_mode": self._volume_config.quality_mode.value if self._volume_config.quality_mode else None,
            "quality_config": self._volume_config.config or {}
        }


class CodeQualityAgent(BaseAgent):
    """Agent responsible for code quality analysis with volume-aware strictness."""
    
    def __init__(self, **kwargs):
        """Initialize the code quality agent with volume control.
        
        Args:
            **kwargs: Additional arguments including 'volume' (0-1000)
        """
        # Initialize the base agent first
        super().__init__(
            role="Senior Code Quality Engineer",
            goal="Analyze and improve code quality through comprehensive checks with configurable strictness",
            backstory="""You are an expert in static code analysis, code smells detection, 
            and quality metrics. You excel at identifying potential issues and suggesting 
            improvements. You have a keen eye for detail and a deep understanding of 
            software engineering best practices.""",
            **kwargs
        )
        
        # Initialize the quality engine with volume configuration
        self._quality_engine = QualityEngine()
        
        # Configure quality engine based on volume if needed
        if self.volume_config.config:
            # Apply any quality engine specific configurations from volume config
            quality_config = {
                k: v for k, v in self.volume_config.config.items()
                if k.startswith("quality_")
            }
            if quality_config:
                # Apply quality config to the quality engine if needed
                pass
    
    @property
    def quality_engine(self) -> QualityEngine:
        """Get the quality engine instance."""
        return self._quality_engine
    
    async def analyze_code_quality(self, repo_path: str) -> Dict[str, Any]:
        """Analyze code quality for the given repository."""
        # Delegate to the quality engine with volume context
        return await self._quality_engine.analyze_code(repo_path)


class PlatformAnalysisAgent(BaseAgent):
    """Agent responsible for platform and technology stack analysis with volume-aware depth."""
    
    def __init__(self, **kwargs):
        """Initialize the platform analysis agent with volume control.
        
        Args:
            **kwargs: Additional arguments including 'volume' (0-1000)
        """
        # Initialize the base agent first
        super().__init__(
            role="Platform Architecture Specialist",
            goal="Identify and analyze the technology stack and platform architecture with configurable depth",
            backstory="""You have deep knowledge of various technology stacks, frameworks, 
            and platform architectures. You can detect platform-specific patterns and 
            provide optimization recommendations. You understand how different components 
            interact and can identify potential integration issues.
            
            Your analysis depth and thoroughness are adjusted based on the current volume level.""",
            **kwargs
        )
        
        # Initialize the platform detector with volume configuration
        self._platform_detector = PlatformDetector()
        
        # Configure platform detector based on volume if needed
        if self.volume_config.config and "platform_scan_depth" in self.volume_config.config:
            self._platform_detector.scan_depth = self.volume_config.config["platform_scan_depth"]
    
    @property
    def platform_detector(self) -> PlatformDetector:
        """Get the platform detector instance."""
        return self._platform_detector
    
    async def analyze_platform(self, repo_path: str) -> PlatformAnalysis:
        """Analyze the platform and technology stack."""
        # Delegate to the platform detector
        detection_result = await self.platform_detector.detect_platform(repo_path)
        
        # Convert to our model
        components = [
            PlatformComponent(
                name=comp["name"],
                version=comp.get("version"),
                confidence=comp["confidence"],
                evidence=comp.get("evidence", [])
            )
            for comp in detection_result.get("components", [])
        ]
        
        return PlatformAnalysis(
            platform=detection_result["platform"],
            confidence=detection_result["confidence"],
            components=components,
            recommendations=detection_result.get("recommendations", [])
        )


class LintingAgent(BaseAgent):
    """Agent responsible for code linting and style enforcement with volume-aware strictness."""
    
    def __init__(self, **kwargs):
        """Initialize the linting agent with volume control.
        
        Args:
            **kwargs: Additional arguments including 'volume' (0-1000)
        """
        super().__init__(
            role="Senior Linting Engineer",
            goal="Detect and fix code style and quality issues with configurable strictness",
            backstory="""You are an expert in code style guides, best practices, and 
            automated code quality tools. You help maintain consistent code quality 
            across the codebase. You're meticulous about following style guides and 
            can spot even the most subtle style violations.
            
            Your strictness and thoroughness are adjusted based on the current volume level.""",
            **kwargs
        )
        
        # Configure linting fixer based on volume
        linting_config = {}
        if self.volume_config.config:
            linting_config.update({
                k: v for k, v in self.volume_config.config.items()
                if k.startswith("linting_")
            })
            
        self._linting_fixer = AILintingFixer(**linting_config)
        
        # Adjust verbosity based on volume
        self._verbose = False
        if self.volume_config.quality_mode:
            self._verbose = (self.volume_config.quality_mode != QualityMode.ULTRA_FAST)
    
    @property
    def linting_fixer(self) -> AILintingFixer:
        """Get the linting fixer instance."""
        return self._linting_fixer
        
    @property
    def verbose(self) -> bool:
        """Get the verbosity setting."""
        return self._verbose
        
    @verbose.setter
    def verbose(self, value: bool) -> None:
        """Set the verbosity setting."""
        self._verbose = value
    
    async def fix_code_issues(self, file_path: str) -> List[CodeIssue]:
        """Fix code style and quality issues in the specified file.
        
        Args:
            file_path: Path to the file to fix
            
        Returns:
            List[CodeIssue]: List of fixed issues, or an error issue if processing failed
            
        Raises:
            FileNotFoundError: If the specified file does not exist
            PermissionError: If there are permission issues reading/writing the file
        """
        try:
            # Get the file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            except UnicodeDecodeError as e:
                return [CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message=f"Failed to decode file: {str(e)}. File may be binary or use a different encoding.",
                    severity=IssueSeverity.HIGH,
                    rule_id="encoding-error",
                    category="error"
                )]
            
            # Fix issues using the linting fixer
            try:
                fixed_content, issues = await self._linting_fixer.fix_code(
                    file_path=file_path,
                    file_content=file_content,
                    verbose=self._verbose
                )
            except Exception as e:
                return [CodeIssue(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message=f"Linting failed: {str(e)}",
                    severity=IssueSeverity.HIGH,
                    rule_id="linting-error",
                    category="error"
                )]
            
            # Write the fixed content back to the file if it changed
            if fixed_content != file_content:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    if self._verbose:
                        print(f"Fixed {len(issues)} issues in {file_path}")
                except Exception as e:
                    # If we can't write the file, log it and continue
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=0,
                        column=0,
                        message=f"Failed to write fixes to file: {str(e)}",
                        severity=IssueSeverity.HIGH,
                        rule_id="write-error",
                        category="error"
                    ))
            
            return issues
            
        except FileNotFoundError:
            raise  # Re-raise file not found errors
            
        except PermissionError:
            raise  # Re-raise permission errors
            
        except Exception as e:
            # For any other unexpected errors, return an error issue
            if self._verbose:
                print(f"Unexpected error fixing issues in {file_path}: {str(e)}")
            return [CodeIssue(
                file_path=file_path,
                line_number=0,
                column=0,
                message=f"Unexpected error: {str(e)}",
                severity=IssueSeverity.HIGH,
                rule_id="unexpected-error",
                category="error"
            )]
