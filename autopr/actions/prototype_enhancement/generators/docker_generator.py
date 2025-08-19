"""
Docker Generator Module

Handles generation of Dockerfiles, docker-compose files, and related configurations.
"""

from pathlib import Path
from typing import Any

from .base_generator import BaseGenerator


class DockerGenerator(BaseGenerator):
    """Generates Docker-related files and configurations."""

    def generate(self, output_dir: str, **kwargs) -> list[str]:
        """Generate Docker-related files and configurations.

        Args:
            output_dir: The directory to generate files in
            **kwargs: Additional arguments including:
                - language: The programming language
                - framework: The web framework being used
                - database: The database type (if any)
                - environment: The target environment (dev, prod, etc.)
        Returns:
            List of paths to generated files
        """
        generated_files = []
        language = kwargs.get("language", "").lower()
        framework = kwargs.get("framework", "").lower()
        database = kwargs.get("database", "").lower()
        environment = kwargs.get("environment", "dev")

        # Common variables for Docker templates
        template_vars = {
            "language": language,
            "framework": framework,
            "database": database,
            "environment": environment,
            **self._get_platform_variables(),
        }

        # Generate Dockerfile
        generated_files.extend(self._generate_dockerfile(output_dir, template_vars))

        # Generate docker-compose files
        generated_files.extend(self._generate_docker_compose(output_dir, template_vars))

        # Generate .dockerignore
        generated_files.extend(self._generate_docker_ignore(output_dir, template_vars))

        # Generate Kubernetes manifests if requested
        if kwargs.get("kubernetes"):
            generated_files.extend(self._generate_kubernetes_manifests(output_dir, template_vars))

        return generated_files

    def _generate_dockerfile(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate Dockerfile based on language and framework."""
        language = variables.get("language", "")
        framework = variables.get("framework", "")
        environment = variables.get("environment", "dev")

        # Check for multi-stage build support
        multi_stage = variables.get("multi_stage", True)

        # Determine Dockerfile template path
        template_path = f"docker/{language}/{framework}/Dockerfile"
        if not self._template_exists(template_path):
            template_path = f"docker/{language}/Dockerfile"
            if not self._template_exists(template_path):
                template_path = "docker/Dockerfile"

        # Render Dockerfile
        content = self._render_template(
            template_path,
            {
                **variables,
                "multi_stage": multi_stage,
                "is_dev": environment == "dev",
                "is_prod": environment == "prod",
            },
        )

        if not content:
            return []

        # Write Dockerfile
        file_path = str(Path(output_dir) / "Dockerfile")
        self._write_file(file_path, content)
        return [file_path]

    def _generate_docker_compose(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate docker-compose files."""
        generated_files = []
        language = variables.get("language", "")
        framework = variables.get("framework", "")
        database = variables.get("database", "")
        environment = variables.get("environment", "dev")

        # Base docker-compose file
        base_vars = {
            **variables,
            "services": self._get_docker_compose_services(
                language, framework, database, environment
            ),
        }

        # Generate base docker-compose.yml
        content = self._render_template("docker/docker-compose.yml", base_vars)
        if content:
            file_path = str(Path(output_dir) / "docker-compose.yml")
            self._write_file(file_path, content)
            generated_files.append(file_path)

        # Generate environment-specific override if needed
        if environment in {"dev", "prod", "test"}:
            override_vars = {
                **base_vars,
                "is_dev": environment == "dev",
                "is_prod": environment == "prod",
                "is_test": environment == "test",
            }

            override_content = self._render_template(
                f"docker/overrides/docker-compose.{environment}.yml", override_vars
            )

            if override_content:
                override_path = str(Path(output_dir) / f"docker-compose.{environment}.yml")
                self._write_file(override_path, override_content)
                generated_files.append(override_path)

        # Generate .env file for docker-compose
        env_vars = self._get_docker_env_vars(language, framework, database, environment)
        if env_vars:
            env_content = "\n".join(f"{k}={v}" for k, v in env_vars.items())
            env_path = str(Path(output_dir) / ".env")
            self._write_file(env_path, env_content)
            generated_files.append(env_path)

        return generated_files

    def _get_docker_compose_services(
        self, language: str, framework: str, database: str, environment: str
    ) -> dict[str, Any]:
        """Get services configuration for docker-compose."""
        services = {}

        # Main application service
        services["app"] = {
            "build": ".",
            "container_name": f"app-{environment}",
            "restart": "unless-stopped",
            "env_file": [".env"],
            "ports": ["3000:3000"],
            "volumes": ["./:/app"] if environment == "dev" else None,
            "depends_on": [],
        }

        # Database service if specified
        if database:
            db_service = self._get_database_service(database, environment)
            if db_service:
                services["db"] = db_service
                services["app"]["depends_on"].append("db")

        # Additional services based on language/framework
        if language == "typescript" and environment == "dev":
            services["app"]["volumes"] = ["./:/app", "/app/node_modules"]
            services["app"]["command"] = "npm run dev"

        return services

    def _get_database_service(self, database: str, environment: str) -> dict[str, Any] | None:
        """Get database service configuration."""
        db_configs = {
            "postgresql": {
                "image": "postgres:13-alpine",
                "container_name": "db",
                "environment": {
                    "POSTGRES_USER": "user",
                    "POSTGRES_PASSWORD": "password",
                    "POSTGRES_DB": "app_db",
                },
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "ports": ["5432:5432"] if environment == "dev" else None,
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U user -d app_db"],
                    "interval": "5s",
                    "timeout": "5s",
                    "retries": 5,
                },
            },
            "mongodb": {
                "image": "mongo:5.0",
                "container_name": "mongo",
                "environment": {
                    "MONGO_INITDB_ROOT_USERNAME": "root",
                    "MONGO_INITDB_ROOT_PASSWORD": "example",
                },
                "volumes": ["mongo_data:/data/db"],
                "ports": ["27017:27017"] if environment == "dev" else None,
            },
            "mysql": {
                "image": "mysql:8.0",
                "container_name": "mysql",
                "environment": {
                    "MYSQL_ROOT_PASSWORD": "root",
                    "MYSQL_DATABASE": "app_db",
                    "MYSQL_USER": "user",
                    "MYSQL_PASSWORD": "password",
                },
                "volumes": ["mysql_data:/var/lib/mysql"],
                "ports": ["3306:3306"] if environment == "dev" else None,
                "command": "--default-authentication-plugin=mysql_native_password",
                "healthcheck": {
                    "test": ["CMD", "mysqladmin", "ping", "-h", "localhost"],
                    "timeout": "5s",
                    "retries": 10,
                },
            },
        }

        return db_configs.get(database.lower())

    def _get_docker_env_vars(
        self, language: str, framework: str, database: str, environment: str
    ) -> dict[str, str]:
        """Get environment variables for Docker."""
        env_vars = {
            "NODE_ENV": environment,
            "PORT": "3000",
            "LOG_LEVEL": "debug" if environment == "dev" else "info",
        }

        # Add database connection strings if database is specified
        if database == "postgresql":
            env_vars.update(
                {
                    "DB_HOST": "db",
                    "DB_PORT": "5432",
                    "DB_NAME": "app_db",
                    "DB_USER": "user",
                    "DB_PASSWORD": "password",
                    "DATABASE_URL": "postgresql://user:password@db:5432/app_db",
                }
            )
        elif database == "mongodb":
            env_vars.update({"MONGODB_URI": "mongodb://root:example@mongo:27017/"})
        elif database == "mysql":
            env_vars.update(
                {
                    "DB_HOST": "mysql",
                    "DB_PORT": "3306",
                    "DB_NAME": "app_db",
                    "DB_USER": "user",
                    "DB_PASSWORD": "password",
                    "DATABASE_URL": "mysql://user:password@mysql:3306/app_db",
                }
            )

        return env_vars

    def _generate_docker_ignore(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate .dockerignore file."""
        language = variables.get("language", "")
        variables.get("framework", "")

        # Common ignore patterns
        ignore_patterns = [
            ".git",
            ".gitignore",
            ".DS_Store",
            "node_modules",
            "npm-debug.log",
            ".env*",
            "!.env.example",
            "dist",
            "build",
            "coverage",
            "*.log",
            "*.swp",
            "*.swo",
            ".vscode",
            ".idea",
            "*.iml",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "venv",
            "env",
            ".venv",
            "ENV",
            "env.bak",
            "venv.bak",
            "*.bak",
            "*.tmp",
            "*.temp",
        ]

        # Language-specific ignores
        if language == "typescript":
            ignore_patterns.extend(
                [
                    "*.tsbuildinfo",
                    "tsconfig.tsbuildinfo",
                    ".next",
                    ".nuxt",
                    ".cache",
                    ".svelte-kit",
                    ".vercel",
                    ".netlify",
                    "*.tsbuildinfo",
                    "tsconfig.tsbuildinfo",
                ]
            )
        elif language == "python":
            ignore_patterns.extend(
                [
                    "*.pyc",
                    "*.pyo",
                    "*.pyd",
                    "__pycache__",
                    "*.egg-info",
                    "*.egg",
                    "*.manifest",
                    "*.spec",
                    "pip-log.txt",
                    "pip-delete-this-directory.txt",
                    "htmlcov",
                    ".tox",
                    ".nox",
                    ".coverage",
                    ".coverage.*",
                    ".cache",
                    "nosetests.xml",
                    "coverage.xml",
                    "*.cover",
                    "*.py,cover",
                    ".hypothesis",
                    ".pytest_cache",
                    "cover",
                    "migrations",
                    "migrations_*",
                    "alembic.ini",
                ]
            )

        # Write .dockerignore file
        content = "\n".join(ignore_patterns)
        file_path = str(Path(output_dir) / ".dockerignore")
        self._write_file(file_path, content)
        return [file_path]

    def _generate_kubernetes_manifests(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate Kubernetes manifests."""
        generated_files = []
        k8s_dir = Path(output_dir) / "k8s"
        k8s_dir.mkdir(exist_ok=True)

        # Generate namespace
        content = self._render_template("kubernetes/namespace.yaml", variables)
        if content:
            file_path = str(k8s_dir / "namespace.yaml")
            self._write_file(file_path, content)
            generated_files.append(file_path)

        # Generate config maps and secrets
        content = self._render_template("kubernetes/configmap.yaml", variables)
        if content:
            file_path = str(k8s_dir / "configmap.yaml")
            self._write_file(file_path, content)
            generated_files.append(file_path)

        # Generate deployments
        content = self._render_template("kubernetes/deployment.yaml", variables)
        if content:
            file_path = str(k8s_dir / "deployment.yaml")
            self._write_file(file_path, content)
            generated_files.append(file_path)

        # Generate services
        content = self._render_template("kubernetes/service.yaml", variables)
        if content:
            file_path = str(k8s_dir / "service.yaml")
            self._write_file(file_path, content)
            generated_files.append(file_path)

        # Generate ingress if needed
        if variables.get("ingress_enabled"):
            content = self._render_template("kubernetes/ingress.yaml", variables)
            if content:
                file_path = str(k8s_dir / "ingress.yaml")
                self._write_file(file_path, content)
                generated_files.append(file_path)

        # Generate database manifests if needed
        database = variables.get("database", "")
        if database:
            db_template = f"kubernetes/{database}.yaml"
            if self._template_exists(db_template):
                content = self._render_template(db_template, variables)
                if content:
                    file_path = str(k8s_dir / f"{database}.yaml")
                    self._write_file(file_path, content)
                    generated_files.append(file_path)

        return generated_files
