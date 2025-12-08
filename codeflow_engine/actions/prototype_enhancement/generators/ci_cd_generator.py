"""
CI/CD Generator Module

Handles generation of CI/CD pipeline configurations for various providers.
"""

from pathlib import Path
from typing import Any

from codeflow_engine.actions.prototype_enhancement.generators.base_generator import BaseGenerator


class CICDGenerator(BaseGenerator):
    """Generates CI/CD pipeline configurations for various providers."""

    def generate(self, output_dir: str, **kwargs) -> list[str]:
        """Generate CI/CD pipeline configurations.

        Args:
            output_dir: The directory to generate files in
            **kwargs: Additional arguments including:
                - ci_provider: The CI/CD provider (github, gitlab, circleci, etc.)
                - language: The programming language
                - test_command: The command to run tests
                - build_command: The command to build the project
                - deploy_command: The command to deploy the project
                - branch: The main branch name (default: main)
                - node_version: Node.js version (for JavaScript/TypeScript projects)
                - python_version: Python version (for Python projects)
                - database: The database type (if any)
                - cache: Whether to enable caching
                - notifications: Configuration for notifications
                - environment: The target environment (dev, staging, prod)
        Returns:
            List of paths to generated files
        """
        generated_files = []
        ci_provider = kwargs.get("ci_provider", "github").lower()
        language = kwargs.get("language", "").lower()

        # Common variables for CI/CD templates
        template_vars = {
            "ci_provider": ci_provider,
            "language": language,
            "test_command": kwargs.get(
                "test_command", self._get_default_test_command(language)
            ),
            "build_command": kwargs.get(
                "build_command", self._get_default_build_command(language)
            ),
            "deploy_command": kwargs.get(
                "deploy_command", self._get_default_deploy_command(language)
            ),
            "branch": kwargs.get("branch", "main"),
            "node_version": kwargs.get("node_version", "18"),
            "python_version": kwargs.get("python_version", "3.10"),
            "database": kwargs.get("database", "").lower(),
            "cache": kwargs.get("cache", True),
            "notifications": kwargs.get("notifications", {}),
            "environment": kwargs.get("environment", "production"),
            **self._get_platform_variables(),
        }

        # Generate CI/CD configuration based on provider
        if ci_provider == "github":
            generated_files.extend(
                self._generate_github_actions(output_dir, template_vars)
            )
        elif ci_provider == "gitlab":
            generated_files.extend(self._generate_gitlab_ci(output_dir, template_vars))
        elif ci_provider == "circleci":
            generated_files.extend(self._generate_circleci(output_dir, template_vars))
        elif ci_provider == "jenkins":
            generated_files.extend(self._generate_jenkins(output_dir, template_vars))
        elif ci_provider == "azure":
            generated_files.extend(
                self._generate_azure_pipelines(output_dir, template_vars)
            )

        # Generate deployment configurations if needed
        if kwargs.get("generate_deployment"):
            generated_files.extend(
                self._generate_deployment_configs(output_dir, template_vars)
            )

        return generated_files

    def _get_default_test_command(self, language: str) -> str:
        """Get the default test command for a language."""
        return {
            "javascript": "npm test",
            "typescript": "npm test",
            "python": "pytest",
            "java": "./mvnw test",
            "go": "go test ./...",
            "ruby": "bundle exec rspec",
            "php": "composer test",
            "csharp": "dotnet test",
            "rust": "cargo test",
        }.get(language, 'echo "No test command specified"')

    def _get_default_build_command(self, language: str) -> str:
        """Get the default build command for a language."""
        return {
            "javascript": "npm run build",
            "typescript": "npm run build",
            "python": "python setup.py build",
            "java": "./mvnw clean package",
            "go": "go build -o app",
            "ruby": "bundle install",
            "php": "composer install --no-dev --optimize-autoloader",
            "csharp": "dotnet build",
            "rust": "cargo build --release",
        }.get(language, 'echo "No build command specified"')

    def _get_default_deploy_command(self, language: str) -> str:
        """Get the default deploy command for a language."""
        return {
            "javascript": "npm run deploy",
            "typescript": "npm run deploy",
            "python": "pip install .",
            "java": "./mvnw deploy",
            "go": "go install",
            "ruby": "bundle exec rake deploy",
            "php": "composer deploy",
            "csharp": "dotnet publish -c Release -o ./publish",
            "rust": "cargo install --path .",
        }.get(language, 'echo "No deploy command specified"')

    def _generate_github_actions(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate GitHub Actions workflow files."""
        generated_files = []
        workflows_dir = Path(output_dir) / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        # Main CI workflow
        ci_workflow = self._render_template("ci/github/ci.yml", variables)
        if ci_workflow:
            ci_path = workflows_dir / "ci.yml"
            self._write_file(str(ci_path), ci_workflow)
            generated_files.append(str(ci_path))

        # CodeQL security scanning
        codeql_workflow = self._render_template("ci/github/codeql.yml", variables)
        if codeql_workflow:
            codeql_path = workflows_dir / "codeql-analysis.yml"
            self._write_file(str(codeql_path), codeql_workflow)
            generated_files.append(str(codeql_path))

        # Dependabot configuration
        dependabot_dir = Path(output_dir) / ".github"
        dependabot_config = self._render_template("ci/github/dependabot.yml", variables)
        if dependabot_config:
            dependabot_path = dependabot_dir / "dependabot.yml"
            self._write_file(str(dependabot_path), dependabot_config)
            generated_files.append(str(dependabot_path))

        # Issue templates
        issue_template_dir = Path(output_dir) / ".github" / "ISSUE_TEMPLATE"
        issue_template_dir.mkdir(parents=True, exist_ok=True)

        issue_templates = [
            "bug_report.md",
            "feature_request.md",
            "security_vulnerability.md",
        ]

        for template in issue_templates:
            content = self._render_template(
                f"ci/github/ISSUE_TEMPLATE/{template}", variables
            )
            if content:
                file_path = issue_template_dir / template
                self._write_file(str(file_path), content)
                generated_files.append(str(file_path))

        # Pull request template
        pr_template = self._render_template(
            "ci/github/pull_request_template.md", variables
        )
        if pr_template:
            pr_path = Path(output_dir) / ".github" / "pull_request_template.md"
            self._write_file(str(pr_path), pr_template)
            generated_files.append(str(pr_path))

        return generated_files

    def _generate_gitlab_ci(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate GitLab CI configuration."""
        generated_files = []

        # Main .gitlab-ci.yml
        gitlab_ci = self._render_template("ci/gitlab/gitlab-ci.yml", variables)
        if gitlab_ci:
            gitlab_ci_path = Path(output_dir) / ".gitlab-ci.yml"
            self._write_file(str(gitlab_ci_path), gitlab_ci)
            generated_files.append(str(gitlab_ci_path))

        # Include any additional GitLab CI configurations
        additional_configs = [
            "includes/.code-quality.yml",
            "includes/docker-build.yml",
            "includes/deploy.yml",
        ]

        for config in additional_configs:
            content = self._render_template(f"ci/gitlab/{config}", variables)
            if content:
                config_path = Path(output_dir) / ".gitlab" / config
                config_path.parent.mkdir(parents=True, exist_ok=True)
                self._write_file(str(config_path), content)
                generated_files.append(str(config_path))

        # Merge request template
        mr_template = self._render_template(
            "ci/gitlab/merge_request_template.md", variables
        )
        if mr_template:
            mr_path = (
                Path(output_dir) / ".gitlab" / "merge_request_templates" / "Default.md"
            )
            mr_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_file(str(mr_path), mr_template)
            generated_files.append(str(mr_path))

        return generated_files

    def _generate_circleci(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate CircleCI configuration."""
        generated_files = []
        circleci_dir = Path(output_dir) / ".circleci"
        circleci_dir.mkdir(exist_ok=True)

        # Main config.yml
        config_yml = self._render_template("ci/circleci/config.yml", variables)
        if config_yml:
            config_path = circleci_dir / "config.yml"
            self._write_file(str(config_path), config_yml)
            generated_files.append(str(config_path))

        # Orbs and commands
        for item in ["orbs", "commands", "executors", "jobs"]:
            content = self._render_template(f"ci/circleci/{item}.yml", variables)
            if content:
                item_dir = circleci_dir / item
                item_dir.mkdir(exist_ok=True)
                item_path = item_dir / f"{item}.yml"
                self._write_file(str(item_path), content)
                generated_files.append(str(item_path))

        return generated_files

    def _generate_jenkins(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate Jenkins pipeline configuration."""
        generated_files = []
        jenkins_dir = Path(output_dir) / "jenkins"
        jenkins_dir.mkdir(exist_ok=True)

        # Main Jenkinsfile
        jenkinsfile = self._render_template("ci/jenkins/Jenkinsfile", variables)
        if jenkinsfile:
            jenkinsfile_path = Path(output_dir) / "Jenkinsfile"
            self._write_file(str(jenkinsfile_path), jenkinsfile)
            generated_files.append(str(jenkinsfile_path))

        # Shared library if needed
        shared_lib = self._render_template("ci/jenkins/vars/buildApp.groovy", variables)
        if shared_lib:
            shared_lib_dir = jenkins_dir / "vars"
            shared_lib_dir.mkdir(parents=True, exist_ok=True)
            shared_lib_path = shared_lib_dir / "buildApp.groovy"
            self._write_file(str(shared_lib_path), shared_lib)
            generated_files.append(str(shared_lib_path))

        # Pipeline configuration
        pipeline_config = self._render_template(
            "ci/jenkins/pipeline-config.yaml", variables
        )
        if pipeline_config:
            config_path = jenkins_dir / "pipeline-config.yaml"
            self._write_file(str(config_path), pipeline_config)
            generated_files.append(str(config_path))

        return generated_files

    def _generate_azure_pipelines(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate Azure Pipelines configuration."""
        generated_files = []

        # Main azure-pipelines.yml
        pipeline_yml = self._render_template("ci/azure/azure-pipelines.yml", variables)
        if pipeline_yml:
            pipeline_path = Path(output_dir) / "azure-pipelines.yml"
            self._write_file(str(pipeline_path), pipeline_yml)
            generated_files.append(str(pipeline_path))

        # Templates
        templates_dir = Path(output_dir) / ".azure-pipelines"
        templates_dir.mkdir(exist_ok=True)

        template_files = [
            "templates/build-steps.yml",
            "templates/test-steps.yml",
            "templates/deploy-steps.yml",
            "variables/common.yml",
            "variables/dev.yml",
            "variables/prod.yml",
        ]

        for template in template_files:
            content = self._render_template(f"ci/azure/{template}", variables)
            if content:
                template_path = templates_dir / template
                template_path.parent.mkdir(parents=True, exist_ok=True)
                self._write_file(str(template_path), content)
                generated_files.append(str(template_path))

        return generated_files

    def _generate_deployment_configs(
        self, output_dir: str, variables: dict[str, Any]
    ) -> list[str]:
        """Generate deployment configuration files."""
        generated_files = []
        deploy_dir = Path(output_dir) / "deploy"
        deploy_dir.mkdir(exist_ok=True)

        # Docker Compose for production
        docker_compose = self._render_template(
            "deploy/docker-compose.prod.yml", variables
        )
        if docker_compose:
            docker_compose_path = deploy_dir / "docker-compose.prod.yml"
            self._write_file(str(docker_compose_path), docker_compose)
            generated_files.append(str(docker_compose_path))

        # Kubernetes manifests
        k8s_dir = deploy_dir / "kubernetes"
        k8s_dir.mkdir(exist_ok=True)

        k8s_manifests = [
            "namespace.yaml",
            "configmap.yaml",
            "secret.yaml",
            "deployment.yaml",
            "service.yaml",
            "ingress.yaml",
            "hpa.yaml",
            "pdb.yaml",
        ]

        for manifest in k8s_manifests:
            content = self._render_template(f"deploy/kubernetes/{manifest}", variables)
            if content:
                manifest_path = k8s_dir / manifest
                self._write_file(str(manifest_path), content)
                generated_files.append(str(manifest_path))

        # Helm chart if needed
        if variables.get("generate_helm_chart"):
            helm_dir = deploy_dir / "helm"
            self._generate_helm_chart(helm_dir, variables)
            generated_files.extend([str(p) for p in helm_dir.rglob("*") if p.is_file()])

        # Terraform configuration if needed
        if variables.get("generate_terraform"):
            terraform_dir = deploy_dir / "terraform"
            self._generate_terraform_config(terraform_dir, variables)
            generated_files.extend(
                [str(p) for p in terraform_dir.rglob("*") if p.is_file()]
            )

        return generated_files

    def _generate_helm_chart(self, output_dir: Path, variables: dict[str, Any]) -> None:
        """Generate a Helm chart for the application."""
        chart_dir = output_dir / variables.get("app_name", "app")
        chart_dir.mkdir(parents=True, exist_ok=True)

        # Chart.yaml
        chart_yaml = self._render_template("deploy/helm/Chart.yaml", variables)
        if chart_yaml:
            (chart_dir / "Chart.yaml").write_text(chart_yaml)

        # values.yaml
        values_yaml = self._render_template("deploy/helm/values.yaml", variables)
        if values_yaml:
            (chart_dir / "values.yaml").write_text(values_yaml)

        # templates directory
        templates_dir = chart_dir / "templates"
        templates_dir.mkdir(exist_ok=True)

        # Generate template files
        template_files = [
            "deployment.yaml",
            "service.yaml",
            "ingress.yaml",
            "serviceaccount.yaml",
            "_helpers.tpl",
            "NOTES.txt",
        ]

        for template in template_files:
            content = self._render_template(
                f"deploy/helm/templates/{template}", variables
            )
            if content:
                (templates_dir / template).write_text(content)

    def _generate_terraform_config(
        self, output_dir: Path, variables: dict[str, Any]
    ) -> None:
        """Generate Terraform configuration for infrastructure as code."""
        # Main configuration files
        main_tf = self._render_template("deploy/terraform/main.tf", variables)
        if main_tf:
            (output_dir / "main.tf").write_text(main_tf)

        variables_tf = self._render_template("deploy/terraform/variables.tf", variables)
        if variables_tf:
            (output_dir / "variables.tf").write_text(variables_tf)

        outputs_tf = self._render_template("deploy/terraform/outputs.tf", variables)
        if outputs_tf:
            (output_dir / "outputs.tf").write_text(outputs_tf)

        # Environment-specific configurations
        envs = ["dev", "staging", "prod"]
        for env in envs:
            env_dir = output_dir / env
            env_dir.mkdir(exist_ok=True)

            env_vars = self._render_template(
                "deploy/terraform/env/vars.tfvars", {**variables, "environment": env}
            )
            if env_vars:
                (env_dir / f"{env}.tfvars").write_text(env_vars)

            backend_tf = self._render_template(
                "deploy/terraform/env/backend.tf", {**variables, "environment": env}
            )
            if backend_tf:
                (env_dir / "backend.tf").write_text(backend_tf)
