#!/usr/bin/env python3
"""
Test script to verify Quality Engine auto-fix integration.
"""

import asyncio
import sys
from pathlib import Path
from autopr.actions.quality_engine.engine import QualityEngine
from autopr.actions.quality_engine.models import QualityInputs, QualityMode

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))


async def test_auto_fix_integration():
    """Test the auto-fix integration."""
    print("🧪 Testing Quality Engine Auto-Fix Integration")

    # Create Quality Engine
    engine = QualityEngine(skip_windows_check=True)

    # Test inputs with auto-fix enabled
    inputs = QualityInputs(
        mode=QualityMode.FAST,
        files=["."],
        auto_fix=True,
        fix_types=["E501", "F401"],
        max_fixes=5,
        dry_run=True,
        enable_ai_agents=True,
    )

    print(f"✅ Quality Engine created")
    print(f"✅ Inputs configured: auto_fix={inputs.auto_fix}, fix_types={inputs.fix_types}")

    try:
        # Run the engine
        print("🔄 Running Quality Engine with auto-fix...")
        result = await engine.run(inputs)

        print(f"✅ Quality Engine completed successfully")
        print(f"📊 Results:")
        print(f"   - Success: {result.success}")
        print(f"   - Issues found: {result.total_issues_found}")
        print(f"   - Issues fixed: {result.total_issues_fixed}")
        print(f"   - Auto-fix applied: {result.auto_fix_applied}")
        print(f"   - Files modified: {len(result.files_modified)}")
        print(f"   - Fix summary: {result.fix_summary}")

        if result.fix_errors:
            print(f"❌ Fix errors: {result.fix_errors}")

        return True
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_auto_fix_integration())
    sys.exit(0 if success else 1)
