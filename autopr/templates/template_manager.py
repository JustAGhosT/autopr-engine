"""
Template Manager
Handles all template operations and discovery
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TemplateInfo:
    name: str
    category: str
    platform: str
    confidence: float
    files: list[str]
    dependencies: list[str]


class TemplateManager:
    """Template management system"""

    def __init__(self, config_path: str = "configs/config.yaml"):
        self.config = self._load_config(config_path)
        self.templates_cache: dict[str, TemplateInfo] = {}
        self._load_templates()

    def discover_templates(self, project_path: Path) -> list[TemplateInfo]:
        """Auto-discover templates based on project structure"""
        discovered = []

        for template_name, template_info in self.templates_cache.items():
            confidence = self._calculate_confidence(project_path, template_info)
            if confidence >= self.config["templates"]["confidence_threshold"]:
                template_info.confidence = confidence
                discovered.append(template_info)

        return sorted(discovered, key=lambda t: t.confidence, reverse=True)

    def generate_from_template(self, template_name: str, context: dict[str, Any]) -> dict[str, str]:
        """Generate files from template with context"""
        # Implementation details...

    def _load_templates(self):
        """Load all template definitions"""
        templates_dir = Path("templates")
        config_dir = Path("configs")

        # Load platform templates
        for platform_file in (templates_dir / "platforms").glob("**/*.yml"):
            self._load_template_file(platform_file)

        # Load build templates
        for build_file in (templates_dir / "build").glob("**/*.yml"):
            self._load_template_file(build_file)

        # Load configuration templates
        for config_file in (config_dir / "platforms").glob("**/*.json"):
            self._load_config_template(config_file)
