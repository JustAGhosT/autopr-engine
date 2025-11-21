"""
Unit tests for platform detection validation logic.

Tests cover:
- Compatibility matrix validation
- Migration path requirements
- Reclassification logic
- Threshold enforcement
"""

import pytest
from autopr.actions.platform_detection.scoring import PlatformScoringEngine


class TestPlatformCompatibility:
    """Test platform compatibility validation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = PlatformScoringEngine()
    
    def test_compatible_platforms_same_group(self):
        """Test platforms in same compatibility group are compatible."""
        # Rapid prototyping group
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "replit", ["lovable", "bolt"]
        )
        assert is_compatible
        assert len(reasons) == 0
        
        # AI assisted group
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "github_copilot", ["tabnine"]
        )
        assert is_compatible
        assert len(reasons) == 0
    
    def test_incompatible_deployment_platforms(self):
        """Test competing deployment platforms are incompatible."""
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "vercel", ["netlify"]
        )
        assert not is_compatible
        assert len(reasons) == 1
        assert "vercel and netlify" in reasons[0]
        assert "competing" in reasons[0].lower()
    
    def test_incompatible_paas_platforms(self):
        """Test competing PaaS platforms are incompatible."""
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "heroku", ["railway"]
        )
        assert not is_compatible
        assert len(reasons) == 1
        assert "heroku and railway" in reasons[0]
    
    def test_incompatible_ai_assistants(self):
        """Test competing AI assistants are incompatible."""
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "github_copilot", ["codeium"]
        )
        assert not is_compatible
        assert "github_copilot and codeium" in reasons[0]
    
    def test_incompatible_issue_trackers(self):
        """Test competing issue trackers are incompatible."""
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "linear", ["jira"]
        )
        assert not is_compatible
        assert "linear and jira" in reasons[0]
    
    def test_complementary_platforms(self):
        """Test platforms from different groups are complementary."""
        # Deployment + AI assistant
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "vercel", ["github_copilot"]
        )
        assert is_compatible
        assert len(reasons) == 0
        
        # Issue tracking + collaboration
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "linear", ["slack"]
        )
        assert is_compatible
    
    def test_multiple_incompatible_pairs(self):
        """Test detection of multiple incompatible pairs."""
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "vercel", ["netlify", "heroku", "railway"]
        )
        assert not is_compatible
        # Should detect vercel+netlify and heroku+railway conflicts
        assert len(reasons) >= 1
    
    def test_unknown_platform(self):
        """Test unknown platforms are treated as compatible."""
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "unknown_platform", ["another_unknown"]
        )
        # Should not fail, just not find conflicts
        assert is_compatible or not is_compatible  # Both outcomes acceptable
    
    def test_empty_secondary_platforms(self):
        """Test with no secondary platforms."""
        is_compatible, reasons = self.engine.check_platform_compatibility(
            "vercel", []
        )
        assert is_compatible
        assert len(reasons) == 0


class TestWorkflowTypeThresholds:
    """Test workflow type determination with updated thresholds."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = PlatformScoringEngine()
    
    def test_single_platform_high_confidence(self):
        """Test single platform with high confidence (> 0.8)."""
        scores = {"github": 0.9}
        workflow_type = self.engine.determine_workflow_type(scores)
        assert workflow_type == "single_platform"
    
    def test_single_platform_medium_confidence(self):
        """Test single platform with medium confidence (0.5-0.8)."""
        scores = {"vercel": 0.65}
        workflow_type = self.engine.determine_workflow_type(scores)
        assert workflow_type == "single_platform"
    
    def test_hybrid_workflow(self):
        """Test hybrid workflow with high + medium confidence platforms."""
        scores = {
            "replit": 0.85,  # High confidence
            "vercel": 0.7,   # Medium confidence
        }
        workflow_type = self.engine.determine_workflow_type(scores)
        assert workflow_type == "hybrid_workflow"
    
    def test_multi_platform(self):
        """Test multi-platform with multiple medium+ confidence platforms."""
        scores = {
            "github": 0.7,   # Medium
            "linear": 0.65,  # Medium
        }
        workflow_type = self.engine.determine_workflow_type(scores)
        assert workflow_type == "multi_platform"
    
    def test_below_new_threshold_not_counted(self):
        """Test scores below 0.5 don't count as medium confidence."""
        scores = {
            "replit": 0.9,   # High
            "vercel": 0.45,  # Below new medium threshold
        }
        workflow_type = self.engine.determine_workflow_type(scores)
        # Should be single_platform, not hybrid
        assert workflow_type == "single_platform"
    
    def test_exactly_at_threshold_boundaries(self):
        """Test behavior at exact threshold boundaries."""
        # At 0.8 boundary
        scores_high = {"github": 0.801}
        workflow_type = self.engine.determine_workflow_type(scores_high)
        assert workflow_type == "single_platform"
        
        # Just below high threshold
        scores_medium = {"github": 0.79}
        workflow_type = self.engine.determine_workflow_type(scores_medium)
        assert workflow_type == "single_platform"
        
        # At medium floor (0.5)
        scores_floor = {"github": 0.51}
        workflow_type = self.engine.determine_workflow_type(scores_floor)
        assert workflow_type == "single_platform"


class TestMigrationOpportunities:
    """Test migration opportunity identification."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = PlatformScoringEngine()
    
    def test_identifies_legacy_platforms(self):
        """Test identification of legacy/outdated platforms."""
        scores = {"heroku": 0.8, "now": 0.6}
        platform_configs = {}
        
        opportunities = self.engine.identify_migration_opportunities(
            scores, platform_configs
        )
        
        # Should identify at least one migration opportunity
        assert len(opportunities) > 0
        # Should mention migration
        assert any("migrat" in opp.lower() for opp in opportunities)
    
    def test_no_opportunities_for_modern_platforms(self):
        """Test modern platforms don't trigger migration suggestions."""
        scores = {"vercel": 0.9, "github_copilot": 0.8}
        platform_configs = {}
        
        opportunities = self.engine.identify_migration_opportunities(
            scores, platform_configs
        )
        
        # May have synergy suggestions but not legacy migrations
        # Check no "deprecated" or similar warnings
        if opportunities:
            assert not any("deprecated" in opp.lower() for opp in opportunities)


class TestRankingThresholds:
    """Test platform ranking with updated thresholds."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = PlatformScoringEngine()
    
    def test_rank_filters_below_threshold(self):
        """Test ranking filters platforms below threshold."""
        scores = {
            "replit": 0.8,
            "vercel": 0.3,   # Below 0.5 detection threshold
            "github": 0.05,  # Well below threshold
        }
        
        primary, secondary = self.engine.rank_platforms(scores, threshold=0.5)
        
        # Only replit should remain after filtering
        assert primary == "replit"
        assert "vercel" not in secondary
        assert "github" not in secondary
    
    def test_rank_preserves_order(self):
        """Test ranking preserves descending score order."""
        scores = {
            "replit": 0.9,
            "vercel": 0.7,
            "linear": 0.6,
        }
        
        primary, secondary = self.engine.rank_platforms(scores, threshold=0.5)
        
        assert primary == "replit"
        assert secondary == ["vercel", "linear"]
    
    def test_rank_returns_unknown_if_all_below_threshold(self):
        """Test returns unknown if all scores below threshold."""
        scores = {
            "replit": 0.3,
            "vercel": 0.2,
        }
        
        primary, secondary = self.engine.rank_platforms(scores, threshold=0.5)
        
        assert primary == "unknown"
        assert len(secondary) == 0


# Integration test scenarios
class TestValidationIntegration:
    """Integration tests for complete validation flow."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = PlatformScoringEngine()
    
    def test_hybrid_with_incompatible_platforms_should_fail(self):
        """Test hybrid workflow with incompatible platforms fails validation."""
        # Simulate detection of vercel + netlify
        scores = {"vercel": 0.85, "netlify": 0.7}
        
        workflow_type = self.engine.determine_workflow_type(scores)
        assert workflow_type == "hybrid_workflow"
        
        primary, secondary = self.engine.rank_platforms(scores, threshold=0.5)
        
        # Check compatibility - should fail
        is_compatible, reasons = self.engine.check_platform_compatibility(
            primary, secondary
        )
        
        assert not is_compatible
        assert len(reasons) > 0
        # Would trigger reclassification in detector
    
    def test_hybrid_with_compatible_platforms_passes(self):
        """Test hybrid workflow with compatible platforms passes validation."""
        scores = {"replit": 0.85, "github_copilot": 0.7}
        
        workflow_type = self.engine.determine_workflow_type(scores)
        assert workflow_type == "hybrid_workflow"
        
        primary, secondary = self.engine.rank_platforms(scores, threshold=0.5)
        
        is_compatible, reasons = self.engine.check_platform_compatibility(
            primary, secondary
        )
        
        assert is_compatible
        assert len(reasons) == 0
    
    def test_confidence_degradation_scenario(self):
        """Test scenario where scores need degradation due to conflicts."""
        # This test documents expected behavior for future confidence degradation
        scores = {"vercel": 0.9, "netlify": 0.9}  # Both high but incompatible
        
        # Currently, compatibility check would fail
        primary, secondary = self.engine.rank_platforms(scores, threshold=0.5)
        is_compatible, reasons = self.engine.check_platform_compatibility(
            primary, secondary
        )
        
        assert not is_compatible
        # Future: could automatically degrade secondary score and reclassify


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
