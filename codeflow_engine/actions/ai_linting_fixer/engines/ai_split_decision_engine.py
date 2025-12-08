"""
AI Split Decision Engine for AI Linting Fixer

AI-powered decision engine for file splitting decisions.
"""

import hashlib
import logging
from typing import Any

from codeflow_engine.actions.ai_linting_fixer.performance_optimizer import \
    IntelligentCache
from codeflow_engine.ai.core.providers.manager import LLMProviderManager

logger = logging.getLogger(__name__)


class AISplitDecisionEngine:
    """AI-powered decision engine for file splitting."""

    def __init__(
        self,
        llm_manager: LLMProviderManager,
        cache_manager: IntelligentCache | None = None,
    ):
        self.llm_manager = llm_manager
        self.cache_manager = cache_manager or IntelligentCache(
            max_size_mb=50, default_ttl_seconds=3600
        )

    async def should_split_file(
        self, file_path: str, content: str, complexity: dict[str, Any]
    ) -> tuple[bool, float, str]:
        """Determine if a file should be split using AI analysis."""
        # Create stable, collision-resistant cache key using SHA-256
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        cache_key = f"split_decision:{file_path}:{content_hash}:{len(content)}"

        # Try cache first
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            logger.debug("Cache hit for split decision: %s", file_path)
            logger.info("Using cached decision: %s", cached_result['reason'])
            return (
                cached_result["should_split"],
                cached_result["confidence"],
                cached_result["reason"],
            )

        # AI analysis
        try:
            logger.debug("Performing AI analysis for split decision...")
            prompt = self._create_split_decision_prompt(content, complexity)
            # Use the LLM manager's complete method
            request = {
                "provider": "openai",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert code analyzer. Determine if a file should be "
                            "split based on complexity, maintainability, and best practices."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            }
            response = await self.llm_manager.complete(
                messages=request["messages"],
                provider=request["provider"],
                temperature=request["temperature"],
            )

            if response and response.content:
                logger.debug("AI response received: %s...", response.content[:100])

                # Enhanced rule-based decision with detailed reasoning
                should_split = False
                confidence = 0.5
                reasons = []

                # Check various criteria with safe access
                total_lines = int(complexity.get("total_lines", 0))
                if total_lines > 200:
                    should_split = True
                    confidence += 0.2
                    reasons.append(f"Large file ({total_lines} lines)")

                complexity_score = float(complexity.get("complexity_score", 0.0))
                if complexity_score > 8.0:
                    should_split = True
                    confidence += 0.3
                    reasons.append(f"High complexity score ({complexity_score:.2f})")

                total_functions = int(complexity.get("total_functions", 0))
                if total_functions > 15:
                    should_split = True
                    confidence += 0.2
                    reasons.append(f"Many functions ({total_functions})")

                total_classes = int(complexity.get("total_classes", 0))
                if total_classes > 3:
                    should_split = True
                    confidence += 0.2
                    reasons.append(f"Multiple classes ({total_classes})")

                # Cap confidence at 0.95
                confidence = min(confidence, 0.95)

                reason = "; ".join(reasons) if reasons else "Within acceptable limits"

                if not should_split:
                    reason = "File is well-structured and within acceptable size/complexity limits"

                result = {
                    "should_split": should_split,
                    "confidence": confidence,
                    "reason": reason,
                }

                # Cache result
                self.cache_manager.set(cache_key, result, ttl_seconds=3600)
                logger.info(
                    "AI analysis complete: %s (confidence: %.2f)", reason, confidence
                )

                return should_split, confidence, reason

        except Exception as e:
            logger.warning("AI split decision failed: %s", e)

        # Fallback to rule-based decision with safe access
        logger.info("Using fallback rule-based decision")
        total_lines = int(complexity.get("total_lines", 0))
        complexity_score = float(complexity.get("complexity_score", 0.0))

        should_split = (total_lines > 150 or complexity_score > 7.0)
        fallback_reason = "Rule-based fallback: "
        if total_lines > 150:
            fallback_reason += f"Large file ({total_lines} lines)"
        elif complexity_score > 7.0:
            fallback_reason += f"High complexity ({complexity_score:.2f})"
        else:
            fallback_reason += "No specific criteria met"

        return should_split, 0.7, fallback_reason

    def _create_split_decision_prompt(
        self, content: str, complexity: dict[str, Any]
    ) -> str:
        """Create prompt for AI split decision."""
        return f"""
Analyze this code file and determine if it should be split:

File Statistics:
- Lines: {complexity['total_lines']}
- Functions: {complexity['total_functions']}
- Classes: {complexity['total_classes']}
- Complexity Score: {complexity['complexity_score']:.2f}

Code Preview:
{content[:1000]}...

Should this file be split? Consider:
1. Maintainability
2. Single Responsibility Principle
3. Code organization
4. Team collaboration

Respond with: YES/NO and brief reasoning.
"""
