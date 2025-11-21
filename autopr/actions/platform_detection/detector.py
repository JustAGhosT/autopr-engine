"""Platform detector core implementation.

This module provides the main platform detection logic used by AutoPR.

It combines:

- platform configuration data (:mod:`autopr.actions.platform_detection.config`)
- filesystem analysis (:mod:`autopr.actions.platform_detection.file_analyzer`)
- scoring and ranking (:mod:`autopr.actions.platform_detection.scoring`)

and exposes:

- a synchronous :meth:`PlatformDetector.detect_platform` API that works with
  :class:`PlatformDetectorInputs`
- an asynchronous :meth:`PlatformDetector.analyze` API used by
  :class:`autopr.agents.platform_analysis_agent.PlatformAnalysisAgent`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel

from .config import PlatformConfigManager
from .file_analyzer import FileAnalyzer
from .models import PlatformDetectorInputs
from .patterns import PlatformPatterns
from .scoring import PlatformScoringEngine


class PlatformDetectorOutputs(BaseModel):
    """Rich analysis output for platform detection.

    This is the analysis-level result used by higher-level components such as
    :class:`PlatformAnalysisAgent`. It intentionally differs from the simpler
    models in :mod:`autopr.actions.platform_detection.models`.
    """

    primary_platform: str
    secondary_platforms: list[str]
    confidence_scores: dict[str, float]
    workflow_type: str
    platform_specific_configs: dict[str, dict[str, Any]]
    recommended_enhancements: list[str]
    migration_opportunities: list[str]
    hybrid_workflow_analysis: dict[str, Any] | None


class PlatformDetector:
    """Detect which rapid prototyping platforms are used in a workspace.

    The detector orchestrates file analysis, configuration loading and scoring
    to produce a ranked set of platforms and workflow recommendations.
    """

    def __init__(self) -> None:
        self.platform_patterns = PlatformPatterns.get_platform_signatures()
        self.advanced_patterns = PlatformPatterns.get_advanced_patterns()
        self.config_manager = PlatformConfigManager()
        self.scoring_engine = PlatformScoringEngine()

    def detect_platform(self, inputs: PlatformDetectorInputs) -> PlatformDetectorOutputs:
        """Run platform detection using the provided inputs.

        This is the synchronous entry point used by lower-level callers.
        Higher-level async callers should use :meth:`analyze` instead.
        """

        try:
            workspace_path = inputs.workspace_path or "."
            workspace = Path(workspace_path)

            # Defensive guard – if the workspace does not exist, return unknown
            if not workspace.exists():
                return PlatformDetectorOutputs(
                    primary_platform="unknown",
                    secondary_platforms=[],
                    confidence_scores={"unknown": 1.0},
                    workflow_type="unknown",
                    platform_specific_configs={},
                    recommended_enhancements=[],
                    migration_opportunities=[],
                    hybrid_workflow_analysis=None,
                )

            # 1) Load platform configs that have detection rules
            platform_configs = (
                self.config_manager.get_platforms_with_detection_rules() or {}
            )

            if not platform_configs:
                return PlatformDetectorOutputs(
                    primary_platform="unknown",
                    secondary_platforms=[],
                    confidence_scores={"unknown": 1.0},
                    workflow_type="unknown",
                    platform_specific_configs={},
                    recommended_enhancements=[],
                    migration_opportunities=[],
                    hybrid_workflow_analysis=None,
                )

            # 2) Analyze the workspace
            analyzer = FileAnalyzer(workspace_path)

            # File and folder indicators
            legacy_indicators = analyzer.scan_for_platform_indicators(platform_configs)
            found_files: dict[str, list[str]] = {}
            found_folders: dict[str, list[str]] = {}
            for platform, data in legacy_indicators.items():
                files = data.get("files", [])
                folders = data.get("folders", [])
                if files:
                    found_files[platform] = files
                if folders:
                    found_folders[platform] = folders

            # Content matches (counts) – convert to repeated markers
            content_match_counts = analyzer.scan_content_for_patterns(platform_configs)
            content_matches: dict[str, list[str]] = {}
            for platform, count in content_match_counts.items():
                if count > 0:
                    content_matches[platform] = ["match"] * count

            # Package metadata
            package_info = analyzer.analyze_package_json()
            dependencies = list(package_info.get("dependencies", {}).keys()) + list(
                package_info.get("devDependencies", {}).keys()
            )
            scripts = package_info.get("scripts", {})

            # Commit message matches per platform based on detection rules
            commit_matches: dict[str, int] = {}
            commit_messages = inputs.commit_messages or []
            for platform_id, cfg in platform_configs.items():
                detection = cfg.get("detection", {}) or {}
                patterns = detection.get("commit_patterns", [])
                if not patterns:
                    continue
                count = 0
                for msg in commit_messages:
                    lower_msg = msg.lower()
                    if any(pat.lower() in lower_msg for pat in patterns):
                        count += 1
                if count:
                    commit_matches[platform_id] = count

            detection_results: dict[str, Any] = {
                "found_files": found_files,
                "found_folders": found_folders,
                "dependencies": dependencies,
                "scripts": scripts,
                "content_matches": content_matches,
                "commit_matches": commit_matches,
            }

            # 3) Adapt platform configs for the scoring engine
            scoring_configs: dict[str, dict[str, Any]] = {}
            for platform_id, cfg in platform_configs.items():
                detection = cfg.get("detection", {}) or {}
                scoring_configs[platform_id] = {
                    "dependencies": detection.get("dependencies", []),
                    "devDependencies": [],
                    "package_scripts": detection.get("package_scripts", []),
                }

            # 4) Calculate scores and derive workflow information
            scores = self.scoring_engine.calculate_platform_scores(
                scoring_configs, detection_results
            )

            # Ensure scores are in [0, 1]
            normalized_scores = {
                k: min(max(v, 0.0), 1.0) for k, v in (scores or {}).items()
            }

            if not normalized_scores:
                return PlatformDetectorOutputs(
                    primary_platform="unknown",
                    secondary_platforms=[],
                    confidence_scores={"unknown": 1.0},
                    workflow_type="unknown",
                    platform_specific_configs={},
                    recommended_enhancements=[],
                    migration_opportunities=[],
                    hybrid_workflow_analysis=None,
                )

            primary_platform, secondary_platforms = self.scoring_engine.rank_platforms(
                normalized_scores
            )

            # Enforce detection threshold of 0.5 per platform detection guidelines
            detection_threshold = 0.5
            primary_score = normalized_scores.get(primary_platform, 0.0)

            # Only treat platforms as "detected" if they meet the 0.5 threshold
            if primary_platform != "unknown" and primary_score < detection_threshold:
                primary_platform = "unknown"

            secondary_platforms = [
                p
                for p in secondary_platforms
                if normalized_scores.get(p, 0.0) >= detection_threshold
            ]

            workflow_type = self.scoring_engine.determine_workflow_type(
                normalized_scores
            )
            hybrid_workflow = self.scoring_engine.analyze_hybrid_workflow(
                normalized_scores, scoring_configs
            )

            recommended_enhancements = self.scoring_engine.generate_recommendations(
                primary_platform,
                secondary_platforms,
                normalized_scores,
                workflow_type,
            )
            migration_opportunities = (
                self.scoring_engine.identify_migration_opportunities(
                    normalized_scores, scoring_configs
                )
            )
            
            # Validate hybrid/multi-platform classifications
            reclassification_reasons = []
            
            if workflow_type in ("hybrid_workflow", "multi_platform"):
                # 1. Check for migration path analysis (mandatory for hybrid/multi-platform)
                if not migration_opportunities:
                    reclassification_reasons.append(
                        f"No migration opportunities identified for {workflow_type} classification"
                    )
                
                # 2. Check platform compatibility
                is_compatible, incompatibility_reasons = (
                    self.scoring_engine.check_platform_compatibility(
                        primary_platform, secondary_platforms
                    )
                )
                
                if not is_compatible:
                    reclassification_reasons.extend(
                        [f"Platform incompatibility: {reason}" for reason in incompatibility_reasons]
                    )
                
                # Reclassify if validation fails
                if reclassification_reasons:
                    import warnings
                    warning_msg = (
                        f"Reclassifying {workflow_type} to single_platform. "
                        f"Reasons: {'; '.join(reclassification_reasons)}"
                    )
                    warnings.warn(warning_msg, UserWarning)
                    
                    workflow_type = "single_platform"
                    # Keep only primary platform
                    secondary_platforms = []
                    
                    # Add analysis note to recommended enhancements
                    recommended_enhancements.insert(
                        0,
                        f"Note: Detected as {workflow_type} but reclassified due to: {reclassification_reasons[0]}"
                    )

            # 5) Platform-specific configs – for now we expose raw detection rules
            platform_specific_configs: dict[str, dict[str, Any]] = {}
            for platform_id, cfg in platform_configs.items():
                detection_cfg = cfg.get("detection", {}) or {}
                project_cfg = cfg.get("project_config", {}) or {}
                platform_specific_configs[platform_id] = {
                    "detection": detection_cfg,
                    "project_config": project_cfg,
                    "config_files": project_cfg.get("configuration_files", []),
                }

            return PlatformDetectorOutputs(
                primary_platform=primary_platform,
                secondary_platforms=secondary_platforms,
                confidence_scores=normalized_scores,
                workflow_type=workflow_type,
                platform_specific_configs=platform_specific_configs,
                recommended_enhancements=recommended_enhancements,
                migration_opportunities=migration_opportunities,
                hybrid_workflow_analysis=hybrid_workflow,
            )

        except Exception:
            # Defensive catch-all: never raise from detection, always return a safe result
            return PlatformDetectorOutputs(
                primary_platform="unknown",
                secondary_platforms=[],
                confidence_scores={"unknown": 1.0},
                workflow_type="unknown",
                platform_specific_configs={},
                recommended_enhancements=[],
                migration_opportunities=[],
                hybrid_workflow_analysis=None,
            )

    async def analyze(
        self,
        *,
        repo_path: str,
        file_paths: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> PlatformDetectorOutputs:
        """Asynchronous analysis API used by higher-level agents.

        Args:
            repo_path: Root path of the repository to analyze.
            file_paths: Optional list of specific files to focus on. Currently
                unused; the detector analyzes the whole workspace for
                robustness, but this parameter is accepted for future
                refinements.
            context: Optional context dictionary that may contain
                ``repository_url`` and ``commit_messages``.
        """

        _ = file_paths  # Currently unused – reserved for future refinement
        ctx = context or {}

        repository_url = ctx.get("repository_url", "")
        commit_messages = ctx.get("commit_messages", []) or []

        inputs = PlatformDetectorInputs(
            repository_url=repository_url,
            commit_messages=list(commit_messages),
            workspace_path=repo_path,
            package_json_content=None,
        )

        # The underlying logic is synchronous; wrapping in async keeps the
        # agent interface consistent without adding concurrency complexity here.
        return self.detect_platform(inputs)

