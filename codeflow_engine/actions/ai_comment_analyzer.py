"""
AutoPR Action: AI Comment Analyzer.

Uses LLM to analyze PR comments and generate intelligent responses and fixes.
"""

import json
import os
from typing import Any

import openai
from pydantic import BaseModel, Field

from codeflow_engine.actions.base import Action


class AICommentAnalysisInputs(BaseModel):
    comment_body: str
    file_path: str | None = None
    file_content: str | None = None
    surrounding_context: str | None = None
    pr_diff: str | None = None


class AICommentAnalysisOutputs(BaseModel):
    intent: str  # "fix_request", "question", "suggestion", "praise", "complex_issue"
    confidence: float
    suggested_actions: list[str] = Field(default_factory=list)
    auto_fixable: bool
    search_block: str | None = None
    replace_block: str | None = None
    response_template: str
    issue_priority: str  # "low", "medium", "high", "critical"
    tags: list[str] = Field(default_factory=list)


def analyze_comment_with_ai(
    inputs: AICommentAnalysisInputs,
) -> AICommentAnalysisOutputs:
    """Analyze PR comment and determine best response strategy using LLM."""

    # Set up OpenAI client (or use local LLM)
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_prompt = """
    You are an expert code reviewer and automation assistant. Analyze PR comments to determine:
    1. The intent and sentiment of the comment
    2. Whether it can be automatically fixed
    3. What actions should be taken
    4. Priority level
    5. Appropriate tags

    If the comment is a fix request, provide a `search_block` and a 
    `replace_block` for the fix.
    The `search_block` should be a small, unique snippet of code to 
    identify the location of the change.
    The `replace_block` should be the code that replaces the 
    `search_block`.

    Return JSON with analysis results.
    """

    file_content = ""
    if inputs.file_path and os.path.exists(inputs.file_path):
        with open(inputs.file_path, 'r') as f:
            file_content = f.read()

    user_prompt = f"""
    Analyze this PR comment:

    Comment: "{inputs.comment_body}"
    File: {inputs.file_path or "N/A"}

    File Content:
    {file_content[:5000]}

    PR Diff:
    {inputs.pr_diff}

    Determine:
    - Intent (fix_request, question, suggestion, praise, complex_issue)
    - Confidence (0.0-1.0)
    - Suggested actions
    - Whether it's auto-fixable
    - search_block (if applicable)
    - replace_block (if applicable)
    - Response template
    - Priority (low/medium/high/critical)
    - Relevant tags
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )

        # Parse AI response
        content = response.choices[0].message.content
        if content is None:
            return fallback_analysis(inputs)
        ai_analysis = json.loads(content)

        return AICommentAnalysisOutputs(**ai_analysis)

    except Exception:
        # Fallback to rule-based analysis
        return fallback_analysis(inputs)


def fallback_analysis(inputs: AICommentAnalysisInputs) -> AICommentAnalysisOutputs:
    """Fallback rule-based analysis if AI fails."""
    comment_lower = inputs.comment_body.lower()

    # Simple rule-based classification
    if any(word in comment_lower for word in ["fix", "remove", "change", "update"]):
        intent = "fix_request"
        auto_fixable = True
    elif any(word in comment_lower for word in ["?", "how", "why", "what"]):
        intent = "question"
        auto_fixable = False
    else:
        intent = "suggestion"
        auto_fixable = False

    return AICommentAnalysisOutputs(
        intent=intent,
        confidence=0.6,
        suggested_actions=["create_issue"],
        auto_fixable=auto_fixable,
        response_template="Thanks for the feedback! I'll look into this.",
        issue_priority="medium",
        tags=["needs-review"],
    )


class AICommentAnalyzer(Action[AICommentAnalysisInputs, AICommentAnalysisOutputs]):
    """Action for analyzing PR comments with AI."""

    def __init__(self) -> None:
        super().__init__(
            name="ai_comment_analyzer",
            description=(
                "Uses LLM to analyze PR comments and generate intelligent responses and fixes"
            ),
            version="1.0.0",
        )

    async def execute(
        self, inputs: AICommentAnalysisInputs, context: dict[str, Any]
    ) -> AICommentAnalysisOutputs:
        """Execute the AI comment analysis."""
        return analyze_comment_with_ai(inputs)
