"""
AutoPR Action: Mem0 Memory Integration
Advanced memory system using Mem0 for persistent, intelligent memory across interactions.
"""

import os
from datetime import datetime
from typing import Any

from pydantic import BaseModel

try:
    from mem0 import Memory

    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False


class Mem0MemoryInputs(BaseModel):
    action_type: str  # "add_memory", "search_memory", "get_insights", "update_memory"
    user_id: str | None = None
    agent_id: str = "autopr_agent"
    memory_content: str | None = None
    metadata: dict[str, Any] = {}
    query: str | None = None
    memory_id: str | None = None


class Mem0MemoryOutputs(BaseModel):
    success: bool
    memories: list[dict[str, Any]] = []
    insights: list[str] = []
    memory_id: str | None = None
    relevance_scores: dict[str, float] = {}
    error_message: str | None = None


class Mem0MemoryManager:
    def __init__(self) -> None:
        if not MEM0_AVAILABLE:
            msg = "Mem0 not installed. Install with: pip install mem0ai"
            raise ImportError(msg)

        # Initialize Mem0 with configuration
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": os.getenv("QDRANT_HOST", "localhost"),
                    "port": int(os.getenv("QDRANT_PORT", "6333")),
                    "api_key": os.getenv("QDRANT_API_KEY"),
                },
            },
            "llm": {
                "provider": os.getenv("MEM0_LLM_PROVIDER", "openai"),
                "config": {
                    "model": os.getenv("MEM0_LLM_MODEL", "gpt-4"),
                    "api_key": os.getenv("OPENAI_API_KEY"),
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                },
            },
        }

        self.memory = Memory.from_config(config)

    def add_memory(self, inputs: Mem0MemoryInputs) -> Mem0MemoryOutputs:
        """Add a new memory to the system."""
        try:
            # Enhanced metadata with AutoPR context
            enhanced_metadata = {
                **inputs.metadata,
                "timestamp": datetime.now().isoformat(),
                "source": "autopr",
                "agent_id": inputs.agent_id,
                "memory_type": inputs.metadata.get("memory_type", "general"),
            }

            # Add memory with user context
            result = self.memory.add(
                messages=inputs.memory_content,
                user_id=inputs.user_id,
                agent_id=inputs.agent_id,
                metadata=enhanced_metadata,
            )

            return Mem0MemoryOutputs(
                success=True,
                memory_id=result.get("id"),
                memories=[
                    {
                        "id": result.get("id"),
                        "content": inputs.memory_content,
                        "metadata": enhanced_metadata,
                    }
                ],
            )

        except Exception as e:
            return Mem0MemoryOutputs(success=False, error_message=f"Failed to add memory: {e!s}")

    def search_memory(self, inputs: Mem0MemoryInputs) -> Mem0MemoryOutputs:
        """Search for relevant memories based on query."""
        try:
            # Search memories with context filters
            results = self.memory.search(
                query=inputs.query,
                user_id=inputs.user_id,
                agent_id=inputs.agent_id,
                limit=10,
            )

            memories = []
            relevance_scores = {}

            for result in results:
                memory_data = {
                    "id": result["id"],
                    "content": result["memory"],
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0),
                    "created_at": result.get("created_at"),
                    "updated_at": result.get("updated_at"),
                }
                memories.append(memory_data)
                relevance_scores[result["id"]] = result.get("score", 0.0)

            return Mem0MemoryOutputs(
                success=True, memories=memories, relevance_scores=relevance_scores
            )

        except Exception as e:
            return Mem0MemoryOutputs(
                success=False, error_message=f"Failed to search memories: {e!s}"
            )

    def get_insights(self, inputs: Mem0MemoryInputs) -> Mem0MemoryOutputs:
        """Get AI-generated insights from stored memories."""
        try:
            # Get all memories for the user/agent
            all_memories = self.memory.get_all(user_id=inputs.user_id, agent_id=inputs.agent_id)

            # Generate insights using Mem0's built-in analysis
            insights = []

            # Analyze patterns in fix types
            fix_memories = [
                m for m in all_memories if m.get("metadata", {}).get("memory_type") == "fix_pattern"
            ]
            if fix_memories:
                insights.append(f"You have applied {len(fix_memories)} automated fixes")

                # Most common fix types
                fix_types = [m.get("metadata", {}).get("fix_type", "") for m in fix_memories]
                if fix_types:
                    most_common = max(set(fix_types), key=fix_types.count)
                    insights.append(f"Most common fix type: {most_common}")

            # Analyze user preferences
            pref_memories = [
                m
                for m in all_memories
                if m.get("metadata", {}).get("memory_type") == "user_preference"
            ]
            if pref_memories:
                insights.append(f"Learned {len(pref_memories)} user preferences")

            # Project-specific insights
            project_memories = [
                m
                for m in all_memories
                if m.get("metadata", {}).get("memory_type") == "project_context"
            ]
            if project_memories:
                insights.append(f"Analyzed {len(project_memories)} project patterns")

            return Mem0MemoryOutputs(success=True, insights=insights, memories=all_memories)

        except Exception as e:
            return Mem0MemoryOutputs(success=False, error_message=f"Failed to get insights: {e!s}")

    def update_memory(self, inputs: Mem0MemoryInputs) -> Mem0MemoryOutputs:
        """Update an existing memory."""
        try:
            self.memory.update(
                memory_id=inputs.memory_id,
                data=inputs.memory_content,
                user_id=inputs.user_id,
                agent_id=inputs.agent_id,
            )

            return Mem0MemoryOutputs(
                success=True,
                memory_id=inputs.memory_id,
                memories=[
                    {
                        "id": inputs.memory_id,
                        "content": inputs.memory_content,
                        "updated": True,
                    }
                ],
            )

        except Exception as e:
            return Mem0MemoryOutputs(success=False, error_message=f"Failed to update memory: {e!s}")

    def record_fix_pattern(
        self,
        comment_type: str,
        fix_type: str,
        success: bool,
        user_id: str,
        context: dict[str, Any],
    ) -> bool:
        """Record a fix pattern for future learning."""
        memory_content = f"Applied {fix_type} fix for {comment_type} comment with {'success' if success else 'failure'}"

        inputs = Mem0MemoryInputs(
            action_type="add_memory",
            user_id=user_id,
            memory_content=memory_content,
            metadata={
                "memory_type": "fix_pattern",
                "comment_type": comment_type,
                "fix_type": fix_type,
                "success": success,
                "context": context,
            },
        )

        result = self.add_memory(inputs)
        return result.success

    def record_user_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: str,
        context: dict[str, Any],
    ) -> bool:
        """Record user preferences for personalized interactions."""
        memory_content = f"User {user_id} prefers {preference_value} for {preference_type}"

        inputs = Mem0MemoryInputs(
            action_type="add_memory",
            user_id=user_id,
            memory_content=memory_content,
            metadata={
                "memory_type": "user_preference",
                "preference_type": preference_type,
                "preference_value": preference_value,
                "context": context,
            },
        )

        result = self.add_memory(inputs)
        return result.success

    def get_relevant_patterns(
        self, comment_type: str, file_path: str, user_id: str
    ) -> list[dict[str, Any]]:
        """Get relevant fix patterns based on context."""
        query = (
            f"fix patterns for {comment_type} comments in {os.path.splitext(file_path)[1]} files"
        )

        inputs = Mem0MemoryInputs(action_type="search_memory", user_id=user_id, query=query)

        result = self.search_memory(inputs)

        if result.success:
            # Filter for fix patterns
            return [
                m
                for m in result.memories
                if m.get("metadata", {}).get("memory_type") == "fix_pattern"
            ]

        return []


def mem0_memory_action(inputs: Mem0MemoryInputs) -> Mem0MemoryOutputs:
    """Main action interface for Mem0 memory system."""
    if not MEM0_AVAILABLE:
        return Mem0MemoryOutputs(
            success=False,
            error_message="Mem0 not available. Install with: pip install mem0ai",
        )

    try:
        manager = Mem0MemoryManager()

        if inputs.action_type == "add_memory":
            return manager.add_memory(inputs)
        if inputs.action_type == "search_memory":
            return manager.search_memory(inputs)
        if inputs.action_type == "get_insights":
            return manager.get_insights(inputs)
        if inputs.action_type == "update_memory":
            return manager.update_memory(inputs)
        return Mem0MemoryOutputs(
            success=False,
            error_message=f"Unknown action type: {inputs.action_type}",
        )

    except Exception as e:
        return Mem0MemoryOutputs(success=False, error_message=f"Mem0 operation failed: {e!s}")
