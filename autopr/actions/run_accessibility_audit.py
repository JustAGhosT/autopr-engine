import asyncio

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    url: str = "http://localhost:3000"
    fail_on_critical: bool = True


class Outputs(pydantic.BaseModel):
    success: bool
    report: str
    violations_count: int
    violations: list[dict]


class RunAccessibilityAudit(Action[Inputs, Outputs]):
    """
    [Simulation] Runs an accessibility audit (like axe-core) on a page
    and reports any violations.
    """

    id = "run_accessibility_audit"

    async def run(self, inputs: Inputs) -> Outputs:
        report_lines = ["[Simulation] Accessibility Audit Report"]

        # Simulate running axe-core and getting violations
        simulated_violations = [
            {
                "id": "color-contrast",
                "impact": "critical",
                "description": "Ensures the contrast between foreground and background colors meets WCAG 2 AA contrast ratio thresholds",
                "nodes": 1,
            },
            {
                "id": "image-alt",
                "impact": "serious",
                "description": "Ensures <img> elements have alternate text or a role of none or presentation",
                "nodes": 2,
            },
        ]

        report_lines.append(f"Auditing URL: {inputs.url}")

        if not simulated_violations:
            return Outputs(
                success=True,
                report=" No accessibility violations found.",
                violations_count=0,
                violations=[],
            )

        success = True
        for violation in simulated_violations:
            if inputs.fail_on_critical and violation["impact"] == "critical":
                success = False
            report_lines.append(
                f"- [{str(violation['impact']).upper()}] {violation['id']}: Affects {violation['nodes']} node(s)."
            )

        return Outputs(
            success=success,
            report="\n".join(report_lines),
            violations_count=len(simulated_violations),
            violations=simulated_violations,
        )


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    asyncio.run(
        run_action_manually(
            action=RunAccessibilityAudit,
            inputs=Inputs(),
        )
    )
