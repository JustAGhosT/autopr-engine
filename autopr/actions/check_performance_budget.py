import asyncio

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    url: str = "http://localhost:3000"
    # Example performance budget
    budget: dict = {
        "performance": 90,
        "lcp": 2500,  # Largest Contentful Paint in ms
        "cls": 0.1,  # Cumulative Layout Shift
        "bundle_size_kb": 150,
    }


class Outputs(pydantic.BaseModel):
    success: bool
    report: str
    metrics: dict


class CheckPerformanceBudget(Action[Inputs, Outputs]):
    """
    [Simulation] Runs a performance audit (like Lighthouse) and checks key metrics
    against a predefined budget.
    """

    id = "check_performance_budget"

    async def run(self, inputs: Inputs) -> Outputs:
        report_lines = ["[Simulation] Performance Budget Report"]
        success = True

        # Simulate running Lighthouse and getting metrics
        simulated_metrics = {
            "performance": 95,
            "lcp": 2100,
            "cls": 0.05,
            "bundle_size_kb": 120,
        }
        report_lines.append(f"Auditing URL: {inputs.url}")

        for metric, budget_value in inputs.budget.items():
            current_value = simulated_metrics.get(metric, 0)
            is_over_budget = (
                current_value > budget_value
                if metric != "performance"
                else current_value < budget_value
            )

            if is_over_budget:
                success = False
                status = "❌ FAILED"
                details = f"(Budget: {budget_value}, Found: {current_value})"
            else:
                status = "✅ PASSED"
                details = f"(Budget: {budget_value}, Found: {current_value})"

            report_lines.append(f"- {metric.upper()}: {status} {details}")

        return Outputs(success=success, report="\\n".join(report_lines), metrics=simulated_metrics)


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=CheckPerformanceBudget,
            inputs=Inputs(),
        )
    )
