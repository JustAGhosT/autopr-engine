"""
Enhancement Strategies Module

Handles platform-specific enhancement logic and package management for prototype enhancement.
"""

from pathlib import Path
from typing import Any

from autopr.actions.prototype_enhancement.file_generators import FileGenerator
from autopr.actions.prototype_enhancement.platform_configs import (
    PlatformConfig,
    PlatformRegistry,
)


class EnhancementStrategy:
    """Base class for platform-specific enhancement strategies."""

    def __init__(self, platform_config: PlatformConfig, file_generator: FileGenerator):
        self.config = platform_config
        self.file_generator = file_generator

    def enhance_project(self, project_path: Path, enhancement_type: str) -> dict[str, Any]:
        """Enhance a project based on the enhancement type."""
        msg = "Subclasses must implement enhance_project"
        raise NotImplementedError(msg)

    def get_package_updates(self, enhancement_type: str) -> dict[str, list[str]]:
        """Get package updates for the enhancement type."""
        msg = "Subclasses must implement get_package_updates"
        raise NotImplementedError(msg)

    def generate_files(self, enhancement_type: str) -> dict[str, str]:
        """Generate files for the enhancement type."""
        msg = "Subclasses must implement generate_files"
        raise NotImplementedError(msg)


class ReplitEnhancementStrategy(EnhancementStrategy):
    """Enhancement strategy for Replit projects."""

    def enhance_project(self, project_path: Path, enhancement_type: str) -> dict[str, Any]:
        """Enhance a Replit project."""
        result = {
            "platform": "replit",
            "enhancement_type": enhancement_type,
            "files_created": [],
            "packages_added": [],
            "configuration_updates": [],
            "next_steps": [],
        }

        if enhancement_type == "production_ready":
            result.update(self._enhance_for_production(project_path))
        elif enhancement_type == "testing":
            result.update(self._enhance_for_testing(project_path))
        elif enhancement_type == "security":
            result.update(self._enhance_for_security(project_path))

        return result

    def _enhance_for_production(self, project_path: Path) -> dict[str, Any]:
        """Enhance Replit project for production."""
        files_created: list[str] = []
        packages_added: list[str] = []
        config_updates: list[str] = []

        # Generate production files
        files = {
            "Dockerfile": self.file_generator.generate_dockerfile("replit"),
            ".env.example": self.file_generator.generate_security_files("replit")[".env.example"],
            "ecosystem.config.js": self._generate_pm2_config(),
        }

        files_created.extend(files.keys())

        # Production packages
        packages = [
            "helmet",
            "cors",
            "express-rate-limit",
            "compression",
            "morgan",
            "pm2",
        ]
        packages_added.extend(packages)

        config_updates.extend(
            [
                "Added security middleware configuration",
                "Configured process manager (PM2)",
                "Set up production logging",
                "Added health check endpoint",
            ]
        )

        return {
            "files_created": files_created,
            "packages_added": packages_added,
            "configuration_updates": config_updates,
            "files": files,
        }

    def _enhance_for_testing(self, project_path: Path) -> dict[str, Any]:
        """Enhance Replit project for testing."""
        files = self.file_generator.generate_testing_files("replit")
        packages = ["jest", "supertest", "mocha", "chai", "sinon"]

        return {
            "files_created": list(files.keys()),
            "packages_added": packages,
            "files": files,
        }

    def _enhance_for_security(self, project_path: Path) -> dict[str, Any]:
        """Enhance Replit project for security."""
        files = self.file_generator.generate_security_files("replit")
        packages = ["helmet", "cors", "express-rate-limit", "bcryptjs", "jsonwebtoken"]

        return {
            "files_created": list(files.keys()),
            "packages_added": packages,
            "files": files,
        }

    def _generate_pm2_config(self) -> str:
        """Generate PM2 ecosystem configuration."""
        return """
module.exports = {
  apps: [{
    name: 'app',
    script: 'index.js',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'development'
    },
    env_production: {
      NODE_ENV: 'production',
      PORT: 8080
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    max_memory_restart: '1G'
  }]
};
        """.strip()

    def get_package_updates(self, enhancement_type: str) -> dict[str, list[str]]:
        """Get package updates for Replit enhancement."""
        packages = PlatformRegistry.get_enhancement_packages()

        if enhancement_type == "production_ready":
            return {
                "dependencies": packages["security"]["common"] + packages["performance"]["common"],
                "devDependencies": [],
            }
        if enhancement_type == "testing":
            return {
                "dependencies": [],
                "devDependencies": packages["testing"]["common"],
            }
        if enhancement_type == "security":
            return {
                "dependencies": packages["security"]["common"],
                "devDependencies": [],
            }

        return {"dependencies": [], "devDependencies": []}

    def generate_files(self, enhancement_type: str) -> dict[str, str]:
        """Generate files for Replit enhancement."""
        if enhancement_type == "production_ready":
            return {
                "Dockerfile": self.file_generator.generate_dockerfile("replit"),
                ".env.example": self.file_generator.generate_security_files("replit")[
                    ".env.example"
                ],
                "ecosystem.config.js": self._generate_pm2_config(),
            }
        if enhancement_type == "testing":
            return self.file_generator.generate_testing_files("replit")
        if enhancement_type == "security":
            return self.file_generator.generate_security_files("replit")

        return {}


class LovableEnhancementStrategy(EnhancementStrategy):
    """Enhancement strategy for Lovable.dev projects."""

    def enhance_project(self, project_path: Path, enhancement_type: str) -> dict[str, Any]:
        """Enhance a Lovable.dev project."""
        result = {
            "platform": "lovable",
            "enhancement_type": enhancement_type,
            "files_created": [],
            "packages_added": [],
            "configuration_updates": [],
            "next_steps": [],
        }

        if enhancement_type == "production_ready":
            result.update(self._enhance_for_production(project_path))
        elif enhancement_type == "testing":
            result.update(self._enhance_for_testing(project_path))
        elif enhancement_type == "security":
            result.update(self._enhance_for_security(project_path))

        return result

    def _enhance_for_production(self, project_path: Path) -> dict[str, Any]:
        """Enhance Lovable project for production."""
        files = {
            "Dockerfile": self.file_generator.generate_dockerfile("lovable"),
            "tsconfig.json": self.file_generator.generate_typescript_config("lovable"),
            "src/utils/errorBoundary.tsx": self._generate_error_boundary(),
        }

        packages = [
            "@loadable/component",
            "react-window",
            "@sentry/react",
            "web-vitals",
        ]

        return {
            "files_created": list(files.keys()),
            "packages_added": packages,
            "configuration_updates": [
                "Added TypeScript strict configuration",
                "Implemented error boundaries",
                "Added performance monitoring",
            ],
            "files": files,
        }

    def _enhance_for_testing(self, project_path: Path) -> dict[str, Any]:
        """Enhance Lovable project for testing."""
        files = self.file_generator.generate_testing_files("lovable")
        files.update(self.file_generator.generate_accessibility_testing())

        packages = [
            "@testing-library/react",
            "@testing-library/jest-dom",
            "playwright",
            "jest-axe",
        ]

        return {
            "files_created": list(files.keys()),
            "packages_added": packages,
            "files": files,
        }

    def _enhance_for_security(self, project_path: Path) -> dict[str, Any]:
        """Enhance Lovable project for security."""
        files = self.file_generator.generate_security_files("lovable")
        packages = ["@types/bcryptjs", "@types/jsonwebtoken"]

        return {
            "files_created": list(files.keys()),
            "packages_added": packages,
            "files": files,
        }

    def _generate_error_boundary(self) -> str:
        """Generate React error boundary component."""
        return """
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
        """.strip()

    def get_package_updates(self, enhancement_type: str) -> dict[str, list[str]]:
        """Get package updates for Lovable enhancement."""
        packages = PlatformRegistry.get_enhancement_packages()

        if enhancement_type == "production_ready":
            return {
                "dependencies": packages["performance"]["react"] + packages["monitoring"]["react"],
                "devDependencies": packages["development"]["typescript"],
            }
        if enhancement_type == "testing":
            return {"dependencies": [], "devDependencies": packages["testing"]["react"]}
        if enhancement_type == "security":
            return {
                "dependencies": [],
                "devDependencies": packages["security"]["react"],
            }

        return {"dependencies": [], "devDependencies": []}

    def generate_files(self, enhancement_type: str) -> dict[str, str]:
        """Generate files for Lovable enhancement."""
        if enhancement_type == "production_ready":
            return {
                "Dockerfile": self.file_generator.generate_dockerfile("lovable"),
                "tsconfig.json": self.file_generator.generate_typescript_config("lovable"),
                "src/utils/errorBoundary.tsx": self._generate_error_boundary(),
            }
        if enhancement_type == "testing":
            files = self.file_generator.generate_testing_files("lovable")
            files.update(self.file_generator.generate_accessibility_testing())
            return files
        if enhancement_type == "security":
            return self.file_generator.generate_security_files("lovable")

        return {}


class BoltEnhancementStrategy(EnhancementStrategy):
    """Enhancement strategy for Bolt.new projects."""

    def enhance_project(self, project_path: Path, enhancement_type: str) -> dict[str, Any]:
        """Enhance a Bolt.new project."""
        result = {
            "platform": "bolt",
            "enhancement_type": enhancement_type,
            "files_created": [],
            "packages_added": [],
            "configuration_updates": [],
            "next_steps": [],
        }

        if enhancement_type == "production_ready":
            result.update(self._enhance_for_production(project_path))
        elif enhancement_type == "testing":
            result.update(self._enhance_for_testing(project_path))
        elif enhancement_type == "security":
            result.update(self._enhance_for_security(project_path))

        return result

    def _enhance_for_production(self, project_path: Path) -> dict[str, Any]:
        """Enhance Bolt project for production."""
        files = {
            "vite.config.ts": self._generate_vite_config(),
            "tsconfig.json": self.file_generator.generate_typescript_config("bolt"),
            "Dockerfile": self.file_generator.generate_dockerfile("bolt"),
        }

        packages = ["@vitejs/plugin-react", "vite-plugin-pwa", "@sentry/react"]

        return {
            "files_created": list(files.keys()),
            "packages_added": packages,
            "configuration_updates": [
                "Optimized Vite configuration for production",
                "Added Progressive Web App features",
                "Set up error monitoring with Sentry",
            ],
            "files": files,
        }

    def _enhance_for_testing(self, project_path: Path) -> dict[str, Any]:
        """Enhance Bolt project for testing."""
        files = {
            "vitest.config.ts": self._generate_vitest_config(),
            "src/test/setup.ts": self._generate_test_setup(),
        }

        packages = ["vitest", "@vitest/ui", "jsdom", "@testing-library/react"]

        return {
            "files_created": list(files.keys()),
            "packages_added": packages,
            "files": files,
        }

    def _enhance_for_security(self, project_path: Path) -> dict[str, Any]:
        """Enhance Bolt project for security."""
        files = self.file_generator.generate_security_files("bolt")
        packages = ["@types/bcryptjs", "@types/jsonwebtoken"]

        return {
            "files_created": list(files.keys()),
            "packages_added": packages,
            "files": files,
        }

    def _generate_vite_config(self) -> str:
        """Generate optimized Vite configuration."""
        return """
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}']
      }
    })
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom']
        }
      }
    },
    sourcemap: true
  },
  server: {
    port: 3000,
    host: true
  }
});
        """.strip()

    def _generate_vitest_config(self) -> str:
        """Generate Vitest configuration."""
        return """
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html']
    }
  }
});
        """.strip()

    def _generate_test_setup(self) -> str:
        """Generate test setup file."""
        return """
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
});

global.IntersectionObserver = vi.fn(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  unobserve: vi.fn()
}));
        """.strip()

    def get_package_updates(self, enhancement_type: str) -> dict[str, list[str]]:
        """Get package updates for Bolt enhancement."""
        packages = PlatformRegistry.get_enhancement_packages()

        if enhancement_type == "production_ready":
            return {
                "dependencies": [
                    "@vitejs/plugin-react",
                    "vite-plugin-pwa",
                    "@sentry/react",
                ],
                "devDependencies": packages["development"]["typescript"],
            }
        if enhancement_type == "testing":
            return {
                "dependencies": [],
                "devDependencies": ["vitest", "@vitest/ui", "jsdom"] + packages["testing"]["react"],
            }
        if enhancement_type == "security":
            return {
                "dependencies": [],
                "devDependencies": packages["security"]["react"],
            }

        return {"dependencies": [], "devDependencies": []}

    def generate_files(self, enhancement_type: str) -> dict[str, str]:
        """Generate files for Bolt enhancement."""
        if enhancement_type == "production_ready":
            return {
                "vite.config.ts": self._generate_vite_config(),
                "tsconfig.json": self.file_generator.generate_typescript_config("bolt"),
                "Dockerfile": self.file_generator.generate_dockerfile("bolt"),
            }
        if enhancement_type == "testing":
            return {
                "vitest.config.ts": self._generate_vitest_config(),
                "src/test/setup.ts": self._generate_test_setup(),
            }
        if enhancement_type == "security":
            return self.file_generator.generate_security_files("bolt")

        return {}


class EnhancementStrategyFactory:
    """Factory for creating platform-specific enhancement strategies."""

    @staticmethod
    def create_strategy(platform: str) -> EnhancementStrategy:
        """Create an enhancement strategy for the given platform."""
        platform_config = PlatformRegistry.get_platform_config(platform)
        file_generator = FileGenerator()

        if platform == "replit":
            return ReplitEnhancementStrategy(platform_config, file_generator)
        if platform == "lovable":
            return LovableEnhancementStrategy(platform_config, file_generator)
        if platform == "bolt":
            return BoltEnhancementStrategy(platform_config, file_generator)

        # Generic strategy for other platforms - create a basic implementation
        class GenericEnhancementStrategy(EnhancementStrategy):
            def enhance_project(self, project_path: Path, enhancement_type: str) -> dict[str, Any]:
                return {
                    "platform": platform,
                    "enhancement_type": enhancement_type,
                    "files_created": [],
                    "packages_added": [],
                    "configuration_updates": [],
                    "next_steps": [],
                }

            def get_package_updates(self, enhancement_type: str) -> dict[str, list[str]]:
                return {"dependencies": [], "devDependencies": []}

            def generate_files(self, enhancement_type: str) -> dict[str, str]:
                return {}

        return GenericEnhancementStrategy(platform_config, file_generator)
