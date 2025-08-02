#!/usr/bin/env python3
"""
Test script for the AutoPR template system with provider support.
"""

import logging
import os
from pathlib import Path
import sys
from typing import Any

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_jinja2_provider():
    """Test the Jinja2 template provider."""
    try:
        from autopr.templates import Jinja2TemplateProvider, TemplateSystem

        # Initialize the template system with Jinja2 provider
        template_dirs = [
            project_root / "autopr" / "templates" / "examples",  # Example templates
        ]

        logger.info("Initializing Jinja2 template provider...")
        jinja2_provider = Jinja2TemplateProvider(template_dirs=template_dirs)

        # Initialize template system with just Jinja2 provider
        template_system = TemplateSystem(template_dirs)

        # Clear default providers and add only Jinja2
        for provider_name in list(template_system.providers.keys()):
            template_system.remove_provider(provider_name)
        template_system.add_provider("jinja2", jinja2_provider)

        # Run common tests
        run_common_tests(template_system, "Jinja2")

        return True

    except Exception as e:
        logger.error(f"Error testing Jinja2 provider: {e}", exc_info=True)
        return False


def test_autoweave_provider():
    """Test the AutoWeave template provider if API key is available."""
    autoweave_api_key = os.environ.get("AUTOWEAVE_API_KEY")
    if not autoweave_api_key:
        logger.warning("Skipping AutoWeave provider test - AUTOWEAVE_API_KEY not set")
        return True  # Skip test, not an error

    try:
        from autopr.templates import AutoWeaveProvider, TemplateSystem

        logger.info("Initializing AutoWeave template provider...")
        autoweave_provider = AutoWeaveProvider(api_key=autoweave_api_key)

        # Initialize template system with AutoWeave provider
        template_system = TemplateSystem()

        # Clear default providers and add only AutoWeave
        for provider_name in list(template_system.providers.keys()):
            template_system.remove_provider(provider_name)
        template_system.add_provider("autoweave", autoweave_provider)

        # Run common tests
        run_common_tests(template_system, "AutoWeave")

        return True

    except Exception as e:
        logger.error(f"Error testing AutoWeave provider: {e}", exc_info=True)
        return False


def test_provider_fallback():
    """Test provider fallback mechanism."""
    try:
        from autopr.templates import AutoWeaveProvider, Jinja2TemplateProvider, TemplateSystem

        # Initialize providers
        template_dirs = [project_root / "autopr" / "templates" / "examples"]
        jinja2_provider = Jinja2TemplateProvider(template_dirs=template_dirs)

        # Create a failing AutoWeave provider
        class FailingAutoWeaveProvider(AutoWeaveProvider):
            def get_template(self, template_id: str) -> Any | None:
                msg = "Simulated AutoWeave API failure"
                raise Exception(msg)

        failing_autoweave = FailingAutoWeaveProvider(api_key="dummy_key")

        # Initialize template system with both providers
        template_system = TemplateSystem(template_dirs)

        # Clear default providers and add our test providers
        for provider_name in list(template_system.providers.keys()):
            template_system.remove_provider(provider_name)

        template_system.add_provider("autoweave", failing_autoweave)
        template_system.add_provider("jinja2", jinja2_provider)

        # Set AutoWeave as default (should fall back to Jinja2)
        template_system.default_provider = "autoweave"

        # This should work because it falls back to Jinja2
        templates = template_system.get_all_templates()
        assert templates, "Expected to get templates from fallback provider"
        logger.info("Successfully tested provider fallback mechanism")

        return True

    except Exception as e:
        logger.error(f"Error testing provider fallback: {e}", exc_info=True)
        return False


def run_common_tests(template_system, provider_name: str):
    """Run common tests against a template system instance."""
    logger.info(f"\n=== Testing {provider_name} Provider ===")

    # Test template discovery
    logger.info("\n--- Available Templates ---")
    templates = template_system.get_all_templates()
    for template in templates:
        logger.info(f"- {template.template_id} ({template.title})")

    if not templates:
        logger.warning("No templates found!")
        return False

    # Use the first template for testing
    template_id = templates[0].template_id
    logger.info(f"\n--- Testing template: {template_id} ---")

    # Get template metadata
    template = template_system.get_template(template_id)
    if template:
        logger.info(f"Title: {template.title}")
        logger.info(f"Description: {template.description}")
        logger.info(f"Version: {template.version}")
        logger.info(f"Author: {template.author}")
        logger.info(f"Tags: {', '.join(template.tags) if template.tags else 'None'}")

    # Test basic rendering
    logger.info("\n--- Basic Rendering ---")
    context = {
        "name": "Developer",
        "project_name": f"Test Project ({provider_name})",
        "description": f"A test project for {provider_name} provider",
        "features": ["Feature A", "Feature B", "Feature C"],
        "greeting": f"Thank you for using {provider_name}!",
    }

    # Add variables based on template requirements
    if template and hasattr(template, "variables"):
        for var_name, var_meta in template.variables.items():
            if var_name not in context and "default" in var_meta:
                context[var_name] = var_meta["default"]

    try:
        result = template_system.render_template(template_id, context)
        logger.info(f"\nRendered template:\n{'-' * 40}\n{result}\n{'-' * 40}")
    except Exception as e:
        logger.error(f"Error rendering template: {e}", exc_info=True)
        return False

    # Test rendering to file
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{template_id}_{provider_name.lower()}.txt"

    logger.info(f"\n--- Rendering to file: {output_file} ---")
    try:
        template_system.render_to_file(template_id, output_file, context)
        logger.info(f"Template rendered to {output_file.absolute()}")
    except Exception as e:
        logger.error(f"Error rendering to file: {e}", exc_info=True)
        return False

    # Test searching for templates
    logger.info("\n--- Searching Templates ---")
    search_terms = ["hello", "test", "template"]
    for term in search_terms:
        try:
            results = template_system.search_templates(term)
            logger.info(f"Search for '{term}': {len(results)} results")
            for result in results[:3]:  # Show first 3 results
                logger.info(f"  - {result.template_id} ({result.title})")
        except Exception as e:
            logger.exception(f"Error searching for '{term}': {e}")
            return False

    logger.info("\n✅ All common tests completed successfully!")
    return True


def test_template_rendering():
    """Run all template system tests."""
    results = {
        "Jinja2 Provider": test_jinja2_provider(),
        "AutoWeave Provider": test_autoweave_provider(),
        "Provider Fallback": test_provider_fallback(),
    }

    # Print summary
    logger.info("\n=== Test Summary ===")
    all_passed = True
    for test_name, passed in results.items():
        status = "PASSED" if passed else "SKIPPED" if passed is None else "FAILED"
        if not passed and passed is not None:
            all_passed = False
        logger.info(f"{test_name}: {status}")

    return all_passed


if __name__ == "__main__":
    success = test_template_rendering()
    sys.exit(0 if success else 1)
