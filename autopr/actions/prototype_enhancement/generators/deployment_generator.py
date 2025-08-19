"""
Deployment Generator Module

Handles generation of deployment-related configuration files and scripts
for different platforms and deployment targets.
"""

import logging
from pathlib import Path
from typing import Any

from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class DeploymentGenerator(BaseGenerator):
    """
    Generates deployment configuration files for various platforms.
    """

    def __init__(self, template_dir: Path | None = None):
        """
        Initialize the deployment generator.

        Args:
            template_dir: Optional directory containing custom templates
        """
        super().__init__(template_dir)
        self.template_name = "deployment"

    def generate(
        self,
        platform: str,
        output_dir: Path,
        context: dict[str, Any] | None = None,
    ) -> list[Path]:
        """
        Generate deployment configuration files.

        Args:
            platform: Target platform (e.g., 'replit', 'vercel', 'render')
            output_dir: Directory to write generated files to
            context: Additional context for template rendering

        Returns:
            List of Path objects to generated files
        """
        if context is None:
            context = {}

        # Add platform-specific context
        context["platform"] = platform

        # Generate platform-specific deployment files
        if platform == "replit":
            return self._generate_replit_deployment(output_dir, context)
        if platform == "vercel":
            return self._generate_vercel_deployment(output_dir, context)
        if platform == "render":
            return self._generate_render_deployment(output_dir, context)
        logger.warning(f"Unsupported deployment platform: {platform}")
        return []

    def _generate_replit_deployment(self, output_dir: Path, context: dict[str, Any]) -> list[Path]:
        """Generate Replit-specific deployment files."""
        generated_files = []

        # Generate .replit file
        replit_config = self._render_template("replit_config.toml", context)
        if replit_config:
            replit_path = output_dir / ".replit"
            replit_path.write_text(replit_config)
            generated_files.append(replit_path)

        # Generate replit.nix if needed
        if context.get("needs_custom_environment"):
            replit_nix = self._render_template("replit.nix", context)
            if replit_nix:
                nix_path = output_dir / "replit.nix"
                nix_path.write_text(replit_nix)
                generated_files.append(nix_path)

        return generated_files

    def _generate_vercel_deployment(self, output_dir: Path, context: dict[str, Any]) -> list[Path]:
        """Generate Vercel deployment configuration."""
        generated_files = []

        # Generate vercel.json
        vercel_config = self._render_template("vercel.json", context)
        if vercel_config:
            vercel_path = output_dir / "vercel.json"
            vercel_path.write_text(vercel_config)
            generated_files.append(vercel_path)

        return generated_files

    def _generate_render_deployment(self, output_dir: Path, context: dict[str, Any]) -> list[Path]:
        """Generate Render deployment configuration."""
        generated_files = []

        # Generate render.yaml
        render_config = self._render_template("render.yaml", context)
        if render_config:
            render_path = output_dir / "render.yaml"
            render_path.write_text(render_config)
            generated_files.append(render_path)

        return generated_files
