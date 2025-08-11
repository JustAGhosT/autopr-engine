"""
Main Prototype Enhancer Module

Orchestrates all modular components and provides the same interface as the original PrototypeEnhancer
for backward compatibility while improving maintainability and testability.
"""

from dataclasses import asdict
import logging
from pathlib import Path
from typing import Any

try:
    from autopr.models.artifacts import (  # type: ignore[import-untyped]
        PrototypeEnhancerInputs,
        PrototypeEnhancerOutputs,
    )
except ImportError:
    # Fallback for when models are not available during development
    from typing import Any as PrototypeEnhancerInputs
    from typing import Any as PrototypeEnhancerOutputs

from .enhancement_strategies import EnhancementStrategy, EnhancementStrategyFactory
from .file_generators import FileGenerator
from .platform_configs import PlatformConfig, PlatformRegistry

logger = logging.getLogger(__name__)


class PrototypeEnhancer:
    """
    Modular prototype enhancer that provides platform-specific enhancements
    for production readiness, testing, and security.

    This class maintains backward compatibility with the original PrototypeEnhancer
    while providing improved modularity and maintainability.
    """

    def __init__(self) -> None:
        """Initialize the prototype enhancer with modular components."""
        self.platform_registry = PlatformRegistry()
        self.file_generator = FileGenerator()
        self.enhancement_strategies: dict[str, EnhancementStrategy] = {}

        # Initialize strategies for all supported platforms
        for platform in self.platform_registry.get_platform_configs():
            self.enhancement_strategies[platform] = EnhancementStrategyFactory.create_strategy(
                platform
            )

        logger.info("PrototypeEnhancer initialized with modular architecture")

    def enhance(self, inputs: PrototypeEnhancerInputs) -> PrototypeEnhancerOutputs:
        """
        Main enhancement method that maintains backward compatibility.

        Args:
            inputs: PrototypeEnhancerInputs containing platform and enhancement type

        Returns:
            PrototypeEnhancerOutputs with enhancement results
        """
        try:
            logger.info(
                f"Starting enhancement for platform: {inputs.platform}, type: {inputs.enhancement_type}"
            )

            # Validate platform support
            if not self.platform_registry.is_supported_platform(inputs.platform):
                return self._create_error_output(f"Unsupported platform: {inputs.platform}")

            # Get platform configuration
            platform_config = self.platform_registry.get_platform_config(inputs.platform)

            # Perform enhancement based on type
            if inputs.enhancement_type == "production_ready":
                result = self._enhance_for_production(inputs, platform_config)
            elif inputs.enhancement_type == "testing":
                result = self._enhance_for_testing(inputs, platform_config)
            elif inputs.enhancement_type == "security":
                result = self._enhance_for_security(inputs, platform_config)
            else:
                return self._create_error_output(
                    f"Unsupported enhancement type: {inputs.enhancement_type}"
                )

            logger.info(f"Enhancement completed successfully for {inputs.platform}")
            return result

        except Exception as e:
            logger.exception(f"Enhancement failed: {e!s}")
            return self._create_error_output(f"Enhancement failed: {e!s}")

    def _enhance_for_production(
        self, inputs: PrototypeEnhancerInputs, config: PlatformConfig
    ) -> PrototypeEnhancerOutputs:
        """Enhance project for production readiness."""
        strategy = self.enhancement_strategies[inputs.platform]
        project_path = Path(inputs.project_path) if inputs.project_path else Path.cwd()

        # Get enhancement results
        enhancement_result = strategy.enhance_project(project_path, "production_ready")

        # Get package updates
        package_updates = strategy.get_package_updates("production_ready")

        # Generate package.json updates
        package_json_updates = self._generate_package_json_updates(
            package_updates["dependencies"], package_updates["devDependencies"]
        )

        # Get production checklist
        production_checklist = self.platform_registry.get_production_checklists()[inputs.platform]

        # Get next steps
        next_steps = self.platform_registry.get_next_steps()[inputs.platform]["production_ready"]

        return PrototypeEnhancerOutputs(
            enhanced_files=enhancement_result.get("files", {}),
            package_json_updates=package_json_updates,
            deployment_configs=self._get_deployment_configs(inputs.platform),
            production_checklist=production_checklist,
            next_steps=next_steps,
            enhancement_summary=self._create_enhancement_summary(enhancement_result),
            platform_specific_notes=self._get_platform_notes(inputs.platform, "production_ready"),
        )

    def _enhance_for_testing(
        self, inputs: PrototypeEnhancerInputs, config: PlatformConfig
    ) -> PrototypeEnhancerOutputs:
        """Enhance project for testing."""
        strategy = self.enhancement_strategies[inputs.platform]
        project_path = Path(inputs.project_path) if inputs.project_path else Path.cwd()

        # Get enhancement results
        enhancement_result = strategy.enhance_project(project_path, "testing")

        # Get package updates
        package_updates = strategy.get_package_updates("testing")

        # Generate package.json updates
        package_json_updates = self._generate_package_json_updates(
            package_updates["dependencies"], package_updates["devDependencies"]
        )

        # Get testing-specific checklist
        testing_checklist = [
            "✅ Unit tests configured",
            "✅ Integration tests setup",
            "✅ Test coverage reporting enabled",
            "✅ CI/CD pipeline includes testing",
            "✅ Test data and fixtures created",
            "✅ Mocking and stubbing configured",
            "✅ Performance testing setup",
            "✅ Accessibility testing enabled",
            "✅ Visual regression testing configured",
            "✅ Test documentation created",
        ]

        # Get next steps
        next_steps = self.platform_registry.get_next_steps()[inputs.platform]["testing"]

        return PrototypeEnhancerOutputs(
            enhanced_files=enhancement_result.get("files", {}),
            package_json_updates=package_json_updates,
            deployment_configs={},
            production_checklist=testing_checklist,
            next_steps=next_steps,
            enhancement_summary=self._create_enhancement_summary(enhancement_result),
            platform_specific_notes=self._get_platform_notes(inputs.platform, "testing"),
        )

    def _enhance_for_security(
        self, inputs: PrototypeEnhancerInputs, config: PlatformConfig
    ) -> PrototypeEnhancerOutputs:
        """Enhance project for security."""
        strategy = self.enhancement_strategies[inputs.platform]
        project_path = Path(inputs.project_path) if inputs.project_path else Path.cwd()

        # Get enhancement results
        enhancement_result = strategy.enhance_project(project_path, "security")

        # Get package updates
        package_updates = strategy.get_package_updates("security")

        # Generate package.json updates
        package_json_updates = self._generate_package_json_updates(
            package_updates["dependencies"], package_updates["devDependencies"]
        )

        # Get security-specific checklist
        security_checklist = [
            "✅ Security headers configured",
            "✅ Input validation implemented",
            "✅ Authentication system secured",
            "✅ Authorization rules defined",
            "✅ CORS properly configured",
            "✅ Rate limiting enabled",
            "✅ SQL injection protection",
            "✅ XSS protection implemented",
            "✅ CSRF protection enabled",
            "✅ Security monitoring setup",
        ]

        # Get next steps
        next_steps = self.platform_registry.get_next_steps()[inputs.platform]["security"]

        return PrototypeEnhancerOutputs(
            enhanced_files=enhancement_result.get("files", {}),
            package_json_updates=package_json_updates,
            deployment_configs={},
            production_checklist=security_checklist,
            next_steps=next_steps,
            enhancement_summary=self._create_enhancement_summary(enhancement_result),
            platform_specific_notes=self._get_platform_notes(inputs.platform, "security"),
        )

    def _generate_package_json_updates(
        self, dependencies: list[str], dev_dependencies: list[str]
    ) -> dict[str, Any]:
        """Generate package.json updates."""
        updates = {}

        if dependencies:
            updates["dependencies"] = dict.fromkeys(dependencies, "latest")

        if dev_dependencies:
            updates["devDependencies"] = dict.fromkeys(dev_dependencies, "latest")

        # Add common scripts based on enhancement type
        updates["scripts"] = {
            "test": "npm run test:unit && npm run test:integration",
            "test:unit": "jest",
            "test:integration": "jest --config jest.integration.config.js",
            "test:coverage": "jest --coverage",
            "lint": "eslint src/",
            "lint:fix": "eslint src/ --fix",
            "build": "npm run build:prod",
            "build:prod": "NODE_ENV=production npm run build",
            "start:prod": "NODE_ENV=production npm start",
            "health-check": "curl -f http://localhost:3000/health || exit 1",
        }

        return updates

    def _get_deployment_configs(self, platform: str) -> dict[str, Any]:
        """Get deployment configurations for the platform."""
        return self.platform_registry.get_deployment_configs().get(platform, {})

    def _create_enhancement_summary(self, enhancement_result: dict[str, Any]) -> str:
        """Create a summary of the enhancement process."""
        files_count = len(enhancement_result.get("files_created", []))
        packages_count = len(enhancement_result.get("packages_added", []))
        config_count = len(enhancement_result.get("configuration_updates", []))

        summary_parts = [
            f"Enhanced {enhancement_result.get('platform', 'unknown')} project for {enhancement_result.get('enhancement_type', 'unknown')}",
            f"Created {files_count} configuration files",
            f"Added {packages_count} packages",
            f"Applied {config_count} configuration updates",
        ]

        return ". ".join(summary_parts) + "."

    def _get_platform_notes(self, platform: str, enhancement_type: str) -> list[str]:
        """Get platform-specific notes for the enhancement."""
        notes = {
            "replit": {
                "production_ready": [
                    "Configure environment variables in Replit Secrets",
                    "Set up database connection in production environment",
                    "Enable always-on for production deployments",
                    "Configure custom domain if needed",
                    "Set up monitoring and alerting",
                ],
                "testing": [
                    "Run tests in Replit console with 'npm test'",
                    "Configure test database separately",
                    "Set up automated testing in CI/CD pipeline",
                    "Use Replit's built-in debugging tools",
                ],
                "security": [
                    "Store sensitive data in Replit Secrets",
                    "Configure HTTPS for production",
                    "Review and update CORS settings",
                    "Enable rate limiting for API endpoints",
                ],
            },
            "lovable": {
                "production_ready": [
                    "Optimize bundle size for faster loading",
                    "Configure CDN for static assets",
                    "Set up error boundaries for better UX",
                    "Implement progressive loading",
                    "Configure analytics and monitoring",
                ],
                "testing": [
                    "Set up component testing with React Testing Library",
                    "Configure visual regression testing",
                    "Implement accessibility testing",
                    "Set up Storybook for component documentation",
                ],
                "security": [
                    "Implement Content Security Policy",
                    "Configure secure API communication",
                    "Set up dependency vulnerability scanning",
                    "Implement XSS protection",
                ],
            },
            "bolt": {
                "production_ready": [
                    "Optimize Vite configuration for production",
                    "Configure Progressive Web App features",
                    "Set up code splitting and lazy loading",
                    "Implement state management",
                    "Configure deployment pipeline",
                ],
                "testing": [
                    "Set up Vitest for fast unit testing",
                    "Configure component testing",
                    "Implement API testing",
                    "Set up visual testing with Playwright",
                ],
                "security": [
                    "Configure secure API calls",
                    "Implement authentication flow",
                    "Set up input sanitization",
                    "Configure security headers",
                ],
            },
        }

        return notes.get(platform, {}).get(enhancement_type, [])

    def _create_error_output(self, error_message: str) -> PrototypeEnhancerOutputs:
        """Create an error output."""
        return PrototypeEnhancerOutputs(
            enhanced_files={},
            package_json_updates={},
            deployment_configs={},
            production_checklist=[],
            next_steps=[f"Error: {error_message}"],
            enhancement_summary=f"Enhancement failed: {error_message}",
            platform_specific_notes=[],
        )

    def get_supported_platforms(self) -> list[str]:
        """Get list of supported platforms."""
        return list(self.platform_registry.get_platform_configs().keys())

    def get_platform_info(self, platform: str) -> dict[str, Any] | None:
        """Get information about a specific platform."""
        if not self.platform_registry.is_supported_platform(platform):
            return None

        config = self.platform_registry.get_platform_config(platform)
        return asdict(config)

    def get_enhancement_types(self) -> list[str]:
        """Get list of supported enhancement types."""
        return ["production_ready", "testing", "security"]

    def validate_inputs(self, inputs: PrototypeEnhancerInputs) -> list[str]:
        """Validate enhancement inputs and return any errors."""
        errors = []

        if not inputs.platform:
            errors.append("Platform is required")
        elif not self.platform_registry.is_supported_platform(inputs.platform):
            errors.append(f"Unsupported platform: {inputs.platform}")

        if not inputs.enhancement_type:
            errors.append("Enhancement type is required")
        elif inputs.enhancement_type not in self.get_enhancement_types():
            errors.append(f"Unsupported enhancement type: {inputs.enhancement_type}")

        if inputs.project_path and not Path(inputs.project_path).exists():
            errors.append(f"Project path does not exist: {inputs.project_path}")

        return errors

    def get_enhancement_preview(self, inputs: PrototypeEnhancerInputs) -> dict[str, Any]:
        """Get a preview of what the enhancement will do without actually performing it."""
        validation_errors = self.validate_inputs(inputs)
        if validation_errors:
            return {"errors": validation_errors}

        strategy = self.enhancement_strategies[inputs.platform]
        package_updates = strategy.get_package_updates(inputs.enhancement_type)

        return {
            "platform": inputs.platform,
            "enhancement_type": inputs.enhancement_type,
            "files_to_create": list(strategy.generate_files(inputs.enhancement_type).keys()),
            "packages_to_add": {
                "dependencies": package_updates["dependencies"],
                "devDependencies": package_updates["devDependencies"],
            },
            "checklist_items": len(
                self.platform_registry.get_production_checklists().get(inputs.platform, [])
            ),
            "next_steps_count": len(
                self.platform_registry.get_next_steps()
                .get(inputs.platform, {})
                .get(inputs.enhancement_type, [])
            ),
        }
