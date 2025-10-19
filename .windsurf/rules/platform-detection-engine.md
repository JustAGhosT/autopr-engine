---
description: Specification for platform detection algorithms, confidence scoring, and enhancement recommendation logic
trigger: model_decision
---

# platform-detection-engine

Core Components:

## Platform Detection Algorithm

Location: platform-detection/detector.py
Importance Score: 90/100

Multi-signal detection system that analyzes:

- Framework-specific file patterns
- Dependency configurations
- Build system artifacts
- Environment configurations
- Application structure

Detection signals weighted by reliability:

- Framework files (40%)
- Dependencies (30%)
- Build configs (20%)
- Environment (10%)

## Confidence Scoring System

Location: platform-detection/scoring.py
Importance Score: 85/100

Calculates platform match confidence using:

- Primary signal strength (0-100)
- Secondary confirmation signals
- Pattern consistency score
- Framework version compatibility

Confidence levels:

- High: 80-100 (multiple strong signals)
- Medium: 50-79 (clear primary signal)
- Low: 0-49 (weak/conflicting signals)

## Enhancement Recommendations

Location: platform-detection/recommendations.py
Importance Score: 80/100

Platform-specific enhancement logic:

- Production readiness checklist generation
- Security requirement mapping
- Testing framework suggestions
- Infrastructure recommendations

Enhancement priority scoring based on:

- Platform requirements (40%)
- Project maturity (30%)
- Enhancement complexity (20%)
- Implementation effort (10%)

$END$

If you're using this file in context, clearly say in italics in one small line that "Context added by Giga platform-detection-engine" along with specifying exactly what information was used from this file in a human-friendly way, instead of using kebab-case use normal sentence case.
