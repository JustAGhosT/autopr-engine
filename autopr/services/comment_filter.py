"""Comment Filter Service.

Provides functionality for managing allowed commenters and comment filtering.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from autopr.database.models import AllowedCommenter, CommentFilterSettings


logger = logging.getLogger(__name__)


class CommentFilterService:
    """Service for managing comment filtering and allowed commenters."""

    def __init__(self, db_session: Session | AsyncSession):
        """Initialize the service with a database session.
        
        Args:
            db_session: SQLAlchemy session (sync or async)
        """
        self.db_session = db_session
        self._is_async = isinstance(db_session, AsyncSession)

    async def get_settings(self) -> Optional[CommentFilterSettings]:
        """Get comment filter settings (singleton).
        
        Returns:
            CommentFilterSettings if exists, None otherwise
        """
        if self._is_async:
            result = await self.db_session.execute(
                select(CommentFilterSettings).limit(1)
            )
            return result.scalar_one_or_none()
        else:
            return self.db_session.query(CommentFilterSettings).first()

    async def update_settings(
        self,
        enabled: Optional[bool] = None,
        auto_add_commenters: Optional[bool] = None,
        auto_reply_enabled: Optional[bool] = None,
        auto_reply_message: Optional[str] = None,
        whitelist_mode: Optional[bool] = None,
    ) -> CommentFilterSettings:
        """Update comment filter settings.
        
        Args:
            enabled: Enable/disable comment filtering
            auto_add_commenters: Auto-add new commenters to allowed list
            auto_reply_enabled: Enable auto-reply when adding new commenters
            auto_reply_message: Template for auto-reply message
            whitelist_mode: Whitelist (True) or blacklist (False) mode
            
        Returns:
            Updated settings
        """
        settings = await self.get_settings()
        
        if settings is None:
            # Create default settings if none exist
            settings = CommentFilterSettings()
            self.db_session.add(settings)
        
        if enabled is not None:
            settings.enabled = enabled
        if auto_add_commenters is not None:
            settings.auto_add_commenters = auto_add_commenters
        if auto_reply_enabled is not None:
            settings.auto_reply_enabled = auto_reply_enabled
        if auto_reply_message is not None:
            settings.auto_reply_message = auto_reply_message
        if whitelist_mode is not None:
            settings.whitelist_mode = whitelist_mode
        
        if self._is_async:
            await self.db_session.commit()
            await self.db_session.refresh(settings)
        else:
            self.db_session.commit()
            self.db_session.refresh(settings)
        
        return settings

    async def is_commenter_allowed(self, github_username: str) -> bool:
        """Check if a commenter is allowed to have their comments processed.
        
        Args:
            github_username: GitHub username to check
            
        Returns:
            True if allowed, False otherwise
        """
        settings = await self.get_settings()
        if settings is None or not settings.enabled:
            # If filtering is disabled, allow all comments
            return True
        
        # Query for commenter without filtering by enabled status first
        if self._is_async:
            result = await self.db_session.execute(
                select(AllowedCommenter).where(
                    AllowedCommenter.github_username == github_username
                )
            )
            commenter = result.scalar_one_or_none()
        else:
            commenter = self.db_session.query(AllowedCommenter).filter(
                AllowedCommenter.github_username == github_username
            ).first()
        
        # In whitelist mode: allowed only if in list AND enabled
        # In blacklist mode: allowed unless explicitly blocked (in list AND disabled)
        if settings.whitelist_mode:
            return commenter is not None and commenter.enabled
        else:
            # Blacklist mode: user is allowed unless they are explicitly blocked
            if commenter is None:
                return True  # Not in list, so allowed
            return commenter.enabled  # In list: allowed if enabled, blocked if disabled

    async def add_commenter(
        self,
        github_username: str,
        github_user_id: Optional[int] = None,
        added_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AllowedCommenter:
        """Add a commenter to the allowed list.
        
        Args:
            github_username: GitHub username
            github_user_id: GitHub user ID (optional)
            added_by: Who added this commenter (username or system)
            notes: Optional notes about this commenter
            
        Returns:
            The created or updated AllowedCommenter
        """
        # Check if commenter already exists
        if self._is_async:
            result = await self.db_session.execute(
                select(AllowedCommenter).where(
                    AllowedCommenter.github_username == github_username
                )
            )
            commenter = result.scalar_one_or_none()
        else:
            commenter = self.db_session.query(AllowedCommenter).filter(
                AllowedCommenter.github_username == github_username
            ).first()
        
        if commenter is None:
            # Create new commenter
            commenter = AllowedCommenter(
                github_username=github_username,
                github_user_id=github_user_id,
                added_by=added_by,
                notes=notes,
                enabled=True,
            )
            self.db_session.add(commenter)
            logger.info(f"Added new allowed commenter: {github_username}")
        else:
            # Update existing commenter
            if github_user_id is not None:
                commenter.github_user_id = github_user_id
            if notes is not None:
                commenter.notes = notes
            commenter.enabled = True
            logger.info(f"Updated allowed commenter: {github_username}")
        
        if self._is_async:
            await self.db_session.commit()
            await self.db_session.refresh(commenter)
        else:
            self.db_session.commit()
            self.db_session.refresh(commenter)
        
        return commenter

    async def remove_commenter(self, github_username: str) -> bool:
        """Remove a commenter from the allowed list (soft delete by disabling).
        
        Args:
            github_username: GitHub username to remove
            
        Returns:
            True if commenter was found and disabled, False otherwise
        """
        if self._is_async:
            result = await self.db_session.execute(
                select(AllowedCommenter).where(
                    AllowedCommenter.github_username == github_username
                )
            )
            commenter = result.scalar_one_or_none()
        else:
            commenter = self.db_session.query(AllowedCommenter).filter(
                AllowedCommenter.github_username == github_username
            ).first()
        
        if commenter is None:
            return False
        
        commenter.enabled = False
        
        if self._is_async:
            await self.db_session.commit()
        else:
            self.db_session.commit()
        
        logger.info(f"Disabled allowed commenter: {github_username}")
        return True

    async def update_commenter_activity(
        self,
        github_username: str,
        increment_count: bool = True,
    ) -> Optional[AllowedCommenter]:
        """Update commenter's last activity time and optionally increment count.
        
        Args:
            github_username: GitHub username
            increment_count: Whether to increment the comment count
            
        Returns:
            Updated AllowedCommenter if exists, None otherwise
        """
        if self._is_async:
            result = await self.db_session.execute(
                select(AllowedCommenter).where(
                    AllowedCommenter.github_username == github_username
                )
            )
            commenter = result.scalar_one_or_none()
        else:
            commenter = self.db_session.query(AllowedCommenter).filter(
                AllowedCommenter.github_username == github_username
            ).first()
        
        if commenter is None:
            return None
        
        commenter.last_comment_at = datetime.now(timezone.utc)
        if increment_count:
            commenter.comment_count += 1
        
        if self._is_async:
            await self.db_session.commit()
            await self.db_session.refresh(commenter)
        else:
            self.db_session.commit()
            self.db_session.refresh(commenter)
        
        return commenter

    async def list_commenters(
        self,
        enabled_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AllowedCommenter]:
        """List allowed commenters with pagination.
        
        Args:
            enabled_only: Only return enabled commenters
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of AllowedCommenter records
        """
        query = select(AllowedCommenter)
        
        if enabled_only:
            query = query.where(AllowedCommenter.enabled.is_(True))
        
        query = query.order_by(AllowedCommenter.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        if self._is_async:
            result = await self.db_session.execute(query)
            return list(result.scalars().all())
        else:
            result = self.db_session.execute(query)
            return list(result.scalars().all())

    async def get_auto_reply_message(self, github_username: str) -> Optional[str]:
        """Get the auto-reply message for a new commenter.
        
        Args:
            github_username: GitHub username to format into the message
            
        Returns:
            Formatted auto-reply message if enabled, None otherwise
        """
        settings = await self.get_settings()
        if settings is None or not settings.auto_reply_enabled:
            return None
        
        return settings.auto_reply_message.format(username=github_username)
