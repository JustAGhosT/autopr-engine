from enum import Enum


class QualityMode(str, Enum):
    """
    Defines the quality analysis modes for the AutoPR system.

    The modes control the depth and thoroughness of quality analysis,
    with higher modes performing more comprehensive but potentially slower analysis.
    """

    ULTRA_FAST = "ultra-fast"
    FAST = "fast"
    COMPREHENSIVE = "comprehensive"
    AI_ENHANCED = "ai_enhanced"
    SMART = "smart"

    @classmethod
    def from_volume(cls, volume: int) -> "QualityMode":
        """
        Map a volume level (0-1000) to a QualityMode.

        Args:
            volume: Volume level from 0 to 1000

        Returns:
            QualityMode: The appropriate quality mode for the given volume
        """
        if not 0 <= volume <= 1000:
            msg = f"Volume must be between 0 and 1000, got {volume}"
            raise ValueError(msg)

        # Import here to avoid circular dependency
        from autopr.utils.volume_utils import VOLUME_THRESHOLDS

        # Use the centralized thresholds
        if volume < VOLUME_THRESHOLDS.ULTRA_FAST_MAX:
            return cls.ULTRA_FAST
        if volume < VOLUME_THRESHOLDS.FAST_MAX:
            return cls.FAST
        if volume < VOLUME_THRESHOLDS.SMART_MAX:
            return cls.SMART
        if volume < VOLUME_THRESHOLDS.COMPREHENSIVE_MAX:
            return cls.COMPREHENSIVE
        return cls.AI_ENHANCED
