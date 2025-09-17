"""
Issue Fixer Module

This module handles the actual fixing of linting issues using AI agents.
"""

import logging
import time
from typing import Any

from autopr.actions.ai_linting_fixer.ai_agent_manager import AIAgentManager
from autopr.actions.ai_linting_fixer.error_handler import (
    ErrorHandler, create_error_context)
from autopr.actions.ai_linting_fixer.file_manager import FileManager
from autopr.actions.ai_linting_fixer.models import (LintingFixResult,
                                                    LintingIssue)

logger = logging.getLogger(__name__)


class IssueFixer:
    """Handles the actual fixing of linting issues."""

    def __init__(
        self,
        ai_agent_manager: AIAgentManager,
        file_manager: FileManager,
        error_handler: ErrorHandler,
        database=None,
    ):
        """Initialize the issue fixer."""
        self.ai_agent_manager = ai_agent_manager
        self.file_manager = file_manager
        self.error_handler = error_handler
        self.database = database

    def fix_issues_with_ai(
        self,
        issues: list[LintingIssue],
        max_fixes: int = 10,
        provider: str | None = None,
        model: str | None = None,
    ) -> LintingFixResult:
        """Fix linting issues using AI."""
        if not issues:
            return LintingFixResult(
                success=True, fixed_issues=[], remaining_issues=[], modified_files=[]
            )

        try:
            logger.info(f"Starting AI-powered fix for {len(issues)} issues")

            # Create error context
            context = create_error_context(
                function_name="fix_issues_with_ai",
                workflow_step="ai_fixing",
                provider=provider,
                model=model,
                issue_count=len(issues),
            )

            # Group issues by file for efficient processing
            issues_by_file: dict[str, list[LintingIssue]] = {}
            for issue in issues:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)

            fixed_issues: list[str] = []
            remaining_issues: list[str] = []
            modified_files: list[str] = []

            # Process each file
            for file_path, file_issues in issues_by_file.items():
                try:
                    # Capture original error codes for this file
                    original_error_codes = [issue.error_code for issue in file_issues]

                    file_result = self._fix_file_issues(
                        file_path=file_path,
                        issues=file_issues,
                        provider=provider,
                        model=model,
                    )

                    if file_result["success"]:
                        # Get the error codes that were actually fixed
                        fixed_error_codes = file_result.get("fixed_issues", [])
                        fixed_issues.extend(fixed_error_codes)

                        # Compute remaining unfixed issues for this file
                        remaining_codes = [
                            code for code in original_error_codes
                            if code not in fixed_error_codes
                        ]
                        remaining_issues.extend(remaining_codes)

                        if file_result["modified"]:
                            modified_files.append(file_path)
                    else:
                        # If file processing failed, all issues remain unfixed
                        remaining_issues.extend(original_error_codes)

                except Exception as e:
                    # Handle file-specific errors
                    file_context = create_error_context(
                        file_path=file_path,
                        function_name="_fix_file_issues",
                        workflow_step="file_processing",
                        provider=provider,
                        model=model,
                    )

                    self.error_handler.log_error(
                        e,
                        file_context,
                        {"file_path": file_path, "issue_count": len(file_issues)},
                        display=True,
                    )

                    # Attempt recovery
                    error_info = self.error_handler.create_error_info(e, file_context)
                    if self.error_handler.attempt_recovery(error_info):
                        logger.info(f"Recovery attempted for {file_path}")
                        # Could implement retry logic here
                    else:
                        logger.exception(f"Failed to process {file_path}: {e}")
                        # All original issues remain unfixed due to processing error
                        remaining_issues.extend(original_error_codes)

            # Create result
            result = LintingFixResult(
                success=len(fixed_issues) > 0,
                fixed_issues=fixed_issues,
                remaining_issues=remaining_issues,
                modified_files=modified_files,
            )

            logger.info(
                f"AI fixing completed: {len(fixed_issues)} fixed, {len(remaining_issues)} remaining"
            )
            return result

        except Exception as e:
            # Handle general errors
            self.error_handler.log_error(
                e,
                context,
                {"issue_count": len(issues), "max_fixes": max_fixes},
                display=True,
            )

            logger.exception(f"AI fixing failed: {e}")
            return LintingFixResult(
                success=False,
                fixed_issues=[],
                remaining_issues=[issue.error_code for issue in issues],
                modified_files=[],
                error_message=str(e),
            )

    def _fix_file_issues(
        self,
        file_path: str,
        issues: list[LintingIssue],
        provider: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Fix issues in a single file."""
        start_time = time.time()

        try:
            # Create error context
            context = create_error_context(
                file_path=file_path,
                function_name="_fix_file_issues",
                workflow_step="file_processing",
                provider=provider,
                model=model,
            )

            # Read file content
            success, original_content = self.file_manager.read_file_safely(file_path)
            if not success:
                msg = f"Could not read file: {file_path}"
                raise FileNotFoundError(msg)

            # Validate syntax before processing
            from autopr.actions.ai_linting_fixer.code_analyzer import \
                CodeAnalyzer

            code_analyzer = CodeAnalyzer()
            syntax_valid_before = code_analyzer.validate_python_syntax(original_content)
            if not syntax_valid_before:
                logger.warning(f"File {file_path} has syntax errors before processing")

            # Create backup
            backup_path = self.file_manager.create_backup(file_path)

            # Process issues with AI
            fixed_content = original_content
            fixed_issues = []

            for issue in issues:
                try:
                    # Create issue-specific context
                    issue_context = create_error_context(
                        file_path=file_path,
                        line_number=issue.line_number,
                        function_name="_fix_file_issues",
                        workflow_step="issue_fixing",
                        provider=provider,
                        model=model,
                        error_code=issue.error_code,
                    )

                    # Attempt to fix the issue
                    fix_result = self._fix_single_issue(
                        file_path=file_path,
                        content=fixed_content,
                        issue=issue,
                        provider=provider,
                        model=model,
                    )

                    if fix_result["success"]:
                        fixed_content = fix_result["content"]
                        fixed_issues.append(issue.error_code)

                except Exception as e:
                    # Handle issue-specific errors
                    self.error_handler.log_error(
                        e,
                        issue_context,
                        {
                            "file_path": file_path,
                            "line_number": issue.line_number,
                            "error_code": issue.error_code,
                            "issue_message": issue.message,
                        },
                        display=True,
                    )

                    # Continue with next issue
                    continue

            # Validate syntax after processing
            syntax_valid_after = code_analyzer.validate_python_syntax(fixed_content)

            # Write fixed content if changes were made
            modified = fixed_content != original_content
            if modified:
                success = self.file_manager.write_file_safely(
                    file_path, fixed_content, backup=False
                )  # Already backed up
                if not success:
                    # Try to restore from backup if available
                    if backup_path:
                        self.file_manager.restore_from_backup(file_path, backup_path)
                        logger.error(
                            f"Failed to write fixed content to {file_path}, restored from backup"
                        )
                        return {
                            "success": False,
                            "error": "Failed to write fixed content",
                            "fixed_issues": [],
                            "modified": False,
                        }

            processing_time = time.time() - start_time

            return {
                "success": True,
                "fixed_issues": fixed_issues,
                "modified": modified,
                "processing_time": processing_time,
                "syntax_valid_before": syntax_valid_before,
                "syntax_valid_after": syntax_valid_after,
            }

        except Exception as e:
            # Handle general file processing errors
            self.error_handler.log_error(
                e,
                context,
                {"file_path": file_path, "issue_count": len(issues)},
                display=True,
            )

            return {
                "success": False,
                "error": str(e),
                "fixed_issues": [],
                "modified": False,
            }

    def _safe_extract_response_content(self, response) -> str:
        """
        Safely extract and normalize response content from various response types.
        
        Args:
            response: The response object from LLM (could be None, dict, string, etc.)
            
        Returns:
            str: Normalized string content, or fallback message if extraction fails
        """
        if response is None:
            return "<no response>"
        
        # Try to extract content from various response formats
        content = None
        
        # Check if response has a content attribute
        if hasattr(response, 'content'):
            content = response.content
        # Check if response is a dict with content key
        elif isinstance(response, dict):
            content = response.get('content')
        # Check if response is already a string
        elif isinstance(response, str):
            content = response
        # Try to get content via get method
        elif hasattr(response, 'get'):
            content = response.get('content')
        
        # If we still don't have content, convert to string
        if content is None:
            content = str(response)
        
        # Ensure content is a string and normalize it
        if not isinstance(content, str):
            content = str(content)
        
        # Normalize whitespace and ensure UTF-8 encoding
        content = content.strip()
        
        # Handle empty content
        if not content:
            return "<empty response>"
        
        return content

    def fix_single_issue(
        self,
        file_path: str,
        content: str,
        issue: LintingIssue,
        provider: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Fix a single linting issue using AI."""
        start_time = time.time()

        try:
            # Select appropriate agent
            agent_type = self.ai_agent_manager.select_agent_for_issues([issue])

            # Get prompts
            system_prompt = self.ai_agent_manager.get_specialized_system_prompt(
                agent_type, [issue]
            )
            user_prompt = self.ai_agent_manager.get_user_prompt(
                file_path, content, [issue]
            )

            # Call AI - Honor provider override if a specific provider is requested
            llm_mgr = self.ai_agent_manager.llm_manager
            request_payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "model": model or "gpt-4.1",
                "temperature": 0.1,
                "max_tokens": 2000,
            }
            if provider and hasattr(llm_mgr, "get_llm"):
                chosen = llm_mgr.get_llm(provider)
                if chosen:
                    response = chosen.complete(request_payload)
                else:
                    response = llm_mgr.complete(request_payload)
            else:
                response = llm_mgr.complete(request_payload)

            # Parse response - safely extract content first
            response_content = self._safe_extract_response_content(response)
            parsed_response = self.ai_agent_manager.parse_ai_response(response_content)

            if not parsed_response.get("success", False):
                error_msg = parsed_response.get("error", "Unknown error")
                logger.warning(
                    f"AI fix failed for {issue.error_code} in {file_path}: {error_msg}"
                )

                # Log interaction to database if available
                if self.database:
                    try:
                        interaction_data = {
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "file_path": file_path,
                            "issue_type": issue.error_code,
                            "issue_details": f"{issue.error_code}: {issue.message}",
                            "provider_used": provider or "azure_openai",
                            "model_used": model or "gpt-4.1",
                            "system_prompt": system_prompt[:1000],
                            "user_prompt": user_prompt[:1000],
                            "ai_response": response_content[:1000],
                            "fix_successful": False,
                            "confidence_score": 0.0,
                            "fixed_codes": "[]",
                            "error_message": error_msg,
                            "syntax_valid_before": True,
                            "syntax_valid_after": False,
                            "file_size_chars": len(content),
                            "prompt_tokens": 0,
                            "response_tokens": 0,
                            "processing_duration": time.time() - start_time,
                            "api_response_time": 0.0,
                            "queue_wait_time": 0.0,
                            "file_complexity_score": 0.0,
                            "parallel_worker_id": 0,
                            "retry_count": 0,
                            "memory_usage_mb": 0.0,
                            "tokens_per_second": 0.0,
                            "agent_type": agent_type,
                        }
                        self.database.log_interaction(interaction_data)
                    except Exception as e:
                        logger.warning(
                            f"Failed to log failed interaction to database: {e}"
                        )

                return {
                    "success": False,
                    "error": error_msg,
                    "agent_type": agent_type,
                    "raw_response": parsed_response.get("raw_response", ""),
                }

            # Apply the fix to the specific line
            fixed_line = parsed_response.get("fixed_code", "")
            if fixed_line and issue.line_number > 0:
                # Split content into lines
                lines = content.split("\n")
                if 1 <= issue.line_number <= len(lines):
                    # Replace the specific line (line_number is 1-indexed)
                    lines[issue.line_number - 1] = fixed_line.strip()
                    fixed_content = "\n".join(lines)
                else:
                    fixed_content = content
            else:
                fixed_content = content

            # Calculate confidence
            confidence = self.ai_agent_manager.calculate_confidence_score(
                parsed_response, [issue], content, fixed_content
            )

            # Log confidence score to performance tracker
            if hasattr(self.ai_agent_manager, "performance_tracker"):
                self.ai_agent_manager.performance_tracker.log_confidence_score(
                    confidence
                )

            # Log interaction to database if available
            if self.database:
                try:
                    interaction_data = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "file_path": file_path,
                        "issue_type": issue.error_code,
                        "issue_details": f"{issue.error_code}: {issue.message}",
                        "provider_used": provider or "azure_openai",
                        "model_used": model or "gpt-4.1",
                        "system_prompt": system_prompt[:1000],  # Truncate for database
                        "user_prompt": user_prompt[:1000],  # Truncate for database
                        "ai_response": response_content[:1000],  # Truncate for database
                        "fix_successful": True,
                        "confidence_score": confidence,
                        "fixed_codes": str(parsed_response.get("changes_made", [])),
                        "error_message": None,
                        "syntax_valid_before": True,  # Assume valid before
                        "syntax_valid_after": True,  # Assume valid after
                        "file_size_chars": len(content),
                        "prompt_tokens": 0,  # Would need to get from LLM response
                        "response_tokens": 0,  # Would need to get from LLM response
                        "processing_duration": time.time() - start_time,
                        "api_response_time": 0.0,  # Would need to track API time
                        "queue_wait_time": 0.0,
                        "file_complexity_score": 0.0,
                        "parallel_worker_id": 0,
                        "retry_count": 0,
                        "memory_usage_mb": 0.0,
                        "tokens_per_second": 0.0,
                        "agent_type": agent_type,
                    }
                    self.database.log_interaction(interaction_data)
                except Exception as e:
                    logger.warning(f"Failed to log interaction to database: {e}")

            return {
                "success": True,
                "content": fixed_content,
                "confidence": confidence,
                "agent_type": agent_type,
                "changes_made": parsed_response.get("changes_made", []),
                "explanation": parsed_response.get("explanation", ""),
            }

        except Exception as e:
            logger.exception(
                f"Error fixing issue {issue.error_code} in {file_path}: {e}"
            )
            return {"success": False, "error": str(e), "agent_type": "unknown"}

    def fix_issues_sync_fallback(
        self,
        issues: list[LintingIssue],
        max_fixes: int = 10,
        provider: str | None = None,
        model: str | None = None,
    ) -> LintingFixResult:
        """Synchronous fallback for fixing issues."""
        logger.info("Using synchronous fallback for issue fixing")
        return self.fix_issues_with_ai(issues, max_fixes, provider, model)
