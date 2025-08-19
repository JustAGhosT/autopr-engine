#!/usr/bin/env python3
"""
Markdown Format Generator Module
===============================

Generates documentation in Markdown format.
"""

from datetime import datetime

from discovery.content_analyzer import TemplateAnalysis

from .base import BaseFormatGenerator


class MarkdownGenerator(BaseFormatGenerator):
    """Generates Markdown documentation."""

    def generate_platform_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate platform guide in Markdown format."""
        return self.generate_content(
            "platform_guide",
            platform_name=analysis.name.replace("_", " ").title(),
            platform_info=analysis.platform_info,
            key_features=analysis.key_features,
            variables=analysis.variables,
            development_approach=analysis.metadata.get("development_approach", {}),
            best_practices=analysis.metadata.get("best_practices", {}),
            troubleshooting=analysis.troubleshooting,
            pricing=analysis.platform_info.get("pricing", {}),
        )

    def generate_use_case_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate use case guide in Markdown format."""
        return self.generate_content(
            "use_case_guide",
            use_case_name=analysis.name.replace("_", " ").title(),
            use_case_info=analysis.use_case_info,
            key_features=analysis.key_features,
            implementation_steps=analysis.use_case_info.get("implementation_steps", []),
            configuration_options=analysis.variables,
            recommended_platforms=analysis.metadata.get("recommended_platforms", []),
            examples=analysis.examples,
            best_practices=analysis.best_practices,
            common_pitfalls=analysis.metadata.get("common_pitfalls", []),
        )

    def generate_integration_guide(self, analysis: TemplateAnalysis) -> str:
        """Generate integration guide in Markdown format."""
        return self.generate_content(
            "integration_guide",
            integration_name=analysis.name.replace("_", " ").title(),
            integration_info=analysis.integration_info,
            key_features=analysis.key_features,
            setup_steps=analysis.integration_info.get("setup_steps", []),
            configuration_options=analysis.variables,
            examples=analysis.examples,
            troubleshooting=analysis.troubleshooting,
        )

    def generate_main_index(self, analyses: list[TemplateAnalysis]) -> str:
        """Generate main documentation index."""
        # Group analyses by category
        platforms = [a for a in analyses if a.category == "platform"]
        use_cases = [a for a in analyses if a.category == "use_case"]
        integrations = [a for a in analyses if a.category == "integration"]

        content = f"""# Template Documentation

*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

Welcome to the comprehensive template documentation. This guide covers all available templates for no-code platform development.

## Quick Start

1. **Choose Your Platform**: Browse the [Platform Guides](#platform-guides) to find the right development environment
2. **Select a Use Case**: Explore [Use Case Templates](#use-case-templates) for specific application types
3. **Add Integrations**: Enhance your application with [Integration Templates](#integration-templates)

## Platform Guides

Build applications on these no-code platforms:

"""

        for platform in sorted(platforms, key=lambda x: x.name):
            platform_name = platform.name.replace("_", " ").title()
            description = platform.platform_info.get("description", "No description available")
            content += f"- **[{platform_name}](platforms/{platform.name}.md)**: {description}\n"

        content += (
            "\n## Use Case Templates\n\nPre-built templates for common application types:\n\n"
        )

        for use_case in sorted(use_cases, key=lambda x: x.name):
            use_case_name = use_case.name.replace("_", " ").title()
            description = use_case.use_case_info.get("description", "No description available")
            content += f"- **[{use_case_name}](use-cases/{use_case.name}.md)**: {description}\n"

        content += "\n## Integration Templates\n\nAdd functionality with these integrations:\n\n"

        for integration in sorted(integrations, key=lambda x: x.name):
            integration_name = integration.name.replace("_", " ").title()
            description = integration.integration_info.get(
                "description", "No description available"
            )
            content += (
                f"- **[{integration_name}](integrations/{integration.name}.md)**: {description}\n"
            )

        content += """

## Getting Started Guide

New to no-code development? Start with our [comprehensive getting started guide](getting_started.md).

## Platform Comparison

Not sure which platform to choose? Check out our [platform comparison guide](platform_comparison.md).

## Support

- [Troubleshooting Guide](troubleshooting.md)
- [Best Practices](best_practices.md)
- [Community Support](community.md)

---

*Happy building! 🚀*
"""

        return content

    def generate_comparison_guide(self, platform_analyses: list[TemplateAnalysis]) -> str:
        """Generate platform comparison guide."""
        content = f"""# Platform Comparison Guide

*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

Choose the right no-code platform for your project with this comprehensive comparison.

## Quick Comparison

| Platform | Complexity | Best For | Pricing |
|----------|------------|----------|---------|
"""

        for analysis in sorted(platform_analyses, key=lambda x: x.name):
            platform_name = analysis.name.replace("_", " ").title()
            complexity = analysis.complexity.title()
            best_for = analysis.platform_info.get("best_for", "General use")
            pricing = analysis.platform_info.get("pricing_summary", "Varies")
            content += f"| {platform_name} | {complexity} | {best_for} | {pricing} |\n"

        content += "\n## Detailed Comparison\n\n"

        for analysis in sorted(platform_analyses, key=lambda x: x.name):
            platform_name = analysis.name.replace("_", " ").title()
            content += f"### {platform_name}\n\n"
            content += f"**Complexity**: {analysis.complexity.title()}\n\n"

            if analysis.key_features:
                content += "**Key Features**:\n"
                for feature in analysis.key_features[:5]:  # Limit to top 5
                    content += f"- {feature}\n"
                content += "\n"

            if analysis.platform_info.get("pros"):
                content += "**Pros**:\n"
                for pro in analysis.platform_info["pros"]:
                    content += f"- {pro}\n"
                content += "\n"

            if analysis.platform_info.get("cons"):
                content += "**Cons**:\n"
                for con in analysis.platform_info["cons"]:
                    content += f"- {con}\n"
                content += "\n"

        content += """## Decision Matrix

Use this matrix to help choose the right platform:

### For Beginners
- **Replit**: Great for learning and simple projects
- **Glide**: Perfect for data-driven apps
- **Bubble**: Comprehensive but has a learning curve

### For Advanced Users
- **Webflow**: Professional websites with custom code
- **Retool**: Complex internal tools and dashboards
- **Bubble**: Advanced workflows and integrations

### For Specific Use Cases
- **E-commerce**: Shopify, Webflow
- **Mobile Apps**: Glide, Adalo
- **Websites**: Webflow, Framer
- **Internal Tools**: Retool, Bubble

## Next Steps

1. Review the detailed platform guides
2. Try the platform's free tier or trial
3. Start with a simple project to test the waters
4. Join the platform's community for support

---

*Still unsure? Start with our [getting started guide](getting_started.md) for more guidance.*
"""

        return content
