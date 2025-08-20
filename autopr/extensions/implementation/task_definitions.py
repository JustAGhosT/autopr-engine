"""
Task Definitions Module

Centralized task definitions and phase configurations for implementation roadmap.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    """Represents a task in the implementation roadmap."""

    id: str
    description: str
    status: str = "pending"
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Default factory handles None values automatically
        pass


class TaskRegistry:
    """Registry for all available implementation tasks."""

    @staticmethod
    def get_task_definitions() -> dict[str, dict[str, Any]]:
        """Get all task definitions with their metadata."""
        return {
            # Immediate Priority Tasks
            "setup_sentry_monitoring": {
                "name": "Setup Sentry Monitoring",
                "description": "Configure Sentry for error tracking and performance monitoring",
                "category": "monitoring",
                "complexity": "medium",
                "estimated_time": "2-3 hours",
                "dependencies": [],
                "files_created": ["sentry_config.py", "requirements-sentry.txt"],
                "env_vars": ["SENTRY_DSN", "SENTRY_ENVIRONMENT"],
            },
            "implement_structured_logging": {
                "name": "Implement Structured Logging",
                "description": "Set up JSON-based structured logging with proper formatters",
                "category": "logging",
                "complexity": "low",
                "estimated_time": "1-2 hours",
                "dependencies": [],
                "files_created": ["logging_config.py", "log_formatters.py"],
                "env_vars": ["LOG_LEVEL", "LOG_FORMAT"],
            },
            "setup_redis_caching": {
                "name": "Setup Redis Caching",
                "description": "Configure Redis for LLM response and API call caching",
                "category": "caching",
                "complexity": "medium",
                "estimated_time": "3-4 hours",
                "dependencies": [],
                "files_created": [
                    "redis_config.py",
                    "cache_manager.py",
                    "cache_decorators.py",
                ],
                "env_vars": ["REDIS_URL", "REDIS_PASSWORD", "CACHE_TTL"],
            },
            "create_health_checks": {
                "name": "Create Health Checks",
                "description": "Implement comprehensive health check endpoints",
                "category": "monitoring",
                "complexity": "medium",
                "estimated_time": "2-3 hours",
                "dependencies": [],
                "files_created": ["health_checks.py", "health_endpoints.py"],
                "env_vars": [],
            },
            "implement_basic_circuit_breakers": {
                "name": "Implement Circuit Breakers",
                "description": "Add circuit breaker pattern for external API calls",
                "category": "resilience",
                "complexity": "high",
                "estimated_time": "4-5 hours",
                "dependencies": [],
                "files_created": ["circuit_breaker.py", "api_resilience.py"],
                "env_vars": ["CIRCUIT_BREAKER_THRESHOLD", "CIRCUIT_BREAKER_TIMEOUT"],
            },
            # Medium Priority Tasks
            "setup_postgresql_integration": {
                "name": "Setup PostgreSQL Integration",
                "description": "Configure PostgreSQL for data persistence",
                "category": "database",
                "complexity": "high",
                "estimated_time": "4-6 hours",
                "dependencies": ["setup_sentry_monitoring"],
                "files_created": ["database_config.py", "models.py", "migrations/"],
                "env_vars": ["DATABASE_URL", "DB_POOL_SIZE"],
            },
            "implement_prometheus_metrics": {
                "name": "Implement Prometheus Metrics",
                "description": "Set up Prometheus metrics collection",
                "category": "monitoring",
                "complexity": "medium",
                "estimated_time": "3-4 hours",
                "dependencies": ["create_health_checks"],
                "files_created": ["metrics_config.py", "custom_metrics.py"],
                "env_vars": ["METRICS_PORT", "METRICS_PATH"],
            },
            "setup_oauth2_authentication": {
                "name": "Setup OAuth2 Authentication",
                "description": "Implement OAuth 2.0 authentication flow",
                "category": "security",
                "complexity": "high",
                "estimated_time": "5-6 hours",
                "dependencies": ["setup_postgresql_integration"],
                "files_created": [
                    "auth_config.py",
                    "oauth_handlers.py",
                    "token_manager.py",
                ],
                "env_vars": [
                    "OAUTH_CLIENT_ID",
                    "OAUTH_CLIENT_SECRET",
                    "JWT_SECRET_KEY",
                ],
            },
            "implement_advanced_llm_routing": {
                "name": "Advanced LLM Routing",
                "description": "Implement intelligent LLM routing and load balancing",
                "category": "ai",
                "complexity": "high",
                "estimated_time": "6-8 hours",
                "dependencies": ["setup_redis_caching", "implement_prometheus_metrics"],
                "files_created": [
                    "llm_router.py",
                    "load_balancer.py",
                    "model_selector.py",
                ],
                "env_vars": ["LLM_ROUTING_STRATEGY", "LOAD_BALANCER_ALGORITHM"],
            },
            "create_comprehensive_testing": {
                "name": "Comprehensive Testing Framework",
                "description": "Set up unit, integration, and performance testing",
                "category": "testing",
                "complexity": "high",
                "estimated_time": "8-10 hours",
                "dependencies": ["implement_basic_circuit_breakers"],
                "files_created": [
                    "test_config.py",
                    "test_fixtures.py",
                    "performance_tests.py",
                    "integration_tests.py",
                ],
                "env_vars": ["TEST_DATABASE_URL", "TEST_REDIS_URL"],
            },
            # Strategic Priority Tasks
            "implement_rag_system": {
                "name": "RAG System Implementation",
                "description": "Implement Retrieval Augmented Generation system",
                "category": "ai",
                "complexity": "very_high",
                "estimated_time": "10-15 hours",
                "dependencies": [
                    "setup_postgresql_integration",
                    "implement_advanced_llm_routing",
                ],
                "files_created": [
                    "rag_system.py",
                    "vector_store.py",
                    "retrieval_engine.py",
                    "embedding_manager.py",
                ],
                "env_vars": ["VECTOR_DB_URL", "EMBEDDING_MODEL", "RAG_CHUNK_SIZE"],
            },
            "create_analytics_dashboard": {
                "name": "Analytics Dashboard",
                "description": "Build comprehensive analytics and monitoring dashboard",
                "category": "analytics",
                "complexity": "very_high",
                "estimated_time": "12-16 hours",
                "dependencies": [
                    "implement_prometheus_metrics",
                    "setup_oauth2_authentication",
                ],
                "files_created": [
                    "dashboard_app.py",
                    "analytics_queries.py",
                    "dashboard_templates/",
                    "static/dashboard/",
                ],
                "env_vars": ["DASHBOARD_SECRET_KEY", "ANALYTICS_DB_URL"],
            },
            "setup_fine_tuned_models": {
                "name": "Fine-tuned Models Setup",
                "description": "Configure fine-tuned model training and deployment",
                "category": "ai",
                "complexity": "very_high",
                "estimated_time": "15-20 hours",
                "dependencies": [
                    "implement_rag_system",
                    "create_comprehensive_testing",
                ],
                "files_created": [
                    "model_training.py",
                    "fine_tuning_pipeline.py",
                    "model_deployment.py",
                    "training_data_processor.py",
                ],
                "env_vars": [
                    "TRAINING_DATA_PATH",
                    "MODEL_REGISTRY_URL",
                    "FINE_TUNING_API_KEY",
                ],
            },
            "implement_multi_cloud_deployment": {
                "name": "Multi-cloud Deployment",
                "description": "Set up deployment across multiple cloud providers",
                "category": "infrastructure",
                "complexity": "very_high",
                "estimated_time": "20-25 hours",
                "dependencies": [
                    "create_analytics_dashboard",
                    "setup_fine_tuned_models",
                ],
                "files_created": [
                    "cloud_config.py",
                    "deployment_scripts/",
                    "terraform/",
                    "kubernetes/",
                ],
                "env_vars": [
                    "AWS_ACCESS_KEY_ID",
                    "GCP_PROJECT_ID",
                    "AZURE_SUBSCRIPTION_ID",
                ],
            },
        }

    @staticmethod
    def get_phase_definitions() -> dict[str, dict[str, Any]]:
        """Get phase definitions with their task assignments."""
        return {
            "immediate": {
                "name": "Immediate Priority (Week 1-2)",
                "description": "Essential production-ready features",
                "duration_days": 10,
                "priority": 1,
                "tasks": [
                    "setup_sentry_monitoring",
                    "implement_structured_logging",
                    "setup_redis_caching",
                    "create_health_checks",
                    "implement_basic_circuit_breakers",
                ],
                "success_criteria": [
                    "Error tracking is functional",
                    "Structured logs are being generated",
                    "Redis caching is working",
                    "Health endpoints return 200",
                    "Circuit breakers prevent cascading failures",
                ],
            },
            "medium": {
                "name": "Medium Priority (Week 3-6)",
                "description": "Enhanced functionality and integrations",
                "duration_days": 25,
                "priority": 2,
                "depends_on": ["immediate"],
                "tasks": [
                    "setup_postgresql_integration",
                    "implement_prometheus_metrics",
                    "setup_oauth2_authentication",
                    "implement_advanced_llm_routing",
                    "create_comprehensive_testing",
                ],
                "success_criteria": [
                    "Database is properly configured",
                    "Metrics are being collected",
                    "Authentication is working",
                    "LLM routing is optimized",
                    "Test coverage > 80%",
                ],
            },
            "strategic": {
                "name": "Long-term Strategic (Month 2+)",
                "description": "Advanced AI features and scalability",
                "duration_days": 45,
                "priority": 3,
                "depends_on": ["medium"],
                "tasks": [
                    "implement_rag_system",
                    "create_analytics_dashboard",
                    "setup_fine_tuned_models",
                    "implement_multi_cloud_deployment",
                ],
                "success_criteria": [
                    "RAG system improves response quality",
                    "Dashboard provides actionable insights",
                    "Fine-tuned models are deployed",
                    "Multi-cloud deployment is stable",
                ],
            },
        }

    @staticmethod
    def get_task_categories() -> dict[str, list[str]]:
        """Get tasks organized by category."""
        tasks = TaskRegistry.get_task_definitions()
        categories: dict[str, list[str]] = {}

        for task_id, task_info in tasks.items():
            category = task_info.get("category", "uncategorized")
            if category not in categories:
                categories[category] = []
            categories[category].append(task_id)

        return categories

    @staticmethod
    def get_dependency_graph() -> dict[str, list[str]]:
        """Get the complete dependency graph for all tasks."""
        tasks = TaskRegistry.get_task_definitions()
        return {task_id: task_info.get("dependencies", []) for task_id, task_info in tasks.items()}
