"""
AutoPR Action: AutoGen Multi-Agent Integration
Collaborative PR comment handling using specialized AutoGen agents.
"""

import json
import os
from typing import Any

from pydantic import BaseModel

try:
    from autogen import ConversableAgent, GroupChat, GroupChatManager

    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    # Create dummy classes for type annotations
    ConversableAgent = object
    GroupChat = object
    GroupChatManager = object


class AutoGenInputs(BaseModel):
    comment_body: str
    file_path: str | None = None
    file_content: str | None = None
    pr_context: dict[str, Any] = {}
    task_type: str = "analyze_and_fix"  # "analyze_and_fix", "code_review", "security_audit"
    agents_config: dict[str, Any] = {}


class AutoGenOutputs(BaseModel):
    success: bool
    analysis: dict[str, Any] = {}
    recommendations: list[str] = []
    fix_code: str | None = None
    agent_conversations: list[dict[str, str]] = []
    consensus: str | None = None
    error_message: str | None = None


class AutoGenAgentSystem:
    def __init__(self, llm_config: dict[str, Any]) -> None:
        if not AUTOGEN_AVAILABLE:
            msg = "AutoGen not installed. Install with: pip install pyautogen"
            raise ImportError(msg)

        self.llm_config: dict[str, Any] = llm_config
        self.agents: dict[str, ConversableAgent] = {}
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize specialized agents for different tasks."""

        # Code Analyzer Agent
        self.agents["code_analyzer"] = ConversableAgent(
            "code_analyzer",
            system_message="""You are a senior code analyzer. Your role is to:
            1. Analyze code comments and identify the specific issue or request
            2. Understand the context and scope of the problem
            3. Classify the type of fix needed (syntax, logic, style, security, performance)
            4. Provide detailed analysis with confidence scores

            Always provide structured analysis with clear reasoning.""",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )

        # Code Fixer Agent
        self.agents["code_fixer"] = ConversableAgent(
            "code_fixer",
            system_message="""You are an expert code fixer. Your role is to:
            1. Take analysis from the code analyzer
            2. Generate precise, minimal code fixes
            3. Ensure fixes follow best practices and project conventions
            4. Provide multiple solution options when appropriate
            5. Include explanations for all changes

            Always write clean, tested, and well-documented code.""",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )

        # Quality Reviewer Agent
        self.agents["quality_reviewer"] = ConversableAgent(
            "quality_reviewer",
            system_message="""You are a quality assurance reviewer. Your role is to:
            1. Review proposed code fixes for correctness
            2. Check for potential side effects or breaking changes
            3. Ensure fixes maintain code quality and consistency
            4. Validate security and performance implications
            5. Approve or suggest improvements to fixes

            Be thorough but constructive in your reviews.""",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )

        # Security Auditor Agent
        self.agents["security_auditor"] = ConversableAgent(
            "security_auditor",
            system_message="""You are a cybersecurity expert. Your role is to:
            1. Identify potential security vulnerabilities in code
            2. Review fixes for security implications
            3. Suggest security best practices
            4. Flag any security-sensitive changes
            5. Ensure compliance with security standards

            Prioritize security without compromising functionality.""",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )

        # Project Manager Agent
        self.agents["project_manager"] = ConversableAgent(
            "project_manager",
            system_message="""You are a technical project manager. Your role is to:
            1. Coordinate between different agents
            2. Make final decisions on fix implementations
            3. Ensure solutions align with project goals
            4. Manage conflicting opinions between agents
            5. Provide clear, actionable summaries

            Focus on practical solutions that deliver value.""",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )

    def analyze_and_fix_comment(self, inputs: AutoGenInputs) -> AutoGenOutputs:
        """Use multi-agent collaboration to analyze and fix PR comments."""
        try:
            # Prepare the context message
            context_message = f"""
            PR Comment Analysis Task:

            Comment: {inputs.comment_body}
            File: {inputs.file_path or 'N/A'}

            File Content Preview:
            {inputs.file_content[:500] if inputs.file_content else 'No content provided'}

            PR Context: {json.dumps(inputs.pr_context, indent=2)}

            Please collaborate to:
            1. Analyze the comment and identify what needs to be done
            2. Propose a fix if applicable
            3. Review the fix for quality and security
            4. Reach consensus on the best solution
            """

            # Create group chat for collaboration
            participants = [
                self.agents["code_analyzer"],
                self.agents["code_fixer"],
                self.agents["quality_reviewer"],
            ]

            # Add security auditor for security-related tasks
            if (
                "security" in inputs.comment_body.lower()
                or "vulnerability" in inputs.comment_body.lower()
            ):
                participants.append(self.agents["security_auditor"])

            # Always include project manager
            participants.append(self.agents["project_manager"])

            # Create group chat
            groupchat = GroupChat(
                agents=participants,
                messages=[],
                max_round=10,
                speaker_selection_method="round_robin",
            )

            # Create group chat manager
            manager = GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)

            # Start the conversation
            chat_result: list[dict[str, Any]] = self.agents["code_analyzer"].initiate_chat(
                manager, message=context_message
            )

            # Extract results from conversation
            return self._extract_results_from_chat(chat_result, inputs)

        except Exception as e:
            return AutoGenOutputs(
                success=False, error_message=f"AutoGen collaboration failed: {e!s}"
            )

    def security_audit_workflow(self, inputs: AutoGenInputs) -> AutoGenOutputs:
        """Specialized security audit workflow."""
        try:
            context_message = f"""
            Security Audit Task:

            Comment: {inputs.comment_body}
            File: {inputs.file_path or 'N/A'}

            Please perform a comprehensive security audit focusing on:
            1. Identifying potential vulnerabilities
            2. Assessing security implications of changes
            3. Recommending security improvements
            4. Ensuring compliance with security best practices
            """

            # Security-focused conversation
            participants = [
                self.agents["security_auditor"],
                self.agents["code_analyzer"],
                self.agents["project_manager"],
            ]

            groupchat = GroupChat(agents=participants, messages=[], max_round=8)

            manager = GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)

            chat_result: list[dict[str, Any]] = self.agents["security_auditor"].initiate_chat(
                manager, message=context_message
            )

            return self._extract_results_from_chat(chat_result, inputs)

        except Exception as e:
            return AutoGenOutputs(success=False, error_message=f"Security audit failed: {e!s}")

    def code_review_workflow(self, inputs: AutoGenInputs) -> AutoGenOutputs:
        """Comprehensive code review workflow."""
        try:
            context_message = f"""
            Code Review Task:

            Comment: {inputs.comment_body}
            File: {inputs.file_path or 'N/A'}

            Please conduct a thorough code review covering:
            1. Code quality and maintainability
            2. Performance implications
            3. Best practices adherence
            4. Potential improvements
            5. Testing considerations
            """

            participants = [
                self.agents["quality_reviewer"],
                self.agents["code_analyzer"],
                self.agents["code_fixer"],
                self.agents["project_manager"],
            ]

            groupchat = GroupChat(agents=participants, messages=[], max_round=12)

            manager = GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)

            chat_result: list[dict[str, Any]] = self.agents["quality_reviewer"].initiate_chat(
                manager, message=context_message
            )

            return self._extract_results_from_chat(chat_result, inputs)

        except Exception as e:
            return AutoGenOutputs(success=False, error_message=f"Code review failed: {e!s}")

    def _extract_results_from_chat(
        self, chat_result: list[dict[str, Any]], inputs: AutoGenInputs
    ) -> AutoGenOutputs:
        """Extract structured results from agent conversations."""
        # Ensure chat_result is properly typed as a list of dicts
        chat_result_list: list[dict[str, Any]] = chat_result

        try:
            # Get all messages from the chat
            messages: list[dict[str, Any]] = chat_result_list

            # Extract agent conversations
            agent_conversations: list[dict[str, str]] = [
                {"agent": msg["name"], "message": msg["content"]}
                for msg in messages
                if isinstance(msg, dict) and "name" in msg and "content" in msg
            ]

            # Analyze conversations for key insights
            analysis: dict[str, Any] = self._analyze_conversations(agent_conversations)
            recommendations: list[str] = self._extract_recommendations(agent_conversations)
            fix_code: str | None = self._extract_fix_code(agent_conversations)
            consensus: str | None = self._extract_consensus(agent_conversations)

            return AutoGenOutputs(
                success=True,
                analysis=analysis,
                recommendations=recommendations,
                fix_code=fix_code,
                agent_conversations=agent_conversations,
                consensus=consensus,
            )

        except Exception as e:
            return AutoGenOutputs(success=False, error_message=f"Failed to extract results: {e!s}")

    def _analyze_conversations(self, conversations: list[dict[str, str]]) -> dict[str, Any]:
        """Analyze agent conversations for key insights."""
        analysis: dict[str, Any] = {
            "total_messages": len(conversations),
            "participating_agents": list({conv["agent"] for conv in conversations}),
            "key_topics": [],
            "confidence_level": "medium",
        }

        # Extract key topics from conversations
        all_content: str = " ".join(conv["message"] for conv in conversations)
        key_terms: list[str] = [
            "fix",
            "security",
            "performance",
            "bug",
            "improvement",
            "refactor",
        ]

        for term in key_terms:
            if term in all_content.lower():
                analysis["key_topics"].append(term)

        # Determine confidence based on agent agreement
        if len(analysis["participating_agents"]) >= 3:
            analysis["confidence_level"] = "high"
        elif "project_manager" in analysis["participating_agents"]:
            analysis["confidence_level"] = "medium"
        else:
            analysis["confidence_level"] = "low"

        return analysis

    def _extract_recommendations(self, conversations: list[dict[str, str]]) -> list[str]:
        """Extract actionable recommendations from conversations."""
        recommendations: list[str] = []

        for conv in conversations:
            content: str = conv["message"].lower()

            # Look for recommendation patterns
            if any(phrase in content for phrase in ["recommend", "suggest", "should", "consider"]):
                # Extract the sentence containing the recommendation
                sentences: list[str] = conv["message"].split(".")
                recommendations.extend(
                    sentence.strip()
                    for sentence in sentences
                    if any(
                        phrase in sentence.lower()
                        for phrase in ["recommend", "suggest", "should", "consider"]
                    )
                )

        return recommendations[:5]  # Limit to top 5 recommendations

    def _extract_fix_code(self, conversations: list[dict[str, str]]) -> str | None:
        """Extract proposed code fixes from conversations."""
        for conv in conversations:
            if conv["agent"] == "code_fixer" and "```" in conv["message"]:
                # Extract code blocks
                parts: list[str] = conv["message"].split("```")
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Odd indices are code blocks
                        return part.strip()

        return None

    def _extract_consensus(self, conversations: list[dict[str, str]]) -> str | None:
        """Extract final consensus from project manager."""
        for conv in reversed(conversations):  # Start from the end
            if conv["agent"] == "project_manager" and any(
                phrase in conv["message"].lower()
                for phrase in ["decision", "consensus", "final", "conclusion"]
            ):
                return conv["message"]

        return None


class AutoGenMultiAgent:
    def __init__(self) -> None:
        self.available = AUTOGEN_AVAILABLE

    def run(self, inputs: dict) -> dict:
        """Runs the multi-agent workflow."""
        if not self.available:
            msg = "AutoGen not available."
            raise RuntimeError(msg)
        # ... implementation ...
        return {}


def autogen_multi_agent_action(inputs: AutoGenInputs) -> AutoGenOutputs:
    """Main action interface for AutoGen multi-agent collaboration."""
    if not AUTOGEN_AVAILABLE:
        return AutoGenOutputs(
            success=False,
            error_message="AutoGen not available. Install with: pip install pyautogen",
        )

    try:
        # Configure LLM based on environment variables
        llm_config: dict[str, Any] = {
            "config_list": [
                {
                    "model": os.getenv("AUTOGEN_MODEL", "gpt-4"),
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "api_type": "openai",
                }
            ],
            "temperature": 0.1,
            "timeout": 120,
        }

        # Initialize agent system
        agent_system = AutoGenAgentSystem(llm_config)

        # Route to appropriate workflow
        if inputs.task_type == "security_audit":
            return agent_system.security_audit_workflow(inputs)
        if inputs.task_type == "code_review":
            return agent_system.code_review_workflow(inputs)
        # Default to analyze_and_fix
        return agent_system.analyze_and_fix_comment(inputs)

    except Exception as e:
        return AutoGenOutputs(success=False, error_message=f"AutoGen system failed: {e!s}")
