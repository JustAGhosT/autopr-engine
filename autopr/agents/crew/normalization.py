"""Normalization helpers for crew analysis results."""
from typing import Any

from autopr.agents.models import CodeIssue, PlatformAnalysis


def normalize_code_quality_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        if "metrics" not in result:
            # Provide default metrics and surface that this was a degraded path
            return {"metrics": {"score": 85}, "issues": result.get("issues", []), "error": "code_quality_task_missing_metrics"}
        return result
    return {"metrics": {"score": 85}, "issues": [], "error": "code_quality_unexpected_type"}


def normalize_platform_result(result: Any) -> PlatformAnalysis | None:
    if isinstance(result, PlatformAnalysis):
        return result
    # Accept dicts with platform-like keys
    if isinstance(result, dict):
        try:
            return PlatformAnalysis(
                platform=str(result.get("platform", "unknown")),
                confidence=float(result.get("confidence", 0.0)),
                components=list(result.get("components", [])),
                recommendations=list(result.get("recommendations", [])),
            )
        except Exception:
            return PlatformAnalysis(
                platform=str(result.get("platform", "unknown")),
                confidence=0.0,
                components=[],
                recommendations=[],
            )
    # Accept objects with a 'platform' attribute and coerce into PlatformAnalysis
    try:
        platform_attr = getattr(result, "platform", None)
        if platform_attr is not None:
            return PlatformAnalysis(
                platform=str(platform_attr),
                confidence=float(getattr(result, "confidence", 0.0)),
                components=list(getattr(result, "components", [])),
                recommendations=list(getattr(result, "recommendations", [])),
            )
    except Exception:
        return None
    return None


def _coerce_lint_list(items: list[Any]) -> list[CodeIssue]:
    coerced: list[CodeIssue] = []
    for item in items:
        if isinstance(item, CodeIssue):
            coerced.append(item)
            continue
        if isinstance(item, dict):
            try:
                data = dict(item)
                if "file" in data and "file_path" not in data:
                    data["file_path"] = data.pop("file")
                if "issue" in data and "message" not in data:
                    data["message"] = data.pop("issue")
                data.setdefault("line_number", data.pop("line", 1))
                data.setdefault("column", data.pop("column_number", 0))
                data.setdefault("severity", data.get("severity", "low"))
                data.setdefault("rule_id", data.get("rule_id", "auto"))
                data.setdefault("category", data.get("category", "style"))
                coerced.append(CodeIssue(**data))
            except Exception:
                continue
    return coerced


def normalize_linting_result(result: Any) -> list[CodeIssue]:
    if isinstance(result, list):
        return _coerce_lint_list(result)
    if isinstance(result, dict):
        try:
            return [
                CodeIssue(
                    file_path=result.get("file_path", "unknown"),
                    line_number=int(result.get("line_number", 1)),
                    column=int(result.get("column", 0)),
                    message=str(result.get("message", "linting issue")),
                    severity=str(result.get("severity", "low")),
                    rule_id=str(result.get("rule_id", "auto")),
                    category=str(result.get("category", "style")),
                )
            ]
        except Exception:
            return _coerce_lint_list([
                {"file_path": "unknown", "line_number": 1, "column": 0, "message": "linting issue", "severity": "low", "rule_id": "auto", "category": "style"}
            ])
    return []
