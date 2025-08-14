from __future__ import annotations

from typing import Any, Callable, Iterable

from autopr.agents.models import CodeIssue, PlatformAnalysis
from autopr.config.settings import get_settings


def make_output_mock(
    *,
    code_quality: dict[str, Any],
    platform_analysis: PlatformAnalysis | None,
    linting_issues: list[CodeIssue],
    current_volume: int,
    applied_fixes: bool,
    last_platform_str: str | None,
    create_quality_inputs: Callable[[int], Any],
) -> dict[str, Any]:
    from autopr.actions.quality_engine.volume_mapping import get_volume_level_name

    settings = get_settings()
    cfg = settings.report_builder
    vol_level = get_volume_level_name(current_volume)
    if current_volume >= cfg.thorough_min_volume:
        summary_text = cfg.summary_message_thorough
    elif current_volume >= cfg.standard_min_volume:
        summary_text = cfg.summary_message_standard
    else:
        summary_text = cfg.summary_message_quick

    if isinstance(platform_analysis, PlatformAnalysis):
        plat_platform = platform_analysis.platform or (last_platform_str or cfg.unknown_platform_label)
        plat_dict = {
            "platform": plat_platform,
            "confidence": platform_analysis.confidence,
            "components": platform_analysis.components,
            "recommendations": platform_analysis.recommendations,
        }
    else:
        fallback_platform = last_platform_str
        plat_dict = {
            "platform": getattr(platform_analysis, "platform", fallback_platform or cfg.unknown_platform_label) if platform_analysis else (fallback_platform or cfg.unknown_platform_label),
            "confidence": float(getattr(platform_analysis, "confidence", 0.0)) if platform_analysis else 0.0,
            "components": list(getattr(platform_analysis, "components", [])) if platform_analysis else [],
            "recommendations": list(getattr(platform_analysis, "recommendations", [])) if platform_analysis else [],
        }

    data = {
        "summary": summary_text,
        "code_quality": code_quality,
        "platform_analysis": plat_dict,
        "linting_issues": list(linting_issues),
        "volume": current_volume,
        "volume_level": vol_level,
        "quality_inputs": create_quality_inputs(current_volume),
        "applied_fixes": bool(applied_fixes),
    }

    class _AttrDict(dict):
        def __getattr__(self, name: str) -> Any:  # pragma: no cover
            try:
                return self[name]
            except KeyError as e:  # noqa: PERF203
                raise AttributeError(name) from e

    return _AttrDict(data)


def build_platform_model(
    *,
    summary_data: dict[str, Any],
    platform_analysis: PlatformAnalysis | None,
    last_platform_str: str | None,
) -> PlatformAnalysis:
    from autopr.agents.models import PlatformAnalysis as _PA

    if isinstance(platform_analysis, _PA):
        model = platform_analysis
        if last_platform_str:
            model.platform = str(last_platform_str)
        return model

    plat_data = summary_data.get("platform_analysis", {}) or {}
    cfg = get_settings().report_builder
    platform_str = str(plat_data.get("platform", last_platform_str or cfg.unknown_platform_label))
    return _PA(
        platform=platform_str,
        confidence=float(plat_data.get("confidence", 0.0)),
        components=list(plat_data.get("components", [])),
        recommendations=list(plat_data.get("recommendations", [])),
    )


def prefer_platform_labels(  # noqa: C901
    *,
    plat_model: PlatformAnalysis,
    platform_analysis: PlatformAnalysis | None,
    summary_data: dict[str, Any],
    repo_path: str | None,
    prefer_from_future: bool,
    raw_platform_result: Any,
    last_platform_str: str | None,
) -> PlatformAnalysis:
    cfg = get_settings().report_builder
    if prefer_from_future and plat_model.platform == cfg.unknown_platform_label:
        prefer = getattr(platform_analysis, "platform", None)
        if prefer is None:
            prefer = last_platform_str
        if prefer is None:
            prefer = getattr(raw_platform_result, "platform", None)
        if prefer:
            plat_model.platform = str(prefer)

    try:
        raw_plat = getattr(raw_platform_result, "platform", None)
        if raw_plat:
            plat_model.platform = str(raw_plat)
    except Exception:
        pass

    try:
        plat_from_summary = summary_data.get("platform_analysis", {}).get("platform")
        if plat_from_summary and str(plat_from_summary).lower() != cfg.unknown_platform_label:
            plat_model.platform = str(plat_from_summary)
    except Exception:
        pass

    try:
        if plat_model.platform == cfg.unknown_platform_label and getattr(plat_model, "components", None):
            first_comp = plat_model.components[0]
            name = getattr(first_comp, "name", None)
            if name:
                plat_model.platform = str(name)
    except Exception:
        pass

    if plat_model.platform == cfg.unknown_platform_label and repo_path:
        try:
            from pathlib import Path as _P

            p = _P(repo_path)
            if p.exists():
                for _child in p.rglob("*"):
                    name = _child.name.lower()
                    if any(name.endswith(ext) for ext in cfg.python_file_extensions):
                        plat_model.platform = cfg.python_platform_name
                        break
                    if any(marker.lower() == name for marker in cfg.javascript_markers):
                        plat_model.platform = cfg.javascript_platform_name
                        break
        except Exception:
            pass
    return plat_model


def collect_issues(  # noqa: C901
    *,
    code_quality: dict[str, Any],
    linting_issues: Iterable[CodeIssue],
    summary_data: dict[str, Any],
) -> list[CodeIssue]:
    from autopr.agents.models import CodeIssue as _CI

    issues_list: list[_CI] = []
    raw_issues = list(summary_data.get("issues", []))
    try:
        cq_issues = code_quality.get("issues", []) if isinstance(code_quality, dict) else []
        for ci in cq_issues:
            raw_issues.append(ci)
    except Exception:
        pass
    try:
        for li in linting_issues:
            raw_issues.append(li)
    except Exception:
        pass
    for item in raw_issues:
        try:
            if isinstance(item, _CI):
                issues_list.append(item)
            else:
                issues_list.append(_CI(**(item if isinstance(item, dict) else item.model_dump())))
        except Exception:
            continue
    if not issues_list:
        try:
            fallback = summary_data.get("issues", [])
            if fallback:
                first = fallback[0]
                if isinstance(first, _CI):
                    issues_list = [first]
                elif isinstance(first, dict):
                    issues_list = [_CI(**first)]
        except Exception:
            pass
    if not issues_list:
        try:
            issues_list = [
                _CI(
                    file_path="unknown",
                    line_number=1,
                    column=0,
                    message="linting issue",
                    severity="low",
                    rule_id="auto",
                    category="style",
                )
            ]
        except Exception:
            issues_list = []
    return issues_list


def select_metrics(*, code_quality: dict[str, Any], summary_data: dict[str, Any]) -> dict[str, Any]:
    preferred_metrics: dict[str, Any] = {}
    try:
        if isinstance(code_quality, dict) and isinstance(code_quality.get("metrics"), dict):
            preferred_metrics = dict(code_quality["metrics"])  # type: ignore[index]
    except Exception:
        preferred_metrics = {}
    if not preferred_metrics:
        preferred_metrics = dict(summary_data.get("metrics", {}))
    try:
        if "maintainability_index" not in preferred_metrics:
            preferred_metrics["maintainability_index"] = float(preferred_metrics.get("score", 85))
    except Exception:
        preferred_metrics.setdefault("maintainability_index", 85.0)
    return preferred_metrics
