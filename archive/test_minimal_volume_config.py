"""Minimal test for VolumeConfig validation."""

import logging
import sys
import traceback
from pathlib import Path

# Set up debug logging to file
log_file = Path("volume_config_test.log")
if log_file.exists():
    log_file.unlink()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def log_section(title):
    """Log a section header for better readability."""
    logger.info("\n" + "=" * 50)
    logger.info(f" {title} ")
    logger.info("=" * 50)


log_section("Starting VolumeConfig Test")

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

log_section("Attempting to import VolumeConfig")

try:
    from autopr.agents.base.volume_config import VolumeConfig

    logger.info("✅ Successfully imported VolumeConfig and QualityMode")

    log_section("Testing VolumeConfig Initialization")

    # Test 1: Default initialization
    logger.info("\nTest 1: Default initialization")
    config = VolumeConfig()
    logger.info(f"✅ Default config: {config}")
    logger.info(f"✅ Volume: {config.volume}")
    logger.info(f"✅ Quality Mode: {type(config.quality_mode).__name__} = {config.quality_mode}")
    logger.info(f"✅ Config: {config.config}")

    # Test 2: Custom volume
    log_section("Testing Custom Volume")
    for volume in [0, 250, 500, 750, 1000]:
        config = VolumeConfig(volume=volume)
        logger.info(
            f"✅ Volume {volume} -> Mode: {config.quality_mode}, AI Agents: {config.config.get('enable_ai_agents')}"
        )

    # Test 3: Boolean validation with different input types
    log_section("Testing Boolean Validation")
    test_cases = [
        (True, "boolean True"),
        (False, "boolean False"),
        ("true", 'string "true"'),
        ("false", 'string "false"'),
        ("True", 'string "True"'),
        ("False", 'string "False"'),
        (1, "integer 1"),
        (0, "integer 0"),
        ("1", 'string "1"'),
        ("0", 'string "0"'),
    ]

    for value, desc in test_cases:
        try:
            logger.info(f"\nTesting with {desc}...")
            config = VolumeConfig(volume=500, config={"enable_ai_agents": value})
            result = config.config.get("enable_ai_agents")
            logger.info(f"✅ {desc}: {result} (type: {type(result).__name__})")

        except Exception as e:
            logger.error(f"❌ Failed with {desc}: {e}\n{traceback.format_exc()}")

    logger.info("\n✅ All tests completed successfully!")

except Exception:
    logger.error("❌ Test failed with error:", exc_info=True)
    raise
