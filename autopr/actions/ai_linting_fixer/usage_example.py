"""
Usage Example: Modular AI Fix Applier

Demonstrates how to use the new modular system following SOLID principles.
"""

import asyncio

from autopr.actions.ai_linting_fixer import (
    AIFixApplier,
    FilePersistenceManager,
    LLMClient,
    ResponseParser,
    StrategySelector,
)
from autopr.actions.ai_linting_fixer.backup_manager import BackupManager
from autopr.actions.ai_linting_fixer.validation_manager import ValidationConfig
from autopr.ai.providers.manager import LLMProviderManager


async def example_usage():
    """Example showing how to use the modular system."""
    
    # Initialize LLM manager (mock for example)
    llm_manager = LLMProviderManager()  # Would be properly configured
    
    # Option 1: Use the simplified coordinator (recommended)
    applier = AIFixApplier(
        llm_manager=llm_manager,
        backup_manager=BackupManager(),
        validation_config=ValidationConfig(),
    )
    
    # Apply fix with validation (high-level interface)
    # result = await applier.apply_specialist_fix_with_validation(
    #     agent=agent,
    #     file_path="example.py", 
    #     content="print('hello')",
    #     issues=[issue],
    #     session_id="session_123"
    # )
    
    # Option 2: Use specific strategy
    # result = await applier.apply_fix_with_strategy(
    #     strategy_name="validation",
    #     agent=agent,
    #     file_path="example.py",
    #     content="print('hello')",
    #     issues=[issue],
    # )
    
    # Option 3: Use components directly for custom workflows
    llm_client = applier.get_llm_client()
    parser = applier.get_response_parser()
    persistence = applier.get_persistence_manager()
    
    # Custom workflow example:
    # request = llm_client.create_request("System prompt", "User prompt")
    # response = await llm_client.complete(request)
    # code = parser.extract_code_from_response(response.content)
    # result = await persistence.persist_fix("file.py", code)
    
    print("✓ Modular system initialized successfully")


def benefits_of_modular_design():
    """
    Benefits of the new modular design:
    
    1. SINGLE RESPONSIBILITY PRINCIPLE:
       - LLMClient: Only handles LLM communication
       - FilePersistenceManager: Only handles file operations
       - ResponseParser: Only handles response parsing
       - FixStrategy: Only handles fix application logic
       
    2. OPEN/CLOSED PRINCIPLE:
       - Easy to add new strategies without modifying existing code
       - New response parsers can be added for different LLMs
       - Different persistence strategies can be implemented
       
    3. LISKOV SUBSTITUTION PRINCIPLE:
       - All strategies implement the same FixStrategy interface
       - Components can be swapped without breaking the system
       
    4. INTERFACE SEGREGATION PRINCIPLE:
       - Each component exposes only the methods it needs
       - No forced dependencies on unused functionality
       
    5. DEPENDENCY INVERSION PRINCIPLE:
       - High-level coordinator depends on abstractions
       - Components are injected rather than hardcoded
       
    6. DRY (DON'T REPEAT YOURSELF):
       - LLM communication logic centralized in LLMClient
       - File operations centralized in FilePersistenceManager
       - Response parsing logic centralized in ResponseParser
       
    7. MAINTAINABILITY:
       - Easier to test individual components
       - Easier to debug specific functionality  
       - Easier to modify without affecting other parts
       
    8. EXTENSIBILITY:
       - New strategies can be added easily
       - Components can be replaced with improved versions
       - Custom workflows can be built using individual components
    """
    pass


if __name__ == "__main__":
    asyncio.run(example_usage())
