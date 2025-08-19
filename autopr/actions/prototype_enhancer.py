"""
Prototype Enhancer - Backward Compatibility Wrapper

This module provides backward compatibility by importing the new modular PrototypeEnhancer
while maintaining the same interface as the original monolithic implementation.

The original 1,247-line PrototypeEnhancer class has been refactored into a modular architecture
with the following components:
- platform_configs.py: Platform definitions and configurations
- file_generators.py: File generation utilities
- enhancement_strategies.py: Platform-specific enhancement logic
- enhancer.py: Main orchestrator class

This refactoring improves:
- Maintainability: Smaller, focused modules
- Testability: Isolated components for unit testing
- Extensibility: Easy addition of new platforms and enhancement types
- Code reuse: Shared utilities across platforms
"""

# Import the new modular PrototypeEnhancer
from autopr.actions.prototype_enhancement import PrototypeEnhancer

# Maintain backward compatibility by re-exporting
__all__ = ["PrototypeEnhancer"]

# Legacy import support - users can still import from this module
# without changing their existing code
