"""
File Generation Module

Handles generation of configuration, testing, security, and deployment files for prototype enhancement.
Now supports hybrid YAML + template approach for enhanced metadata and flexibility.
"""

import json
from pathlib import Path
from typing import Any

from .config_loader import ConfigLoader
from .platform_configs import PlatformConfig, PlatformRegistry
from .template_metadata import TemplateRegistry


class FileGenerator:
    """Generates various configuration and setup files for different platforms.

    Now supports hybrid YAML + template approach with metadata-driven generation.
    """

    def __init__(self, templates_dir: str | None = None) -> None:
        self.platform_registry = PlatformRegistry()

        # Initialize template registry with hybrid YAML + template support
        if templates_dir is None:
            # Default to templates directory relative to this file
            current_dir = Path(__file__).parent
            templates_dir = str(current_dir.parent.parent.parent / "templates")

        self.template_registry = TemplateRegistry(templates_dir)

        # Backward compatibility flag
        self.use_hybrid_templates = True

    # New hybrid template methods
    def generate_from_template(
        self,
        template_key: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> str | None:
        """Generate content from a template using the hybrid YAML + template approach.

        Args:
            template_key: Template identifier (e.g., 'docker/react.dockerfile')
            variables: Variables to substitute in the template
            variants: List of variants to apply

        Returns:
            Generated content or None if template not found
        """
        if not self.use_hybrid_templates:
            return None

        return self.template_registry.generate_template(template_key, variables, variants)

    def list_available_templates(
        self, platform: str | None = None, category: str | None = None
    ) -> list[str]:
        """List all available templates, optionally filtered by platform or category."""
        return self.template_registry.list_templates(platform, category)

    def get_template_info(self, template_key: str) -> dict[str, Any]:
        """Get comprehensive information about a template including metadata."""
        return self.template_registry.get_template_info(template_key)

    def generate_dockerfile(
        self,
        platform: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> str:
        """Generate Dockerfile for the platform using hybrid templates when available."""
        config = self.platform_registry.get_platform_config(platform)

        # Try hybrid template approach first
        if self.use_hybrid_templates:
            template_key = None
            if config.framework == "react":
                template_key = "docker/react.dockerfile"
            elif config.framework in {"express", "node"}:
                template_key = "docker/node.dockerfile"
            else:
                template_key = "docker/generic.dockerfile"

            # Attempt to generate using hybrid template
            if template_key:
                # Merge platform-specific variables with user variables
                template_vars = variables or {}
                if "node_version" not in template_vars:
                    template_vars["node_version"] = "18"  # Default

                hybrid_content = self.generate_from_template(template_key, template_vars, variants)
                if hybrid_content:
                    return hybrid_content

        # Fallback to original approach
        if config.framework == "react":
            return self._generate_react_dockerfile()
        if config.framework in {"express", "node"}:
            return self._generate_node_dockerfile()
        return self._generate_generic_dockerfile()

    def _generate_react_dockerfile(self) -> str:
        """Generate Dockerfile for React applications."""
        return ConfigLoader.load_template("docker", "react.dockerfile")

    def _generate_node_dockerfile(self) -> str:
        """Generate Dockerfile for Node.js applications."""
        return ConfigLoader.load_template("docker", "node.dockerfile")

    def _generate_generic_dockerfile(self) -> str:
        """Generate generic Dockerfile."""
        return ConfigLoader.load_template("docker", "generic.dockerfile")

    def generate_typescript_config(
        self,
        platform: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> str:
        """Generate TypeScript configuration using hybrid templates when available."""
        config = self.platform_registry.get_platform_config(platform)

        # Try hybrid template approach first
        if self.use_hybrid_templates:
            template_key = None
            if config.framework == "react":
                template_key = "typescript/react-tsconfig.yml"
            elif config.name == "bolt":
                template_key = "typescript/vite-tsconfig.yml"
            else:
                template_key = "typescript/basic-tsconfig.yml"

            # Attempt to generate using hybrid template
            if template_key:
                # Merge platform-specific variables with user variables
                template_vars = variables or {}
                if "target" not in template_vars:
                    template_vars["target"] = "ES2020" if config.name == "bolt" else "es5"

                hybrid_content = self.generate_from_template(template_key, template_vars, variants)
                if hybrid_content:
                    return hybrid_content

        # Fallback to original approach
        if config.framework == "react":
            return self._generate_react_tsconfig()
        if config.name == "bolt":
            return self._generate_vite_tsconfig()
        return self._generate_basic_tsconfig()

    def _generate_react_tsconfig(self) -> str:
        """Generate tsconfig.json for React projects."""
        return json.dumps(
            {
                "compilerOptions": {
                    "target": "es5",
                    "lib": ["dom", "dom.iterable", "es6"],
                    "allowJs": True,
                    "skipLibCheck": True,
                    "esModuleInterop": True,
                    "allowSyntheticDefaultImports": True,
                    "strict": True,
                    "forceConsistentCasingInFileNames": True,
                    "noFallthroughCasesInSwitch": True,
                    "module": "esnext",
                    "moduleResolution": "node",
                    "resolveJsonModule": True,
                    "isolatedModules": True,
                    "noEmit": True,
                    "jsx": "react-jsx",
                },
                "include": ["src"],
                "exclude": ["node_modules"],
            },
            indent=2,
        )

    def _generate_vite_tsconfig(self) -> str:
        """Generate tsconfig.json for Vite projects."""
        return json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2020",
                    "useDefineForClassFields": True,
                    "lib": ["ES2020", "DOM", "DOM.Iterable"],
                    "module": "ESNext",
                    "skipLibCheck": True,
                    "moduleResolution": "bundler",
                    "allowImportingTsExtensions": True,
                    "resolveJsonModule": True,
                    "isolatedModules": True,
                    "noEmit": True,
                    "jsx": "react-jsx",
                    "strict": True,
                    "noUnusedLocals": True,
                    "noUnusedParameters": True,
                    "noFallthroughCasesInSwitch": True,
                },
                "include": ["src"],
                "references": [{"path": "./tsconfig.node.json"}],
            },
            indent=2,
        )

    def _generate_basic_tsconfig(self) -> str:
        """Generate basic tsconfig.json."""
        return json.dumps(
            {
                "compilerOptions": {
                    "target": "es2020",
                    "module": "commonjs",
                    "lib": ["es2020"],
                    "outDir": "./dist",
                    "rootDir": "./src",
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True,
                    "resolveJsonModule": True,
                },
                "include": ["src/**/*"],
                "exclude": ["node_modules", "dist"],
            },
            indent=2,
        )

    def generate_next_config(
        self,
        platform: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> str:
        """Generate Next.js configuration using hybrid templates when available."""
        self.platform_registry.get_platform_config(platform)

        # Try hybrid template approach first
        if self.use_hybrid_templates:
            template_vars = variables or {}

            # Set default variables based on platform
            if "react_strict_mode" not in template_vars:
                template_vars["react_strict_mode"] = True
            if "swc_minify" not in template_vars:
                template_vars["swc_minify"] = True
            if "app_dir" not in template_vars:
                template_vars["app_dir"] = True
            if "image_domains" not in template_vars:
                template_vars["image_domains"] = ["localhost"]
            if "custom_env_vars" not in template_vars:
                template_vars["custom_env_vars"] = ["CUSTOM_KEY"]

            hybrid_content = self.generate_from_template(
                "build/next.config.yml", template_vars, variants
            )
            if hybrid_content:
                return hybrid_content

        # Fallback to original hardcoded approach
        return """
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['localhost'],
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
}

module.exports = nextConfig
        """.strip()

    def generate_testing_files(
        self,
        platform: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> dict[str, str]:
        """Generate testing configuration files using hybrid templates when available."""
        config = self.platform_registry.get_platform_config(platform)

        # Try hybrid template approach first
        if self.use_hybrid_templates:
            testing_files = {}

            # Generate Jest config for most platforms
            if config.name != "bolt":
                jest_vars = variables or {}
                if "coverage_threshold" not in jest_vars:
                    jest_vars["coverage_threshold"] = 80

                jest_content = self.generate_from_template(
                    "testing/jest.config.js", jest_vars, variants
                )
                if jest_content:
                    testing_files["jest.config.js"] = jest_content

            # Generate Vitest config for Bolt platform
            if config.name == "bolt":
                vitest_vars = variables or {}
                if "coverage_threshold" not in vitest_vars:
                    vitest_vars["coverage_threshold"] = 80

                vitest_content = self.generate_from_template(
                    "build/vitest.config.js", vitest_vars, variants
                )
                if vitest_content:
                    testing_files["vitest.config.js"] = vitest_content

            # If we got hybrid content, return it
            if testing_files:
                # Add additional testing files from original approach
                if config.framework == "react":
                    react_files = self._generate_react_testing_files()
                    testing_files.update(react_files)
                else:
                    common_files = self._generate_common_testing_files()
                    testing_files.update(common_files)

                return testing_files

        # Fallback to original approach
        if config.framework == "react":
            return self._generate_react_testing_files()
        return self._generate_common_testing_files()

    def _generate_react_testing_files(self) -> dict[str, str]:
        """Generate React testing setup."""
        return {
            "src/setupTests.ts": """
import '@testing-library/jest-dom';
            """.strip(),
            "src/__tests__/App.test.tsx": """
import { render, screen } from '@testing-library/react';
import App from '../App';

test('renders learn react link', () => {
  render(<App />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
            """.strip(),
            "jest.config.js": """
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapping: {
    '\\\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/index.tsx',
    '!src/reportWebVitals.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
            """.strip(),
        }

    def _generate_common_testing_files(self) -> dict[str, str]:
        """Generate common testing files."""
        return {
            ".github/workflows/test.yml": """
name: Test
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test -- --coverage --watchAll=false
      - name: Upload coverage
        uses: codecov/codecov-action@v3
            """.strip(),
            "playwright.config.ts": """
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
            """.strip(),
        }

    def generate_security_files(self, platform: str) -> dict[str, str]:
        """Generate security configuration files."""
        config = self.platform_registry.get_platform_config(platform)
        files: dict[str, str] = {}

        files[".env.example"] = self._generate_env_example(config)
        files["security/helmet.config.js"] = self._generate_helmet_config()
        files["security/cors.config.js"] = self._generate_cors_config()

        if config.framework == "react":
            files["public/.htaccess"] = self._generate_htaccess()

        return files

    def _generate_env_example(self, config: PlatformConfig) -> str:
        """Generate environment variables example."""
        env_vars = [
            "# Environment Configuration",
            "NODE_ENV=development",
            "PORT=3000",
            "",
            "# Database",
            "DATABASE_URL=postgresql://user:password@localhost:5432/dbname",
            "",
            "# Authentication",
            "JWT_SECRET=your-secret-key-here",
            "SESSION_SECRET=your-session-secret",
            "",
            "# External APIs",
            "API_KEY=your-api-key",
            "",
            "# Monitoring",
            "SENTRY_DSN=your-sentry-dsn",
            "",
            "# Feature Flags",
            "ENABLE_FEATURE_X=false",
        ]

        if config.framework == "react":
            env_vars.extend(
                [
                    "",
                    "# React App Variables (must start with REACT_APP_)",
                    "REACT_APP_API_URL=http://localhost:3001",
                    "REACT_APP_ENVIRONMENT=development",
                ]
            )

        return "\n".join(env_vars)

    def _generate_helmet_config(self) -> str:
        """Generate Helmet security configuration."""
        return """
const helmet = require('helmet');

const helmetConfig = {
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      imgSrc: ["'self'", "data:", "https:"],
      scriptSrc: ["'self'"],
      connectSrc: ["'self'"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },
};

module.exports = helmetConfig;
        """.strip()

    def _generate_cors_config(self) -> str:
        """Generate CORS configuration."""
        return """
const corsConfig = {
  origin: process.env.NODE_ENV === 'production'
    ? ['https://yourdomain.com']
    : ['http://localhost:3000', 'http://localhost:3001'],
  credentials: true,
  optionsSuccessStatus: 200,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
};

module.exports = corsConfig;
        """.strip()

    def _generate_htaccess(self) -> str:
        """Generate .htaccess for React apps."""
        return """
Options -MultiViews
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^ index.html [QSA,L]

# Security headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
        """.strip()

    def generate_storybook_config(self) -> dict[str, str]:
        """Generate Storybook configuration."""
        return {
            ".storybook/main.js": """
module.exports = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
};
            """.strip(),
            ".storybook/preview.js": """
export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
};
            """.strip(),
            "src/components/Button/Button.stories.tsx": """
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Example/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    backgroundColor: { control: 'color' },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    primary: true,
    label: 'Button',
  },
};

export const Secondary: Story = {
  args: {
    label: 'Button',
  },
};
            """.strip(),
        }

    def generate_accessibility_testing(self) -> dict[str, str]:
        """Generate accessibility testing setup."""
        return {
            "src/utils/axe-config.ts": """
import { configureAxe } from 'jest-axe';

const axe = configureAxe({
  rules: {
    // Disable color-contrast rule for now
    'color-contrast': { enabled: false },
  },
});

export default axe;
            """.strip(),
            "src/__tests__/accessibility.test.tsx": """
import { render } from '@testing-library/react';
import axe from '../utils/axe-config';
import App from '../App';

describe('Accessibility tests', () => {
  test('should not have any accessibility violations', async () => {
    const { container } = render(<App />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
            """.strip(),
        }

    def generate_azure_configs(
        self,
        platform: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> dict[str, str]:
        """Generate Azure-specific configuration files using hybrid templates when available."""
        config = self.platform_registry.get_platform_config(platform)
        files: dict[str, str] = {}

        # Try hybrid template approach first
        if self.use_hybrid_templates:
            # Azure DevOps Pipeline
            pipeline_vars = variables or {}
            if "node_version" not in pipeline_vars:
                pipeline_vars["node_version"] = "18.x"
            if "build_command" not in pipeline_vars:
                pipeline_vars["build_command"] = config.build_command

            pipeline_content = self.generate_from_template(
                "deployment/azure-pipeline.yml", pipeline_vars, variants
            )
            if pipeline_content:
                files["azure-pipelines.yml"] = pipeline_content

            # Web.config for Azure App Service
            web_config_vars = variables or {}
            if "framework" not in web_config_vars:
                web_config_vars["framework"] = config.framework

            web_config_content = self.generate_from_template(
                "deployment/web.config.yml", web_config_vars, variants
            )
            if web_config_content:
                files["web.config"] = web_config_content

            # Static Web App config for React
            if config.framework == "react":
                swa_vars = variables or {}
                if "api_authentication" not in swa_vars:
                    swa_vars["api_authentication"] = True

                swa_content = self.generate_from_template(
                    "deployment/azure-static-web-app.config.yml", swa_vars, variants
                )
                if swa_content:
                    files["staticwebapp.config.json"] = swa_content

            # If we got hybrid content, return it
            if files:
                return files

        # Fallback to original hardcoded approach
        files["azure-pipelines.yml"] = self._generate_azure_pipeline(config)
        files["web.config"] = self._generate_web_config(config)

        if config.framework == "react":
            files["staticwebapp.config.json"] = self._generate_static_web_app_config()

        return files

    def _generate_azure_pipeline(self, config: PlatformConfig) -> str:
        """Generate Azure DevOps pipeline."""
        return f"""
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  nodeVersion: '18.x'

stages:
- stage: Build
  displayName: 'Build stage'
  jobs:
  - job: Build
    displayName: 'Build job'
    steps:
    - task: NodeTool@0
      inputs:
        versionSpec: '$(nodeVersion)'
      displayName: 'Install Node.js'

    - script: |
        npm ci
      displayName: 'Install dependencies'

    - script: |
        npm run test -- --coverage --watchAll=false
      displayName: 'Run tests'

    - script: |
        {config.build_command}
      displayName: 'Build application'

    - task: ArchiveFiles@2
      inputs:
        rootFolderOrFile: '$(System.DefaultWorkingDirectory)'
        includeRootFolder: false
        archiveType: 'zip'
        archiveFile: '$(Build.ArtifactStagingDirectory)/$(Build.BuildId).zip'
        replaceExistingArchive: true

    - task: PublishBuildArtifacts@1
      inputs:
        PathtoPublish: '$(Build.ArtifactStagingDirectory)'
        ArtifactName: 'drop'
        publishLocation: 'Container'
        """.strip()

    def _generate_web_config(self, config: PlatformConfig) -> str:
        """Generate web.config for Azure App Service."""
        if config.framework == "react":
            return """
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="React Routes" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/" />
        </rule>
      </rules>
    </rewrite>
    <httpHeaders>
      <add name="X-Content-Type-Options" value="nosniff" />
      <add name="X-Frame-Options" value="DENY" />
      <add name="X-XSS-Protection" value="1; mode=block" />
    </httpHeaders>
  </system.webServer>
</configuration>
            """.strip()
        return """
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="iisnode" path="index.js" verb="*" modules="iisnode"/>
    </handlers>
    <rewrite>
      <rules>
        <rule name="DynamicContent">
          <match url="/*" />
          <action type="Rewrite" url="index.js"/>
        </rule>
      </rules>
    </rewrite>
    <httpHeaders>
      <add name="X-Content-Type-Options" value="nosniff" />
      <add name="X-Frame-Options" value="DENY" />
      <add name="X-XSS-Protection" value="1; mode=block" />
    </httpHeaders>
  </system.webServer>
</configuration>
            """.strip()

    def _generate_static_web_app_config(self) -> str:
        """Generate Azure Static Web Apps configuration."""
        return json.dumps(
            {
                "routes": [
                    {"route": "/api/*", "allowedRoles": ["authenticated"]},
                    {"route": "/*", "serve": "/index.html", "statusCode": 200},
                ],
                "responseOverrides": {"401": {"redirect": "/login", "statusCode": 302}},
                "globalHeaders": {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "X-XSS-Protection": "1; mode=block",
                },
            },
            indent=2,
        )

    def generate_deployment_automation(
        self,
        platform: str,
        variables: dict[str, Any] | None = None,
        variants: list[str] | None = None,
    ) -> dict[str, str]:
        """Generate deployment automation scripts using hybrid templates when available."""
        config = self.platform_registry.get_platform_config(platform)
        files: dict[str, str] = {}

        # Try hybrid template approach first
        if self.use_hybrid_templates:
            # GitHub Actions workflow
            github_vars = variables or {}
            if "node_version" not in github_vars:
                github_vars["node_version"] = "18"
            if "build_command" not in github_vars:
                github_vars["build_command"] = config.build_command

            github_content = self.generate_from_template(
                "deployment/github-actions.yml", github_vars, variants
            )
            if github_content:
                files[".github/workflows/deploy.yml"] = github_content

            # Platform-specific deployment configs
            for target in config.deployment_targets:
                if target == "vercel":
                    vercel_vars = variables or {}
                    if "framework" not in vercel_vars:
                        vercel_vars["framework"] = config.framework
                    if "spa_routing" not in vercel_vars:
                        vercel_vars["spa_routing"] = config.framework == "react"

                    vercel_content = self.generate_from_template(
                        "deployment/vercel.config.yml", vercel_vars, variants
                    )
                    if vercel_content:
                        files["vercel.json"] = vercel_content

                elif target == "netlify":
                    netlify_vars = variables or {}
                    if "build_command" not in netlify_vars:
                        netlify_vars["build_command"] = config.build_command
                    if "publish_directory" not in netlify_vars:
                        netlify_vars["publish_directory"] = (
                            "build" if config.framework == "react" else "dist"
                        )
                    if "spa_routing" not in netlify_vars:
                        netlify_vars["spa_routing"] = config.framework == "react"

                    netlify_content = self.generate_from_template(
                        "deployment/netlify.config.yml", netlify_vars, variants
                    )
                    if netlify_content:
                        files["netlify.toml"] = netlify_content

            # If we got hybrid content, return it
            if files:
                return files

        # Fallback to original hardcoded approach
        files[".github/workflows/deploy.yml"] = self._generate_github_actions_deploy(config)

        # Platform-specific deployment configs
        for target in config.deployment_targets:
            if target == "vercel":
                files["vercel.json"] = self._generate_vercel_config(config)
            elif target == "netlify":
                files["netlify.toml"] = self._generate_netlify_config(config)

        return files

    def _generate_github_actions_deploy(self, config: PlatformConfig) -> str:
        """Generate GitHub Actions deployment workflow."""
        return f"""
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test -- --coverage --watchAll=false
      - name: Build
        run: {config.build_command}

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Build
        run: {config.build_command}
      - name: Deploy
        run: echo "Add deployment step here"
        """.strip()

    def _generate_vercel_config(self, config: PlatformConfig) -> str:
        """Generate Vercel configuration."""
        vercel_config = {
            "version": 2,
            "builds": [
                {
                    "src": "package.json",
                    "use": (
                        "@vercel/node"
                        if config.framework in {"express", "node"}
                        else "@vercel/static-build"
                    ),
                }
            ],
        }

        if config.framework == "react":
            vercel_config["routes"] = [
                {"handle": "filesystem"},
                {"src": "/.*", "dest": "/index.html"},
            ]

        return json.dumps(vercel_config, indent=2)

    def _generate_netlify_config(self, config: PlatformConfig) -> str:
        """Generate Netlify configuration."""
        return f"""
[build]
  publish = "build"
  command = "{config.build_command}"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
        """.strip()

    def generate_monitoring_scripts(self, platform: str) -> dict[str, str]:
        """Generate monitoring scripts."""
        return {
            "scripts/health_check.sh": """
#!/bin/bash
# Health check script
set -e

echo "Checking application health..."

# Check if the application is responding
if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Application is healthy"
    exit 0
else
    echo "❌ Application health check failed"
    exit 1
fi
            """.strip(),
            "scripts/monitor.sh": """
#!/bin/bash
# Monitoring script
set -e

echo "Starting application monitoring..."

# Monitor CPU and memory usage
while true; do
    echo "$(date): CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%, Memory: $(free | grep Mem | awk '{printf("%.2f%%", $3/$2 * 100.0)}')"
    sleep 30
done
            """.strip(),
            "scripts/alert_on_failure.sh": """
#!/bin/bash
# Alert script for failures
set -e

SERVICE_NAME="$1"
ERROR_MESSAGE="$2"

echo "ALERT: $SERVICE_NAME failed - $ERROR_MESSAGE"

# Add your alerting logic here
# Examples:
# - Send email
# - Post to Slack
# - Send to monitoring service
# - Log to external system

# Example webhook notification
# curl -X POST -H 'Content-type: application/json' \\
#   --data '{"text":"ALERT: '$SERVICE_NAME' failed - '$ERROR_MESSAGE'"}' \\
#   $SLACK_WEBHOOK_URL
            """.strip(),
        }

    def generate_backup_scripts(self, platform: str) -> dict[str, str]:
        """Generate backup scripts."""
        return {
            "scripts/backup.sh": """
#!/bin/bash
# Backup script
set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Creating backup at $TIMESTAMP..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database (if applicable)
if [ ! -z "$DATABASE_URL" ]; then
    echo "Backing up database..."
    pg_dump $DATABASE_URL > $BACKUP_DIR/db_backup_$TIMESTAMP.sql
fi

# Backup uploaded files (if applicable)
if [ -d "./uploads" ]; then
    echo "Backing up uploaded files..."
    tar -czf $BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz ./uploads
fi

# Backup configuration
echo "Backing up configuration..."
cp .env $BACKUP_DIR/env_backup_$TIMESTAMP

echo "✅ Backup completed: $BACKUP_DIR"
            """.strip(),
            "scripts/restore.sh": """
#!/bin/bash
# Restore script
set -e

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Restoring from backup: $BACKUP_FILE"

# Restore database
if [[ $BACKUP_FILE == *.sql ]]; then
    echo "Restoring database..."
    psql $DATABASE_URL < $BACKUP_FILE
fi

# Restore files
if [[ $BACKUP_FILE == *.tar.gz ]]; then
    echo "Restoring files..."
    tar -xzf $BACKUP_FILE
fi

echo "✅ Restore completed"
            """.strip(),
        }
