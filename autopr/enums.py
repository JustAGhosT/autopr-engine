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
        MAX_VOLUME = 1000
        MIN_VOLUME = 0
        if not MIN_VOLUME <= volume <= MAX_VOLUME:
            msg = f"Volume must be between {MIN_VOLUME} and {MAX_VOLUME}, got {volume}"
            raise ValueError(msg)

        # Thresholds aligned with tests:
        # 0 -> ULTRA_FAST
        # 100-299 -> FAST
        # 300-599 -> SMART
        # 600-799 -> COMPREHENSIVE
        # 800-1000 -> AI_ENHANCED
        THRESH_FAST = 100
        THRESH_SMART = 300
        THRESH_COMPREHENSIVE = 600
        THRESH_AI = 800
        if volume < THRESH_FAST:
            return cls.ULTRA_FAST
        if volume < THRESH_SMART:
            return cls.FAST
        if volume < THRESH_COMPREHENSIVE:
            return cls.SMART
        if volume <= THRESH_AI:
            return cls.COMPREHENSIVE
        return cls.AI_ENHANCED
