"""
Code Quality Agent for AutoPR.

This module provides the CodeQualityAgent class which is responsible for analyzing
and improving code quality based on various metrics and best practices.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from crewai import Agent as CrewAgent

from autopr.agents.base import BaseAgent, VolumeConfig
from autopr.actions.llm import get_llm_provider_manager
from autopr.actions.quality_engine import QualityMode
from autopr.actions.quality_engine.volume_mapping import get_volume_config


@dataclass
class CodeQualityInputs:
    """Inputs for the CodeQualityAgent.
    
    Attributes:
        code: The code to analyze
        file_path: Path to the file containing the code
        language: Programming language of the code
        context: Additional context for the analysis
    """
    code: str
    file_path: str
    language: str
    context: Dict[str, Any] = None


@dataclass
class CodeQualityOutputs:
    """Outputs from the CodeQualityAgent.
    
    Attributes:
        issues: List of code quality issues found
        score: Overall quality score (0-100)
        metrics: Dictionary of quality metrics
        suggestions: List of improvement suggestions
    """
    issues: List[Dict[str, Any]]
    score: float
    metrics: Dict[str, Any]
    suggestions: List[str]


class CodeQualityAgent(BaseAgent[CodeQualityInputs, CodeQualityOutputs]):
    """Agent for analyzing and improving code quality.
    
    This agent analyzes code for quality issues, provides a quality score,
    and suggests improvements based on best practices and coding standards.
    """
    
    def __init__(
        self,
        volume: int = 500,  # Default to moderate level (500/1000)
        verbose: bool = False,
        allow_delegation: bool = False,
        max_iter: int = 3,
        max_rpm: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        """Initialize the CodeQualityAgent.
        
        Args:
            volume: Volume level (0-1000) for quality control
            verbose: Whether to enable verbose logging
            allow_delegation: Whether to allow task delegation
            max_iter: Maximum number of iterations for the agent
            max_rpm: Maximum requests per minute for the agent
            **kwargs: Additional keyword arguments passed to the base class
        """
        super().__init__(
            name="Code Quality Analyst",
            role="Analyze and improve code quality by identifying issues and suggesting improvements.",
            backstory=(
                "You are a meticulous code quality analyst with deep knowledge of "
                "software engineering best practices, design patterns, and code smells. "
                "Your goal is to help developers write clean, maintainable, and efficient code."
            ),
            volume=volume,
            verbose=verbose,
            allow_delegation=allow_delegation,
            max_iter=max_iter,
            max_rpm=max_rpm,
            **kwargs
        )
    
    async def _execute(self, inputs: CodeQualityInputs) -> CodeQualityOutputs:
        """Analyze code quality and provide improvement suggestions.
        
        Args:
            inputs: The input data for the agent
            
        Returns:
            CodeQualityOutputs containing analysis results and suggestions
        """
        # Get volume-based configuration
        volume_config = self.volume_config.config or {}
        
        # Prepare the prompt for the LLM
        prompt = self._build_prompt(inputs, volume_config)
        
        try:
            # Get response from the LLM
            response = await self.llm_provider.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Lower temperature for more deterministic output
                max_tokens=2000,
            )
            
            # Parse the response
            result = self._parse_response(response.choices[0].message.content)
            
            return CodeQualityOutputs(
                issues=result.get("issues", []),
                score=result.get("score", 0.0),
                metrics=result.get("metrics", {}),
                suggestions=result.get("suggestions", []),
            )
            
        except Exception as e:
            # Log the error and return a default response
            if self.verbose:
                print(f"Error in CodeQualityAgent: {str(e)}")
            
            return CodeQualityOutputs(
                issues=[{"message": f"Error analyzing code: {str(e)}", "severity": "error"}],
                score=0.0,
                metrics={"error": str(e)},
                suggestions=["Failed to analyze code quality due to an error."],
            )
    
    def _build_prompt(self, inputs: CodeQualityInputs, config: Dict[str, Any]) -> str:
        """Build the prompt for the LLM based on inputs and configuration.
        
        Args:
            inputs: The input data for the agent
            config: Volume-based configuration
            
        Returns:
            The formatted prompt string
        """
        # Get the quality mode name for the prompt
        quality_mode = self.volume_config.quality_mode or QualityMode.STANDARD
        
        return f"""
        Analyze the following code for quality issues and provide improvement suggestions.
        
        File: {inputs.file_path}
        Language: {inputs.language}
        Quality Mode: {quality_mode.name}
        
        Code:
        ```{inputs.language}
        {inputs.code}
        ```
        
        Context: {inputs.context or 'No additional context provided.'}
        
        Please provide a detailed analysis including:
        1. A list of code quality issues with severity levels
        2. An overall quality score (0-100)
        3. Key quality metrics (complexity, maintainability, etc.)
        4. Specific suggestions for improvement
        
        Format your response as a JSON object with the following structure:
        {{
            "issues": [
                {{
                    "message": "Description of the issue",
                    "severity": "error|warning|info",
                    "line": 123,
                    "column": 45,
                    "rule_id": "rule-identifier"
                }}
            ],
            "score": 85.5,
            "metrics": {{
                "complexity": 12,
                "maintainability_index": 78.5,
                "duplication": 5.2
            }},
            "suggestions": [
                "Specific suggestion 1",
                "Specific suggestion 2"
            ]
        }}
        """
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured format.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            A dictionary containing the parsed response
            
        Raises:
            ValueError: If the response cannot be parsed
        """
        import json
        from json import JSONDecodeError
        
        try:
            # Try to parse the response as JSON
            result = json.loads(response.strip())
            
            # Validate the response structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a JSON object")
                
            # Ensure required fields exist
            if "issues" not in result:
                result["issues"] = []
            if "score" not in result:
                result["score"] = 0.0
            if "metrics" not in result or not isinstance(result["metrics"], dict):
                result["metrics"] = {}
            if "suggestions" not in result:
                result["suggestions"] = []
                
            return result
            
        except JSONDecodeError as e:
            # If JSON parsing fails, return a default response with the error
            return {
                "issues": [{
                    "message": f"Failed to parse LLM response: {str(e)}",
                    "severity": "error"
                }],
                "score": 0.0,
                "metrics": {"error": "Response parsing failed"},
                "suggestions": ["The code quality analysis could not be completed due to a parsing error."],
            }
