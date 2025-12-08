"""
Tests for Comment Filter Service

Tests the comment filtering functionality including:
- Checking allowed commenters
- Adding/removing commenters
- Managing settings
- Activity tracking
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Try to import SQLAlchemy, but skip tests if not available
pytest.importorskip("sqlalchemy", reason="SQLAlchemy not installed")

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker
    from codeflow_engine.database.models import (
        AllowedCommenter,
        Base,
        CommentFilterSettings,
    )
    from codeflow_engine.services.comment_filter import CommentFilterService
except ImportError:
    pytest.skip("Database or service modules not available", allow_module_level=True)


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create default settings (with auto_reply_enabled=False by default)
    default_settings = CommentFilterSettings(
        enabled=True,
        auto_add_commenters=False,
        auto_reply_enabled=False,  # Disabled by default until GitHub API is implemented
        whitelist_mode=True,
    )
    session.add(default_settings)
    session.commit()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def comment_service(in_memory_db):
    """Create CommentFilterService instance for testing."""
    return CommentFilterService(in_memory_db)


class TestCommentFilterSettings:
    """Tests for comment filter settings management."""

    @pytest.mark.asyncio
    async def test_get_settings_returns_default(self, comment_service):
        """Test that get_settings returns the default settings."""
        settings = await comment_service.get_settings()
        
        assert settings is not None
        assert settings.enabled is True
        assert settings.auto_add_commenters is False
        assert settings.auto_reply_enabled is False  # Default is False until GitHub API implemented
        assert settings.whitelist_mode is True

    @pytest.mark.asyncio
    async def test_update_settings_modifies_values(self, comment_service):
        """Test that update_settings modifies settings correctly."""
        updated = await comment_service.update_settings(
            enabled=False,
            auto_add_commenters=True,
            auto_reply_enabled=False,
            whitelist_mode=False,
        )
        
        assert updated.enabled is False
        assert updated.auto_add_commenters is True
        assert updated.auto_reply_enabled is False
        assert updated.whitelist_mode is False

    @pytest.mark.asyncio
    async def test_update_settings_partial_update(self, comment_service):
        """Test that partial updates work correctly."""
        # Update only one field
        updated = await comment_service.update_settings(enabled=False)
        
        assert updated.enabled is False
        # Other fields should remain unchanged (including False auto_reply_enabled)
        assert updated.auto_reply_enabled is False
        assert updated.whitelist_mode is True

    @pytest.mark.asyncio
    async def test_update_settings_custom_message(self, comment_service):
        """Test updating the auto-reply message."""
        custom_message = "Welcome @{username}! You're now on the list."
        updated = await comment_service.update_settings(
            auto_reply_message=custom_message
        )
        
        assert updated.auto_reply_message == custom_message


class TestCommenterManagement:
    """Tests for adding, removing, and listing commenters."""

    @pytest.mark.asyncio
    async def test_add_commenter_creates_new_record(self, comment_service):
        """Test that add_commenter creates a new record."""
        commenter = await comment_service.add_commenter(
            github_username="testuser",
            github_user_id=12345,
            added_by="admin",
            notes="Test user",
        )
        
        assert commenter.github_username == "testuser"
        assert commenter.github_user_id == 12345
        assert commenter.enabled is True
        assert commenter.added_by == "admin"
        assert commenter.notes == "Test user"

    @pytest.mark.asyncio
    async def test_add_commenter_twice_updates_existing(self, comment_service):
        """Test that adding same commenter twice updates the existing record."""
        # Add first time
        await comment_service.add_commenter(
            github_username="testuser",
            github_user_id=12345,
        )
        
        # Add second time with different notes
        commenter = await comment_service.add_commenter(
            github_username="testuser",
            notes="Updated notes",
        )
        
        assert commenter.github_username == "testuser"
        assert commenter.notes == "Updated notes"
        
        # Verify only one record exists
        commenters = await comment_service.list_commenters(enabled_only=False)
        assert len(commenters) == 1

    @pytest.mark.asyncio
    async def test_remove_commenter_disables_record(self, comment_service):
        """Test that remove_commenter disables the record (soft delete)."""
        # Add a commenter
        await comment_service.add_commenter(github_username="testuser")
        
        # Remove it
        success = await comment_service.remove_commenter("testuser")
        assert success is True
        
        # Verify it's disabled
        commenters = await comment_service.list_commenters(enabled_only=True)
        assert len(commenters) == 0
        
        # But still exists when listing all
        all_commenters = await comment_service.list_commenters(enabled_only=False)
        assert len(all_commenters) == 1
        assert all_commenters[0].enabled is False

    @pytest.mark.asyncio
    async def test_remove_nonexistent_commenter_returns_false(self, comment_service):
        """Test that removing non-existent commenter returns False."""
        success = await comment_service.remove_commenter("nonexistent")
        assert success is False

    @pytest.mark.asyncio
    async def test_list_commenters_pagination(self, comment_service):
        """Test that list_commenters supports pagination."""
        # Add multiple commenters
        for i in range(10):
            await comment_service.add_commenter(github_username=f"user{i}")
        
        # Get first page
        page1 = await comment_service.list_commenters(limit=5, offset=0)
        assert len(page1) == 5
        
        # Get second page
        page2 = await comment_service.list_commenters(limit=5, offset=5)
        assert len(page2) == 5
        
        # Verify different results
        page1_usernames = {c.github_username for c in page1}
        page2_usernames = {c.github_username for c in page2}
        assert page1_usernames.isdisjoint(page2_usernames)


class TestCommenterFiltering:
    """Tests for checking if commenters are allowed."""

    @pytest.mark.asyncio
    async def test_is_commenter_allowed_whitelist_mode(self, comment_service):
        """Test whitelist mode: only allowed commenters pass."""
        # Ensure whitelist mode
        await comment_service.update_settings(whitelist_mode=True)
        
        # Add one commenter
        await comment_service.add_commenter(github_username="allowed_user")
        
        # Check allowed user
        is_allowed = await comment_service.is_commenter_allowed("allowed_user")
        assert is_allowed is True
        
        # Check non-allowed user
        is_not_allowed = await comment_service.is_commenter_allowed("random_user")
        assert is_not_allowed is False

    @pytest.mark.asyncio
    async def test_is_commenter_allowed_disabled_commenter(self, comment_service):
        """Test that disabled commenters are not allowed."""
        # Add and then disable a commenter
        await comment_service.add_commenter(github_username="testuser")
        await comment_service.remove_commenter("testuser")
        
        # Should not be allowed
        is_allowed = await comment_service.is_commenter_allowed("testuser")
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_is_commenter_allowed_filtering_disabled(self, comment_service):
        """Test that when filtering is disabled, all commenters are allowed."""
        # Disable filtering
        await comment_service.update_settings(enabled=False)
        
        # Any user should be allowed
        is_allowed = await comment_service.is_commenter_allowed("any_user")
        assert is_allowed is True

    @pytest.mark.asyncio
    async def test_is_commenter_allowed_blacklist_mode(self, comment_service):
        """Test blacklist mode: all except blocked commenters pass."""
        # Set to blacklist mode
        await comment_service.update_settings(whitelist_mode=False)
        
        # Random user should be allowed
        is_allowed = await comment_service.is_commenter_allowed("random_user")
        assert is_allowed is True
        
        # Add a commenter and disable it (blacklist)
        await comment_service.add_commenter(github_username="blocked_user")
        await comment_service.remove_commenter("blocked_user")
        
        # Blocked user should not be allowed
        is_blocked = await comment_service.is_commenter_allowed("blocked_user")
        assert is_blocked is False


class TestCommenterActivity:
    """Tests for tracking commenter activity."""

    @pytest.mark.asyncio
    async def test_update_commenter_activity_increments_count(self, comment_service):
        """Test that updating activity increments comment count."""
        # Add a commenter
        commenter = await comment_service.add_commenter(github_username="testuser")
        initial_count = commenter.comment_count
        
        # Update activity
        updated = await comment_service.update_commenter_activity(
            "testuser", increment_count=True
        )
        
        assert updated is not None
        assert updated.comment_count == initial_count + 1
        assert updated.last_comment_at is not None

    @pytest.mark.asyncio
    async def test_update_commenter_activity_without_increment(self, comment_service):
        """Test updating activity without incrementing count."""
        # Add a commenter
        commenter = await comment_service.add_commenter(github_username="testuser")
        initial_count = commenter.comment_count
        
        # Update activity without increment
        updated = await comment_service.update_commenter_activity(
            "testuser", increment_count=False
        )
        
        assert updated is not None
        assert updated.comment_count == initial_count
        assert updated.last_comment_at is not None

    @pytest.mark.asyncio
    async def test_update_activity_nonexistent_user_returns_none(self, comment_service):
        """Test that updating activity for non-existent user returns None."""
        result = await comment_service.update_commenter_activity("nonexistent")
        assert result is None


class TestAutoReplyMessage:
    """Tests for auto-reply message generation."""

    @pytest.mark.asyncio
    async def test_get_auto_reply_message_formats_username(self, comment_service):
        """Test that auto-reply message formats username correctly."""
        # First enable auto_reply and set a custom message with username placeholder
        await comment_service.update_settings(
            auto_reply_enabled=True,
            auto_reply_message="Hello @{username}! Welcome."
        )
        
        message = await comment_service.get_auto_reply_message("testuser")
        assert message == "Hello @testuser! Welcome."

    @pytest.mark.asyncio
    async def test_get_auto_reply_message_when_disabled(self, comment_service):
        """Test that no message is returned when auto-reply is disabled."""
        # Auto-reply is disabled by default
        message = await comment_service.get_auto_reply_message("testuser")
        assert message is None

    @pytest.mark.asyncio
    async def test_get_auto_reply_message_default(self, comment_service):
        """Test default auto-reply message when enabled."""
        # Enable auto-reply to test the default message
        await comment_service.update_settings(auto_reply_enabled=True)
        
        message = await comment_service.get_auto_reply_message("testuser")
        
        assert message is not None
        assert "testuser" in message
        assert "allowed commenters" in message.lower()
