"""
Task Definitions and Phase Configuration
Centralized definitions for all implementation tasks and phases
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    """Individual implementation task definition"""

    name: str
    description: str
    category: str
    complexity: str  # "low", "medium", "high"
    estimated_hours: int
    dependencies: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    packages_required: list[str] = field(default_factory=list)


@dataclass
class Phase:
    """Implementation phase definition"""

    name: str
    display_name: str
    duration_days: int
    tasks: list[str]
    depends_on: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)


class TaskRegistry:
    """Registry of all implementation tasks"""

    def __init__(self) -> None:
        self._tasks = self._initialize_tasks()

    def _initialize_tasks(self) -> dict[str, Task]:
        """Initialize all task definitions"""
        return {
            # Immediate Priority Tasks
            "setup_sentry_monitoring": Task(
                name="setup_sentry_monitoring",
                description="Setup Sentry for error tracking and performance monitoring",
                category="monitoring",
                complexity="medium",
                estimated_hours=4,
                files_created=[
                    "autopr/monitoring/sentry_config.py",
                    "autopr/monitoring/__init__.py",
                    "requirements.txt",
                ],
                packages_required=["sentry-sdk[fastapi]>=1.32.0"],
            ),
            "implement_structured_logging": Task(
                name="implement_structured_logging",
                description="Implement structured JSON logging with correlation IDs",
                category="logging",
                complexity="medium",
                estimated_hours=3,
                files_created=[
                    "autopr/logging/structured_logger.py",
                    "autopr/logging/correlation.py",
                    "autopr/logging/__init__.py",
                ],
                packages_required=["structlog>=23.1.0", "python-json-logger>=2.0.7"],
            ),
            "setup_redis_caching": Task(
                name="setup_redis_caching",
                description="Setup Redis caching for LLM responses and API calls",
                category="caching",
                complexity="high",
                estimated_hours=6,
                files_created=[
                    "autopr/caching/redis_cache.py",
                    "autopr/caching/cache_manager.py",
                    "autopr/caching/decorators.py",
                    "autopr/caching/__init__.py",
                ],
                packages_required=["redis>=4.6.0", "aioredis>=2.0.1"],
            ),
            "create_health_checks": Task(
                name="create_health_checks",
                description="Create comprehensive health check endpoints",
                category="monitoring",
                complexity="medium",
                estimated_hours=4,
                files_created=[
                    "autopr/health/health_checks.py",
                    "autopr/health/system_monitor.py",
                    "autopr/health/__init__.py",
                ],
                packages_required=["psutil>=5.9.0"],
            ),
            "implement_basic_circuit_breakers": Task(
                name="implement_basic_circuit_breakers",
                description="Implement circuit breaker pattern for external API calls",
                category="resilience",
                complexity="high",
                estimated_hours=5,
                files_created=[
                    "autopr/resilience/circuit_breaker.py",
                    "autopr/resilience/retry_policies.py",
                    "autopr/resilience/__init__.py",
                ],
                packages_required=["tenacity>=8.2.0"],
            ),
            # Medium Priority Tasks
            "setup_postgresql_integration": Task(
                name="setup_postgresql_integration",
                description="Setup PostgreSQL integration for data persistence",
                category="database",
                complexity="high",
                estimated_hours=8,
                dependencies=["implement_structured_logging"],
                files_created=[
                    "autopr/database/postgresql.py",
                    "autopr/database/migrations/",
                    "autopr/database/models.py",
                    "autopr/database/__init__.py",
                ],
                packages_required=["asyncpg>=0.30.0", "alembic>=1.12.0"],
            ),
            "implement_prometheus_metrics": Task(
                name="implement_prometheus_metrics",
                description="Implement Prometheus metrics collection",
                category="monitoring",
                complexity="medium",
                estimated_hours=5,
                dependencies=["create_health_checks"],
                files_created=[
                    "autopr/metrics/prometheus_metrics.py",
                    "autopr/metrics/custom_metrics.py",
                    "autopr/metrics/__init__.py",
                ],
                packages_required=["prometheus-client>=0.17.0"],
            ),
            "setup_oauth2_authentication": Task(
                name="setup_oauth2_authentication",
                description="Setup OAuth 2.0 authentication with GitHub/Google",
                category="authentication",
                complexity="high",
                estimated_hours=10,
                files_created=[
                    "autopr/auth/oauth2.py",
                    "autopr/auth/providers.py",
                    "autopr/auth/middleware.py",
                    "autopr/auth/__init__.py",
                ],
                packages_required=["authlib>=1.2.1", "python-jose>=3.3.0"],
            ),
            "implement_advanced_llm_routing": Task(
                name="implement_advanced_llm_routing",
                description="Implement advanced LLM routing and load balancing",
                category="ai",
                complexity="high",
                estimated_hours=12,
                dependencies=[
                    "setup_redis_caching",
                    "implement_basic_circuit_breakers",
                ],
                files_created=[
                    "autopr/ai/routing/llm_router.py",
                    "autopr/ai/routing/load_balancer.py",
                    "autopr/ai/routing/fallback_handler.py",
                    "autopr/ai/routing/__init__.py",
                ],
                packages_required=["aiohttp>=3.8.5"],
            ),
            "create_comprehensive_testing": Task(
                name="create_comprehensive_testing",
                description="Create comprehensive testing framework with fixtures",
                category="testing",
                complexity="high",
                estimated_hours=15,
                files_created=[
                    "tests/fixtures/",
                    "tests/integration/",
                    "tests/unit/",
                    "tests/conftest.py",
                    "pytest.ini",
                ],
                packages_required=[
                    "pytest>=7.4.0",
                    "pytest-asyncio>=0.21.0",
                    "pytest-mock>=3.13.0",
                ],
            ),
            # Strategic Priority Tasks
            "implement_rag_system": Task(
                name="implement_rag_system",
                description="Implement RAG (Retrieval Augmented Generation) system",
                category="ai",
                complexity="high",
                estimated_hours=20,
                dependencies=[
                    "setup_postgresql_integration",
                    "implement_advanced_llm_routing",
                ],
                files_created=[
                    "autopr/ai/rag/vector_store.py",
                    "autopr/ai/rag/document_processor.py",
                    "autopr/ai/rag/retriever.py",
                    "autopr/ai/rag/__init__.py",
                ],
                packages_required=["chromadb>=0.4.0", "sentence-transformers>=2.2.0"],
            ),
            "create_analytics_dashboard": Task(
                name="create_analytics_dashboard",
                description="Create analytics dashboard for monitoring and insights",
                category="analytics",
                complexity="high",
                estimated_hours=25,
                dependencies=[
                    "implement_prometheus_metrics",
                    "setup_postgresql_integration",
                ],
                files_created=[
                    "autopr/dashboard/analytics.py",
                    "autopr/dashboard/templates/",
                    "autopr/dashboard/static/",
                    "autopr/dashboard/__init__.py",
                ],
                packages_required=["streamlit>=1.25.0", "plotly>=5.15.0"],
            ),
            "setup_fine_tuned_models": Task(
                name="setup_fine_tuned_models",
                description="Setup fine-tuned model training and deployment pipeline",
                category="ai",
                complexity="high",
                estimated_hours=30,
                dependencies=["implement_rag_system", "create_comprehensive_testing"],
                files_created=[
                    "autopr/ai/training/fine_tuning.py",
                    "autopr/ai/training/data_preparation.py",
                    "autopr/ai/training/model_deployment.py",
                    "autopr/ai/training/__init__.py",
                ],
                packages_required=[
                    "transformers>=4.30.0",
                    "datasets>=2.14.0",
                    "accelerate>=0.21.0",
                ],
            ),
            "implement_multi_cloud_deployment": Task(
                name="implement_multi_cloud_deployment",
                description="Implement multi-cloud deployment configuration",
                category="deployment",
                complexity="high",
                estimated_hours=20,
                dependencies=["create_analytics_dashboard"],
                files_created=[
                    "deployment/aws/",
                    "deployment/gcp/",
                    "deployment/azure/",
                    "deployment/kubernetes/",
                    "docker-compose.prod.yml",
                ],
                packages_required=[
                    "boto3>=1.28.0",
                    "google-cloud>=0.34.0",
                    "azure-mgmt>=4.0.0",
                ],
            ),
        }

    def get_task(self, task_name: str) -> Task:
        """Get task definition by name"""
        if task_name not in self._tasks:
            msg = f"Unknown task: {task_name}"
            raise ValueError(msg)
        return self._tasks[task_name]

    def get_all_tasks(self) -> dict[str, Task]:
        """Get all task definitions"""
        return self._tasks.copy()

    def get_tasks_by_category(self, category: str) -> list[Task]:
        """Get all tasks in a specific category"""
        return [task for task in self._tasks.values() if task.category == category]

    def get_tasks_by_complexity(self, complexity: str) -> list[Task]:
        """Get all tasks with specific complexity"""
        return [task for task in self._tasks.values() if task.complexity == complexity]


class ImplementationPhases:
    """Implementation phase definitions and management"""

    def __init__(self) -> None:
        self._phases = self._initialize_phases()

    def _initialize_phases(self) -> dict[str, Phase]:
        """Initialize all phase definitions"""
        return {
            "immediate": Phase(
                name="immediate",
                display_name="Immediate Priority (Week 1-2)",
                duration_days=10,
                tasks=[
                    "setup_sentry_monitoring",
                    "implement_structured_logging",
                    "setup_redis_caching",
                    "create_health_checks",
                    "implement_basic_circuit_breakers",
                ],
                success_criteria=[
                    "Error tracking is functional",
                    "Structured logging is implemented",
                    "Redis caching is working",
                    "Health checks return 200 OK",
                    "Circuit breakers prevent cascade failures",
                ],
            ),
            "medium": Phase(
                name="medium",
                display_name="Medium Priority (Week 3-6)",
                duration_days=25,
                depends_on=["immediate"],
                tasks=[
                    "setup_postgresql_integration",
                    "implement_prometheus_metrics",
                    "setup_oauth2_authentication",
                    "implement_advanced_llm_routing",
                    "create_comprehensive_testing",
                ],
                success_criteria=[
                    "PostgreSQL integration is working",
                    "Prometheus metrics are collected",
                    "OAuth2 authentication is functional",
                    "LLM routing handles failures gracefully",
                    "Test coverage is above 80%",
                ],
            ),
            "strategic": Phase(
                name="strategic",
                display_name="Long-term Strategic (Month 2+)",
                duration_days=45,
                depends_on=["medium"],
                tasks=[
                    "implement_rag_system",
                    "create_analytics_dashboard",
                    "setup_fine_tuned_models",
                    "implement_multi_cloud_deployment",
                ],
                success_criteria=[
                    "RAG system improves response quality",
                    "Analytics dashboard provides insights",
                    "Fine-tuned models are deployed",
                    "Multi-cloud deployment is automated",
                ],
            ),
        }

    def get_phase(self, phase_name: str) -> Phase:
        """Get phase definition by name"""
        if phase_name not in self._phases:
            msg = f"Unknown phase: {phase_name}"
            raise ValueError(msg)
        return self._phases[phase_name]

    def get_all_phases(self) -> dict[str, Phase]:
        """Get all phase definitions"""
        return self._phases.copy()

    def get_phase_order(self) -> list[str]:
        """Get phases in dependency order"""
        return ["immediate", "medium", "strategic"]

    def validate_phase_dependencies(self, phase_name: str) -> list[str]:
        """Validate that phase dependencies are met"""
        phase = self.get_phase(phase_name)

        return [
            dep_phase
            for dep_phase in phase.depends_on
            if not self._is_phase_completed(dep_phase)
        ]

    def _is_phase_completed(self, phase_name: str) -> bool:
        """Check if a phase has been completed"""
        from pathlib import Path

        completion_file = Path.cwd() / f".autopr_phase_{phase_name}_complete"
        return completion_file.exists()
