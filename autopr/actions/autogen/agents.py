"""
AutoGen Agents

Specialized agents for different tasks in the AutoGen system.
"""

from typing import Any, Dict, List, Optional

try:
    from autogen import ConversableAgent  # type: ignore
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    # Create dummy class for type annotations
    class ConversableAgentDummy:
        def __init__(self, *args: Any, **kwargs: Any) -> None: pass
        def initiate_chat(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
            return []

    ConversableAgent = ConversableAgentDummy


class AutoGenAgentFactory:
    """Factory for creating specialized AutoGen agents."""

    @staticmethod
    def create_code_analyzer(llm_config: Dict[str, Any]) -> ConversableAgent:
        """Create a code analyzer agent."""
        if not AUTOGEN_AVAILABLE:
            raise ImportError("AutoGen not installed. Install with: pip install pyautogen")

        return ConversableAgent(
            name="code_analyzer",
            system_message="""You are a senior code analyzer. Your role is to:
            1. Analyze code comments and identify the specific issue or request
            2. Understand the context and scope of the problem
            3. Classify the type of fix needed (syntax, logic, style, security, performance)
            4. Provide detailed analysis with confidence scores

            Always provide structured analysis with clear reasoning.""",
            llm_config=llm_config,
            human_input_mode="NEVER",
        )

    @staticmethod
    def create_code_fixer(llm_config: Dict[str, Any]) -> ConversableAgent:
        """Create a code fixer agent."""
        if not AUTOGEN_AVAILABLE:
            raise ImportError("AutoGen not installed. Install with: pip install pyautogen")

        return ConversableAgent(
            name="code_fixer",
            system_message="""You are an expert code fixer. Your role is to:
            1. Take analysis from the code analyzer
            2. Generate precise, minimal code fixes
            3. Ensure fixes follow best practices and project conventions
            4. Provide multiple solution options when appropriate""",
            llm_config=llm_config,
            human_input_mode="NEVER",
        )

    @staticmethod
    def create_security_auditor(llm_config: Dict[str, Any]) -> ConversableAgent:
        """Create a security auditor agent."""
        if not AUTOGEN_AVAILABLE:
            raise ImportError("AutoGen not installed. Install with: pip install pyautogen")

        return ConversableAgent(
            name="security_auditor",
            system_message="""You are a security expert. Your role is to:
            1. Identify potential security vulnerabilities
            2. Assess code for security best practices
            3. Provide security-focused recommendations
            4. Ensure compliance with security standards""",
            llm_config=llm_config,
            human_input_mode="NEVER",
        )
