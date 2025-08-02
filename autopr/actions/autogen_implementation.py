"""
AutoPR Action: AutoGen Multi-Agent Implementation
Uses AutoGen for complex multi-agent development tasks
"""

from datetime import datetime
import json
import os
from typing import Any

from pydantic import BaseModel, Field

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
    task_description: str
    task_type: (
        str  # "feature_development", "bug_fix", "security_review", "performance_optimization"
    )
    repository: str
    file_paths: list[str] = []
    requirements: dict[str, Any] = {}
    complexity_level: str = "medium"  # "simple", "medium", "complex"
    max_agents: int = 4


class AutoGenOutputs(BaseModel):
    implementation_plan: str
    code_changes: dict[str, str] = Field(default_factory=dict)  # file_path -> code_content
    test_files: dict[str, str] = Field(default_factory=dict)  # test_file_path -> test_content
    documentation: str
    agent_conversations: list[dict[str, Any]] = Field(default_factory=list)
    quality_score: float
    success: bool
    errors: list[str] = Field(default_factory=list)


class AutoGenImplementation:
    def __init__(self) -> None:
        if not AUTOGEN_AVAILABLE:
            msg = "AutoGen not installed. Install with: pip install pyautogen"
            raise ImportError(msg)

        self.llm_config = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 0.1,
            "timeout": 120,
        }

        # Alternative LLM configurations
        self.alternative_configs = {
            "claude": {
                "model": "claude-3-sonnet-20240229",
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "api_type": "anthropic",
            },
            "mistral": {
                "model": "mistral-large-latest",
                "api_key": os.getenv("MISTRAL_API_KEY"),
                "api_type": "mistral",
            },
        }

    def execute_multi_agent_task(self, inputs: AutoGenInputs) -> AutoGenOutputs:
        """Main function to execute multi-agent development task"""

        if not AUTOGEN_AVAILABLE:
            return AutoGenOutputs(
                implementation_plan="",
                code_changes={},
                test_files={},
                documentation="",
                agent_conversations=[],
                quality_score=0.0,
                success=False,
                errors=["AutoGen not available"],
            )

        try:
            # Create specialized agents based on task type
            agents = self._create_agents(inputs.task_type, inputs.complexity_level)

            # Setup group chat
            group_chat = GroupChat(
                agents=agents,
                messages=[],
                max_round=20,
                speaker_selection_method="round_robin",
            )

            # Create group chat manager
            manager = GroupChatManager(groupchat=group_chat, llm_config=self.llm_config)

            # Execute the task
            conversation_result = self._execute_conversation(agents, manager, inputs)

            # Process results
            return self._process_results(conversation_result, inputs)

        except Exception as e:
            return AutoGenOutputs(
                implementation_plan="",
                code_changes={},
                test_files={},
                documentation="",
                agent_conversations=[],
                quality_score=0.0,
                success=False,
                errors=[str(e)],
            )

    def _create_agents(self, task_type: str, complexity_level: str) -> list[ConversableAgent]:
        """Create specialized agents based on task requirements"""

        agents = []

        # Always include a Software Architect for planning
        architect = ConversableAgent(
            name="Software_Architect",
            system_message="""
You are a Senior Software Architect with expertise in TypeScript, React, and modern development practices.

Your responsibilities:
1. Analyze requirements and create detailed implementation plans
2. Design system architecture and component interactions
3. Ensure code follows best practices and design patterns
4. Review overall solution quality and maintainability

Focus on:
- Clean, maintainable code architecture
- TypeScript best practices and type safety
- Component design and reusability
- Performance considerations
- Testing strategy
            """,
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )
        agents.append(architect)

        # Always include a Senior Developer for implementation
        developer = ConversableAgent(
            name="Senior_Developer",
            system_message="""
You are a Senior TypeScript/React Developer with expertise in modern web development.

Your responsibilities:
1. Implement features based on architectural designs
2. Write clean, efficient, and well-documented code
3. Follow TypeScript best practices and ensure type safety
4. Create robust error handling and edge case management
5. Optimize code for performance and maintainability

Coding standards:
- Use proper TypeScript interfaces and types
- Implement proper error handling
- Write self-documenting code with clear variable names
- Follow React best practices (hooks, state management)
- Ensure accessibility compliance
            """,
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )
        agents.append(developer)

        # Add task-specific agents
        if task_type == "security_review" or complexity_level == "complex":
            security_agent = ConversableAgent(
                name="Security_Auditor",
                system_message="""
You are a Security Specialist focused on web application security and secure coding practices.

Your responsibilities:
1. Review code for security vulnerabilities
2. Ensure proper input validation and sanitization
3. Check for authentication and authorization issues
4. Verify secure data handling and storage
5. Identify potential attack vectors

Security focus areas:
- XSS prevention and input sanitization
- SQL injection prevention
- Authentication and session management
- CSRF protection
- Secure API design
- Data encryption and privacy
                """,
                llm_config=self.llm_config,
                human_input_mode="NEVER",
            )
            agents.append(security_agent)

        if (
            task_type in {"feature_development", "performance_optimization"}
            or complexity_level == "complex"
        ):
            qa_engineer = ConversableAgent(
                name="QA_Engineer",
                system_message="""
You are a QA Engineer specializing in automated testing and quality assurance.

Your responsibilities:
1. Design comprehensive test strategies
2. Create unit tests, integration tests, and E2E tests
3. Ensure test coverage meets quality standards
4. Validate edge cases and error scenarios
5. Review code for testability and maintainability

Testing expertise:
- Jest/Vitest unit testing
- React Testing Library for component tests
- Playwright for E2E testing
- Test-driven development (TDD)
- Mocking and stubbing strategies
- Performance testing considerations
                """,
                llm_config=self.llm_config,
                human_input_mode="NEVER",
            )
            agents.append(qa_engineer)

        # Add Code Reviewer for complex tasks
        if complexity_level == "complex":
            reviewer = ConversableAgent(
                name="Code_Reviewer",
                system_message="""
You are a Senior Code Reviewer with expertise in code quality and best practices.

Your responsibilities:
1. Review all code changes for quality and maintainability
2. Ensure adherence to coding standards and conventions
3. Identify potential bugs and edge cases
4. Suggest improvements for performance and readability
5. Validate that requirements are fully met

Review criteria:
- Code readability and maintainability
- Performance optimization opportunities
- Error handling completeness
- TypeScript type safety
- Test coverage adequacy
- Documentation quality
                """,
                llm_config=self.llm_config,
                human_input_mode="NEVER",
            )
            agents.append(reviewer)

        return agents

    def _execute_conversation(
        self, agents: list, manager: GroupChatManager, inputs: AutoGenInputs
    ) -> dict:
        """Execute the multi-agent conversation"""

        # Prepare the initial task message
        task_message = self._create_task_message(inputs)

        # Start the conversation
        conversation_history = []

        try:
            # Initiate the conversation with the architect
            architect = agents[0]  # First agent is always the architect

            result = architect.initiate_chat(manager, message=task_message, max_turns=20)

            # Extract conversation history
            conversation_history = manager.groupchat.messages

            return {
                "success": True,
                "conversation_history": conversation_history,
                "final_result": result,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "conversation_history": conversation_history,
            }

    def _create_task_message(self, inputs: AutoGenInputs) -> str:
        """Create the initial task message for agents"""

        message = f"""
# Development Task: {inputs.task_type.replace('_', ' ').title()}

## Task Description
{inputs.task_description}

## Repository
{inputs.repository}

## File Paths (if specific files need modification)
{', '.join(inputs.file_paths) if inputs.file_paths else 'No specific files specified'}

## Requirements
{json.dumps(inputs.requirements, indent=2) if inputs.requirements else 'No specific requirements'}

## Complexity Level
{inputs.complexity_level}

## Expected Deliverables
1. **Implementation Plan**: Detailed step-by-step plan
2. **Code Changes**: Complete implementation with proper TypeScript types
3. **Test Files**: Comprehensive test coverage
4. **Documentation**: Clear documentation for the implementation

## Collaboration Instructions
- Software Architect: Start by analyzing requirements and creating an implementation plan
- Senior Developer: Implement the solution based on the architectural plan
- Security Auditor (if present): Review for security vulnerabilities
- QA Engineer (if present): Create comprehensive tests
- Code Reviewer (if present): Provide final quality review

Please work together to create a complete, production-ready solution.
        """

        return message.strip()

    def _process_results(self, conversation_result: dict, inputs: AutoGenInputs) -> AutoGenOutputs:
        """Process the conversation results into structured output"""

        if not conversation_result.get("success"):
            return AutoGenOutputs(
                implementation_plan="",
                code_changes={},
                test_files={},
                documentation="",
                agent_conversations=[],
                quality_score=0.0,
                success=False,
                errors=[conversation_result.get("error", "Unknown error")],
            )

        conversation_history = conversation_result.get("conversation_history", [])

        # Extract different types of content from conversation
        implementation_plan = self._extract_implementation_plan(conversation_history)
        code_changes = self._extract_code_changes(conversation_history)
        test_files = self._extract_test_files(conversation_history)
        documentation = self._extract_documentation(conversation_history)

        # Calculate quality score based on various factors
        quality_score = self._calculate_quality_score(
            implementation_plan, code_changes, test_files, conversation_history
        )

        # Format conversation history
        formatted_conversations = self._format_conversations(conversation_history)

        return AutoGenOutputs(
            implementation_plan=implementation_plan,
            code_changes=code_changes,
            test_files=test_files,
            documentation=documentation,
            agent_conversations=formatted_conversations,
            quality_score=quality_score,
            success=True,
            errors=[],
        )

    def _extract_implementation_plan(self, conversation_history: list) -> str:
        """Extract implementation plan from conversation"""
        plan_content = []

        for message in conversation_history:
            content = message.get("content", "")
            if "implementation plan" in content.lower() or "plan:" in content.lower():
                plan_content.append(f"**{message.get('name', 'Agent')}**: {content}")

        return "\n\n".join(plan_content) if plan_content else "No implementation plan found"

    def _extract_code_changes(self, conversation_history: list) -> dict[str, str]:
        """Extract code changes from conversation"""
        code_changes = {}

        for message in conversation_history:
            content = message.get("content", "")

            # Look for code blocks
            if "```" in content:
                # Extract code blocks and try to determine file paths
                import re

                code_blocks = re.findall(
                    r"```(?:typescript|tsx|ts|javascript|jsx|js)?\n(.*?)\n```",
                    content,
                    re.DOTALL,
                )

                for i, code_block in enumerate(code_blocks):
                    # Try to extract filename from context
                    filename = self._extract_filename_from_context(content, code_block)
                    if not filename:
                        filename = f"generated_file_{i + 1}.tsx"

                    code_changes[filename] = code_block.strip()

        return code_changes

    def _extract_test_files(self, conversation_history: list) -> dict[str, str]:
        """Extract test files from conversation"""
        test_files = {}

        for message in conversation_history:
            content = message.get("content", "")

            if "test" in content.lower() and "```" in content:
                import re

                code_blocks = re.findall(
                    r"```(?:typescript|tsx|ts|javascript|jsx|js)?\n(.*?)\n```",
                    content,
                    re.DOTALL,
                )

                for i, code_block in enumerate(code_blocks):
                    if (
                        "test" in code_block.lower()
                        or "describe" in code_block
                        or "it(" in code_block
                    ):
                        filename = f"test_file_{i + 1}.test.tsx"
                        test_files[filename] = code_block.strip()

        return test_files

    def _extract_documentation(self, conversation_history: list) -> str:
        """Extract documentation from conversation"""
        doc_content = []

        for message in conversation_history:
            content = message.get("content", "")
            if "documentation" in content.lower() or "readme" in content.lower():
                doc_content.append(f"**{message.get('name', 'Agent')}**: {content}")

        return "\n\n".join(doc_content) if doc_content else "No documentation found"

    def _extract_filename_from_context(self, content: str, code_block: str) -> str | None:
        """Try to extract filename from the context around a code block"""
        import re

        # Look for common filename patterns
        filename_patterns = [
            r"File: ([^\n]+)",
            r"`([^`]+\.(?:tsx?|jsx?|ts|js))`",
            r"([a-zA-Z][a-zA-Z0-9_-]*\.(?:tsx?|jsx?|ts|js))",
        ]

        for pattern in filename_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        # If code contains component or class names, generate filename
        if "export default" in code_block or "export class" in code_block:
            component_match = re.search(
                r"(?:export default|export class|function) (\w+)", code_block
            )
            if component_match:
                component_name = component_match.group(1)
                return f"{component_name}.tsx"

        return None

    def _calculate_quality_score(
        self, plan: str, code_changes: dict, test_files: dict, conversation: list
    ) -> float:
        """Calculate quality score based on various factors"""
        score = 0.0
        max_score = 100.0

        # Implementation plan quality (20 points)
        if len(plan) > 100:
            score += 20
        elif len(plan) > 50:
            score += 10

        # Code changes quality (40 points)
        if code_changes:
            score += 20  # Base points for having code

            # Check for TypeScript types
            for code in code_changes.values():
                if "interface" in code or "type" in code:
                    score += 5
                if "export" in code:
                    score += 5
                if "// " in code or "/* " in code:  # Comments
                    score += 5
                if "try" in code and "catch" in code:  # Error handling
                    score += 5

        # Test files quality (25 points)
        if test_files:
            score += 15  # Base points for having tests

            for test_code in test_files.values():
                if "describe" in test_code and "it(" in test_code:
                    score += 5
                if "expect" in test_code:
                    score += 5

        # Conversation quality (15 points)
        if len(conversation) >= 5:
            score += 10  # Good collaboration
        if len(conversation) >= 10:
            score += 5  # Excellent collaboration

        return min(score, max_score)

    def _format_conversations(self, conversation_history: list) -> list[dict]:
        """Format conversation history for output"""

        return [
            {
                "agent": message.get("name", "Unknown"),
                "content": message.get("content", ""),
                "timestamp": datetime.now().isoformat(),
            }
            for message in conversation_history
        ]


# Entry point for AutoPR
def run(inputs_dict: dict) -> dict:
    """AutoPR entry point"""
    inputs = AutoGenInputs(**inputs_dict)
    implementation = AutoGenImplementation()
    outputs = implementation.execute_multi_agent_task(inputs)
    return outputs.dict()


if __name__ == "__main__":
    # Test the action
    sample_inputs = {
        "task_description": "Add user role-based access control to the dashboard components",
        "task_type": "feature_development",
        "repository": "my-org/my-repo",
        "file_paths": ["src/components/Dashboard.tsx", "src/types/User.ts"],
        "requirements": {
            "roles": ["admin", "user", "viewer"],
            "permissions": ["read", "write", "admin"],
            "component_protection": True,
            "route_protection": True,
        },
        "complexity_level": "medium",
    }

    result = run(sample_inputs)
