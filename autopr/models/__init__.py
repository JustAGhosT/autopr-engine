"""
Models Package

This package contains data models and schemas used throughout the AutoPR system.
"""

from pathlib import Path


package_dir = Path(__file__).parent
package_dir.mkdir(parents=True, exist_ok=True)

# Create artifacts module
artifacts_path = package_dir / "artifacts.py"
if not artifacts_path.exists():
    with artifacts_path.open("w", encoding="utf-8") as f:
        content = (
            '"""\n'
            "Artifacts Module\n\n"
            "This module contains data models for various artifacts "
            "used in the AutoPR system.\n"
            '"""\n\n'
            "from dataclasses import dataclass\n"
            "from enum import Enum\n"
            "from typing import Any, Dict, List, Optional\n\n\n"
            "class EnhancementType(str, Enum):\n"
            '    """Types of enhancements that can be applied to '
            'a prototype."""\n'
            '    PRODUCTION = "production"\n'
            '    TESTING = "testing"\n'
            '    SECURITY = "security"\n\n\n'
            "@dataclass\n"
            "class PrototypeEnhancerInputs:\n"
            '    """Input model for the PrototypeEnhancer."""\n'
            "    platform: str\n"
            '    enhancement_type: "EnhancementType"\n'
            "    project_path: str\n"
            "    config: Optional[Dict[str, Any]] = None\n"
            "    dry_run: bool = False\n\n\n"
            "@dataclass\n"
            "class PrototypeEnhancerOutputs:\n"
            '    """Output model for the PrototypeEnhancer."""\n'
            "    success: bool\n"
            "    message: str\n"
            "    generated_files: List[str]\n"
            "    modified_files: List[str]\n"
            "    next_steps: List[str]\n"
            "    metadata: Optional[Dict[str, Any]] = None\n"
        )
        f.write(content)

# Create a placeholder for other model files
for model_file in ["base.py", "config.py", "events.py"]:
    file_path = package_dir / model_file
    if not file_path.exists():
        with file_path.open("w", encoding="utf-8") as f:
            model_name = model_file.capitalize().replace("_", " ").replace(
                ".py", ""
            )
            model_desc = model_file.replace("_", " ").replace(".py", "")
            content = (
                f'"""\n{model_name}\n\n'
                f'This module contains data models for {model_desc}.\n"""'
            )
            f.write(content)

# Export the models for easier imports
__all__ = [
    "EnhancementType",
    "PrototypeEnhancerInputs",
    "PrototypeEnhancerOutputs",
]
