"""
Volume configuration for agent quality control.

This module provides the VolumeConfig class which handles configuration that varies
based on a volume level (0-1000), where 0 is the lowest strictness and 1000 is the highest.
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass
from autopr.utils.volume_utils import QualityMode
from autopr.actions.quality_engine.volume_mapping import volume_to_quality_mode


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
        """Initialize volume-based configuration with enhanced boolean handling.
        
        This method:
        1. Validates and clamps the volume to 0-1000 range
        2. Loads default quality mode and config if not provided
        3. Ensures all boolean values in config are properly typed
        4. Preserves user-provided config values while applying volume defaults
        """
        # Ensure volume is within valid range (0-1000)
        try:
            self.volume = max(0, min(1000, int(self.volume)))
        except (TypeError, ValueError) as e:
            raise ValueError(f"Volume must be an integer between 0-1000, got {self.volume}") from e
        
        # Store user-provided config to preserve it
        user_config = self.config.copy() if self.config else {}
        
        # Get default mode and config based on volume if needed
        if self.quality_mode is None or self.config is None:
            try:
                # Get the default mode and config based on volume
                mode, default_config = volume_to_quality_mode(self.volume)
            except Exception as e:
                raise ValueError(
                    f"Failed to get default mode and config for volume {self.volume}"
                ) from e
            
            # Initialize with default values
            self.quality_mode = mode
            self.config = default_config
            
            # Apply user-provided config on top of defaults
            if user_config:
                self.config.update(user_config)
        
        # Ensure all boolean values in config are properly typed
        if self.config:
            for key, value in list(self.config.items()):
                # Only process fields that look like boolean flags
                if not isinstance(key, str) or not key.lower().startswith(
                    ('is_', 'has_', 'enable_', 'allow_')
                ):
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
    def _warn_about_conversion(value: Any) -> None:
        """Issue a warning about failed boolean conversion.
        
        Args:
            value: The value that failed boolean conversion
        """
        import warnings
        warnings.warn(
            f"Could not convert value '{value}' to boolean, defaulting to False",
            UserWarning,
            stacklevel=3  # Adjusted for additional call level
        )

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
            VolumeConfig._warn_about_conversion(value)
            return False
                
        if isinstance(value, (int, float)):
            return bool(value)
            
        # For any other type, treat as False with a warning
        VolumeConfig._warn_about_conversion(value)
        return False
