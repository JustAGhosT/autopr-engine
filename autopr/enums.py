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
    def from_volume(cls, volume: int) -> 'QualityMode':
        """
        Map a volume level (0-1000) to a QualityMode.
        
        Args:
            volume: Volume level from 0 to 1000
            
        Returns:
            QualityMode: The appropriate quality mode for the given volume
        """
        if not 0 <= volume <= 1000:
            raise ValueError(f"Volume must be between 0 and 1000, got {volume}")
            
        if volume < 100:
            return cls.ULTRA_FAST
        elif volume < 300:
            return cls.FAST
        elif volume < 700:
            return cls.SMART
        elif volume < 900:
            return cls.COMPREHENSIVE
        else:
            return cls.AI_ENHANCED
