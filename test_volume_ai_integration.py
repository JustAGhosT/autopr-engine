#!/usr/bin/env python3
"""
Test script to demonstrate AI fixer integration with volume control system
"""

from autopr.actions.ai_linting_fixer.specialists import SpecialistManager
from autopr.utils.volume_utils import _get_ai_fixer_issue_types, get_volume_config


def test_volume_ai_integration():
    """Test the integration between volume control and AI fixer."""

    print("🔧 Testing Volume Control + AI Fixer Integration")
    print("=" * 60)

    # Test different volume levels
    test_volumes = [100, 300, 500, 700, 900]

    for volume in test_volumes:
        print(f"\n📊 Volume Level: {volume}")
        print("-" * 40)

        # Get volume configuration
        config = get_volume_config(volume)

        print(f"Quality Mode: {config.get('mode', 'Unknown')}")
        print(f"AI Agents Enabled: {config.get('enable_ai_agents', False)}")
        print(f"AI Fixer Enabled: {config.get('ai_fixer_enabled', False)}")
        print(f"Max Fixes: {config.get('ai_fixer_max_fixes', 0)}")

        # Get AI fixer issue types
        issue_types = _get_ai_fixer_issue_types(volume)
        print(f"AI Fixer Issue Types: {issue_types}")

        # Show specialist coverage
        specialist_manager = SpecialistManager()
        covered_codes = set()
        for specialist in specialist_manager.get_all_specialists().values():
            if "*" in specialist.supported_codes:
                covered_codes.update(issue_types)
            else:
                covered_codes.update(set(specialist.supported_codes) & set(issue_types))

        print(f"Covered Issue Types: {sorted(list(covered_codes))}")
        print(
            f"Coverage: {len(covered_codes)}/{len(issue_types)} ({len(covered_codes) / len(issue_types) * 100:.1f}%)"
        )

    # Test specialist selection for different issue types
    print("\n🎯 Specialist Selection Examples")
    print("-" * 40)

    specialist_manager = SpecialistManager()

    # Test cases with different issue combinations
    test_cases = [
        {
            "name": "Low Volume (100) - Basic Issues",
            "volume": 100,
            "issues": ["F401", "F841"],  # Unused imports and variables
        },
        {
            "name": "Medium Volume (500) - Style Issues",
            "volume": 500,
            "issues": ["E501", "G004", "F541"],  # Line length, logging, f-strings
        },
        {
            "name": "High Volume (700) - Complex Issues",
            "volume": 700,
            "issues": [
                "E722",
                "B001",
                "F821",
                "TRY401",
            ],  # Exceptions, undefined names, verbose logging
        },
        {
            "name": "Maximum Volume (900) - All Issues",
            "volume": 900,
            "issues": ["*"],  # All issues
        },
    ]

    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}")
        print("-" * 30)

        volume = test_case["volume"]
        issue_types = test_case["issues"]

        # Get volume configuration
        config = get_volume_config(volume)
        ai_fixer_enabled = config.get("ai_fixer_enabled", False)

        print(f"Volume: {volume}")
        print(f"AI Fixer Enabled: {ai_fixer_enabled}")
        print(f"Target Issue Types: {issue_types}")

        if ai_fixer_enabled:
            # Show which specialists would handle these issues
            for specialist in specialist_manager.get_all_specialists().values():
                if specialist.can_handle_issues_from_codes(issue_types):
                    print(f"  → {specialist.name} (expertise: {specialist.expertise_level})")
        else:
            print("  → AI Fixer disabled at this volume level")


def test_specialist_coverage():
    """Test specialist coverage of different issue types."""

    print("\n🔍 Specialist Coverage Analysis")
    print("-" * 40)

    specialist_manager = SpecialistManager()

    # Get all supported codes
    all_codes = specialist_manager.list_supported_codes()
    all_codes = [code for code in all_codes if code != "*"]  # Remove wildcard

    print(f"Total Supported Codes: {len(all_codes)}")
    print(f"Codes: {', '.join(all_codes)}")

    # Show coverage by specialist
    print("\n📊 Coverage by Specialist:")
    for name, specialist in specialist_manager.get_all_specialists().items():
        if "*" in specialist.supported_codes:
            print(f"  {name}: ALL codes (wildcard)")
        else:
            print(f"  {name}: {len(specialist.supported_codes)} codes")
            print(f"    {', '.join(specialist.supported_codes)}")


if __name__ == "__main__":
    test_volume_ai_integration()
    test_specialist_coverage()
