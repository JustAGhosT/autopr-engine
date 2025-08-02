# production_monitoring.py
import asyncio
import logging

import aiohttp
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import metrics, trace


class ContinueProductionMonitoring:
    def __init__(self, connection_string: str):
        # Configure Azure Monitor
        configure_azure_monitor(connection_string=connection_string)

        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)

        # Create metrics
        self.request_counter = self.meter.create_counter(
            "continue_requests_total", description="Total number of Continue.dev requests"
        )

        self.response_time_histogram = self.meter.create_histogram(
            "continue_response_time_seconds", description="Response time for Continue.dev requests"
        )

        self.cost_counter = self.meter.create_counter(
            "continue_cost_total", description="Total cost of Continue.dev requests"
        )

        self.logger = logging.getLogger(__name__)

    async def monitor_request(
        self,
        model: str,
        prompt: str,
        response: str,
        user_id: str,
        response_time: float,
        cost: float,
    ) -> None:
        """Monitor individual request"""

        with self.tracer.start_as_current_span("continue_request") as span:
            # Set span attributes
            span.set_attribute("model", model)
            span.set_attribute("user_id", user_id)
            span.set_attribute("prompt_length", len(prompt))
            span.set_attribute("response_length", len(response))
            span.set_attribute("response_time", response_time)
            span.set_attribute("cost", cost)

            # Update metrics
            self.request_counter.add(1, {"model": model, "user": user_id})
            self.response_time_histogram.record(response_time, {"model": model})
            self.cost_counter.add(cost, {"model": model, "user": user_id})

            # Log request
            self.logger.info(
                f"Continue request - Model: {model}, User: {user_id}, "
                f"Response time: {response_time:.2f}s, Cost: ${cost:.4f}"
            )

    async def check_model_health(self) -> dict[str, bool]:
        """Check health of all model endpoints"""

        endpoints = [
            (
                "gpt-4.1",
                "https://dev-saf-openai-phoenixvc-ai.openai.azure.com/openai/deployments/gpt-4.1/chat/completions",
            ),
            (
                "gpt-4o",
                "https://dev-saf-openai-phoenixvc-ai.openai.azure.com/openai/deployments/gpt-4o/chat/completions",
            ),
            (
                "model-router",
                "https://jurie-mcnb2krj-swedencentral.cognitiveservices.azure.com/openai/deployments/model-router/chat/completions",
            ),
        ]

        health_status = {}

        for model_name, endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    test_payload = {
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 5,
                    }

                    async with session.post(
                        f"{endpoint}?api-version=2025-01-01-preview",
                        json=test_payload,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as response:
                        health_status[model_name] = response.status == 200

            except Exception as e:
                health_status[model_name] = False
                self.logger.error(f"Health check failed for {model_name}: {e}")

        return health_status

    async def generate_usage_report(self, days: int = 7) -> dict:
        """Generate usage report for the past N days"""

        # This would typically query Azure Monitor logs
        # For now, returning a sample structure

        return {
            "period": f"Last {days} days",
            "total_requests": 1250,
            "total_cost": 45.67,
            "models": {
                "gpt-4.1": {"requests": 450, "cost": 28.90, "avg_response_time": 2.3},
                "gpt-4o": {"requests": 650, "cost": 15.23, "avg_response_time": 1.8},
                "model-router": {"requests": 150, "cost": 1.54, "avg_response_time": 0.5},
            },
            "top_users": [
                {"user_id": "dev1@company.com", "requests": 89, "cost": 12.45},
                {"user_id": "dev2@company.com", "requests": 76, "cost": 9.87},
                {"user_id": "dev3@company.com", "requests": 65, "cost": 8.23},
            ],
        }


# Example usage and monitoring setup
async def main() -> None:
    monitor = ContinueProductionMonitoring(
        connection_string="InstrumentationKey=your-key;IngestionEndpoint=https://swedencentral-1.in.applicationinsights.azure.com/"
    )

    # Check model health
    health = await monitor.check_model_health()
    print("Model Health Status:")
    for model, status in health.items():
        print(f"  {model}: {'✅ Healthy' if status else '❌ Unhealthy'}")

    # Generate usage report
    report = await monitor.generate_usage_report()
    print(f"\nUsage Report ({report['period']}):")
    print(f"Total Requests: {report['total_requests']:,}")
    print(f"Total Cost: ${report['total_cost']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
