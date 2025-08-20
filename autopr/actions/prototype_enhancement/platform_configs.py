"""
Platform Configuration Module

Centralized platform definitions and enhancement configurations for prototype enhancement.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlatformConfig:
    """Configuration for a specific platform."""

    name: str
    display_name: str
    description: str
    primary_language: str
    framework: str
    deployment_targets: list[str] = field(default_factory=list)
    common_files: list[str] = field(default_factory=list)
    package_manager: str = "npm"
    build_command: str = "npm run build"
    start_command: str = "npm start"
    test_command: str = "npm test"


class PlatformRegistry:
    """Registry for all supported platforms and their configurations."""

    @staticmethod
    def get_platform_configs() -> dict[str, PlatformConfig]:
        """Get all platform configurations."""
        return {
            "replit": PlatformConfig(
                name="replit",
                display_name="Replit",
                description="Replit-generated web applications",
                primary_language="javascript",
                framework="express",
                deployment_targets=["azure", "vercel", "railway"],
                common_files=[
                    "package.json",
                    "index.js",
                    "server.js",
                    "public/index.html",
                    "public/style.css",
                    "public/script.js",
                ],
                package_manager="npm",
                build_command="npm run build",
                start_command="npm start",
                test_command="npm test",
            ),
            "lovable": PlatformConfig(
                name="lovable",
                display_name="Lovable.dev",
                description="Lovable.dev React applications",
                primary_language="typescript",
                framework="react",
                deployment_targets=["vercel", "netlify", "azure"],
                common_files=[
                    "package.json",
                    "src/App.tsx",
                    "src/index.tsx",
                    "src/components/",
                    "public/index.html",
                    "tsconfig.json",
                ],
                package_manager="npm",
                build_command="npm run build",
                start_command="npm start",
                test_command="npm test",
            ),
            "bolt": PlatformConfig(
                name="bolt",
                display_name="Bolt.new",
                description="Bolt.new full-stack applications",
                primary_language="typescript",
                framework="react",
                deployment_targets=["vercel", "railway", "render"],
                common_files=[
                    "package.json",
                    "src/App.tsx",
                    "src/main.tsx",
                    "src/components/",
                    "src/lib/",
                    "index.html",
                    "vite.config.ts",
                ],
                package_manager="npm",
                build_command="npm run build",
                start_command="npm run dev",
                test_command="npm test",
            ),
            "same": PlatformConfig(
                name="same",
                display_name="Same.new",
                description="Same.new cloned applications",
                primary_language="javascript",
                framework="various",
                deployment_targets=["vercel", "netlify", "github-pages"],
                common_files=["package.json", "README.md", "src/", "public/"],
                package_manager="npm",
                build_command="npm run build",
                start_command="npm start",
                test_command="npm test",
            ),
            "emergent": PlatformConfig(
                name="emergent",
                display_name="Emergent.sh",
                description="Emergent.sh automation projects",
                primary_language="javascript",
                framework="node",
                deployment_targets=["railway", "render", "azure"],
                common_files=[
                    "package.json",
                    "index.js",
                    "lib/",
                    "config/",
                    "scripts/",
                ],
                package_manager="npm",
                build_command="npm run build",
                start_command="npm start",
                test_command="npm test",
            ),
        }

    @staticmethod
    def get_enhancement_packages() -> dict[str, dict[str, list[str]]]:
        """Get enhancement packages by category and platform."""
        return {
            "security": {
                "common": [
                    "helmet",
                    "cors",
                    "express-rate-limit",
                    "bcryptjs",
                    "jsonwebtoken",
                    "express-validator",
                ],
                "react": ["@types/bcryptjs", "@types/jsonwebtoken"],
                "node": ["dotenv", "express-session"],
            },
            "performance": {
                "common": ["compression", "morgan", "cluster", "pm2"],
                "react": ["@loadable/component", "react-window", "react-virtualized"],
                "node": ["node-cache", "redis"],
            },
            "monitoring": {
                "common": [
                    "@azure/monitor-opentelemetry-exporter",
                    "winston",
                    "express-prometheus-middleware",
                ],
                "react": ["@sentry/react", "web-vitals"],
                "node": ["@sentry/node", "pino"],
            },
            "testing": {
                "common": ["jest", "supertest"],
                "react": [
                    "@testing-library/react",
                    "@testing-library/jest-dom",
                    "@testing-library/user-event",
                    "playwright",
                ],
                "node": ["mocha", "chai", "sinon"],
            },
            "development": {
                "common": ["nodemon", "concurrently"],
                "react": [
                    "@storybook/react",
                    "@storybook/addon-essentials",
                    "eslint-plugin-react",
                    "prettier",
                ],
                "typescript": [
                    "typescript",
                    "@types/node",
                    "ts-node",
                    "eslint",
                    "@typescript-eslint/parser",
                    "@typescript-eslint/eslint-plugin",
                ],
            },
        }

    @staticmethod
    def get_production_checklists() -> dict[str, list[str]]:
        """Get production readiness checklists by platform."""
        return {
            "replit": [
                "✅ Environment variables configured",
                "✅ Database connection secured",
                "✅ Error handling implemented",
                "✅ Logging configured",
                "✅ Rate limiting enabled",
                "✅ CORS configured properly",
                "✅ Security headers added",
                "✅ Health check endpoint created",
                "✅ Process manager configured (PM2)",
                "✅ Monitoring and alerting setup",
            ],
            "lovable": [
                "✅ TypeScript configuration optimized",
                "✅ Build process configured",
                "✅ Environment variables setup",
                "✅ Error boundaries implemented",
                "✅ Performance monitoring added",
                "✅ Accessibility testing setup",
                "✅ SEO optimization implemented",
                "✅ Progressive Web App features",
                "✅ Code splitting configured",
                "✅ Bundle size optimization",
            ],
            "bolt": [
                "✅ Vite configuration optimized",
                "✅ TypeScript strict mode enabled",
                "✅ Component testing setup",
                "✅ State management configured",
                "✅ API integration secured",
                "✅ Error handling implemented",
                "✅ Performance optimization",
                "✅ Build optimization",
                "✅ Deployment configuration",
                "✅ Monitoring setup",
            ],
            "same": [
                "✅ Dependencies updated",
                "✅ Security vulnerabilities fixed",
                "✅ Build process verified",
                "✅ Testing framework added",
                "✅ Documentation updated",
                "✅ License compliance checked",
                "✅ Performance baseline established",
                "✅ Deployment strategy defined",
                "✅ Monitoring configured",
                "✅ Backup strategy implemented",
            ],
            "emergent": [
                "✅ Automation scripts tested",
                "✅ Error handling robust",
                "✅ Logging comprehensive",
                "✅ Configuration externalized",
                "✅ Security credentials secured",
                "✅ Rate limiting implemented",
                "✅ Health checks configured",
                "✅ Monitoring and alerting",
                "✅ Backup and recovery",
                "✅ Documentation complete",
            ],
        }

    @staticmethod
    def get_deployment_configs() -> dict[str, dict[str, Any]]:
        """Get deployment configurations by platform."""
        return {
            "replit": {
                "azure": {
                    "app_service": True,
                    "runtime": "node",
                    "version": "18",
                    "startup_command": "npm start",
                    "environment_variables": ["NODE_ENV=production", "PORT=8080"],
                },
                "vercel": {
                    "framework": "other",
                    "build_command": "npm run build",
                    "output_directory": "dist",
                    "install_command": "npm install",
                },
                "railway": {
                    "start_command": "npm start",
                    "build_command": "npm run build",
                    "healthcheck_path": "/health",
                },
            },
            "lovable": {
                "vercel": {
                    "framework": "create-react-app",
                    "build_command": "npm run build",
                    "output_directory": "build",
                    "install_command": "npm install",
                },
                "netlify": {
                    "build_command": "npm run build",
                    "publish_directory": "build",
                    "node_version": "18",
                },
                "azure": {
                    "app_service": True,
                    "runtime": "node",
                    "version": "18",
                    "build_command": "npm run build",
                },
            },
            "bolt": {
                "vercel": {
                    "framework": "vite",
                    "build_command": "npm run build",
                    "output_directory": "dist",
                    "install_command": "npm install",
                },
                "railway": {
                    "start_command": "npm run preview",
                    "build_command": "npm run build",
                    "healthcheck_path": "/",
                },
                "render": {
                    "build_command": "npm run build",
                    "start_command": "npm run preview",
                    "environment": "node",
                },
            },
            "same": {
                "vercel": {
                    "framework": "other",
                    "build_command": "npm run build",
                    "output_directory": "dist",
                },
                "netlify": {
                    "build_command": "npm run build",
                    "publish_directory": "dist",
                },
                "github-pages": {
                    "build_command": "npm run build",
                    "output_directory": "dist",
                    "base_path": "/",
                },
            },
            "emergent": {
                "railway": {
                    "start_command": "npm start",
                    "build_command": "npm run build",
                    "healthcheck_path": "/health",
                },
                "render": {
                    "build_command": "npm run build",
                    "start_command": "npm start",
                    "environment": "node",
                },
                "azure": {
                    "app_service": True,
                    "runtime": "node",
                    "version": "18",
                    "startup_command": "npm start",
                },
            },
        }

    @staticmethod
    def get_next_steps() -> dict[str, dict[str, list[str]]]:
        """Get next steps by platform and enhancement type."""
        return {
            "replit": {
                "production_ready": [
                    "Set up environment variables in production",
                    "Configure database connection string",
                    "Set up monitoring and alerting",
                    "Configure SSL certificate",
                    "Set up backup strategy",
                    "Implement CI/CD pipeline",
                    "Configure load balancing if needed",
                    "Set up log aggregation",
                    "Implement security scanning",
                    "Create runbook for operations",
                ],
                "testing": [
                    "Write unit tests for core functionality",
                    "Set up integration testing",
                    "Configure test database",
                    "Implement API testing",
                    "Set up automated testing pipeline",
                ],
                "security": [
                    "Implement authentication system",
                    "Set up authorization rules",
                    "Configure security headers",
                    "Implement input validation",
                    "Set up security monitoring",
                ],
            },
            "lovable": {
                "production_ready": [
                    "Optimize bundle size",
                    "Implement code splitting",
                    "Set up error boundaries",
                    "Configure performance monitoring",
                    "Implement SEO optimization",
                    "Set up analytics tracking",
                    "Configure PWA features",
                    "Implement accessibility features",
                    "Set up A/B testing framework",
                    "Configure CDN for assets",
                ],
                "testing": [
                    "Write component tests",
                    "Set up visual regression testing",
                    "Implement accessibility testing",
                    "Configure performance testing",
                    "Set up end-to-end testing",
                ],
                "security": [
                    "Implement CSP headers",
                    "Set up dependency scanning",
                    "Configure secure API communication",
                    "Implement XSS protection",
                    "Set up security monitoring",
                ],
            },
            "bolt": {
                "production_ready": [
                    "Optimize Vite configuration",
                    "Implement state management",
                    "Set up API integration",
                    "Configure error handling",
                    "Implement performance monitoring",
                    "Set up deployment pipeline",
                    "Configure environment management",
                    "Implement logging strategy",
                    "Set up monitoring dashboard",
                    "Create deployment documentation",
                ],
                "testing": [
                    "Set up Vitest configuration",
                    "Write component tests",
                    "Implement API testing",
                    "Configure visual testing",
                    "Set up performance testing",
                ],
                "security": [
                    "Implement secure API calls",
                    "Set up authentication flow",
                    "Configure CORS properly",
                    "Implement input sanitization",
                    "Set up security headers",
                ],
            },
            "same": {
                "production_ready": [
                    "Update all dependencies",
                    "Fix security vulnerabilities",
                    "Implement proper error handling",
                    "Set up monitoring",
                    "Configure deployment strategy",
                    "Implement backup solution",
                    "Set up performance monitoring",
                    "Create documentation",
                    "Implement testing strategy",
                    "Set up CI/CD pipeline",
                ],
                "testing": [
                    "Add comprehensive test suite",
                    "Set up automated testing",
                    "Implement integration tests",
                    "Configure test coverage",
                    "Set up quality gates",
                ],
                "security": [
                    "Audit dependencies",
                    "Implement security headers",
                    "Set up vulnerability scanning",
                    "Configure secure deployment",
                    "Implement security monitoring",
                ],
            },
            "emergent": {
                "production_ready": [
                    "Implement robust error handling",
                    "Set up comprehensive logging",
                    "Configure monitoring and alerting",
                    "Implement rate limiting",
                    "Set up health checks",
                    "Configure backup strategy",
                    "Implement security measures",
                    "Set up deployment automation",
                    "Create operational documentation",
                    "Implement performance optimization",
                ],
                "testing": [
                    "Write automation tests",
                    "Set up integration testing",
                    "Implement load testing",
                    "Configure test environments",
                    "Set up automated validation",
                ],
                "security": [
                    "Secure API endpoints",
                    "Implement authentication",
                    "Set up authorization",
                    "Configure secure communication",
                    "Implement audit logging",
                ],
            },
        }

    @staticmethod
    def is_supported_platform(platform: str) -> bool:
        """Check if a platform is supported."""
        return platform in PlatformRegistry.get_platform_configs()

    @staticmethod
    def get_platform_config(platform: str) -> PlatformConfig:
        """Get configuration for a specific platform."""
        configs = PlatformRegistry.get_platform_configs()
        if platform not in configs:
            msg = f"Unsupported platform: {platform}"
            raise ValueError(msg)
        return configs[platform]
