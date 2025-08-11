"""Minimal test script to verify AutoPRCrew import."""
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Python path:")
for p in sys.path:
    print(f"  {p}")

print("\nAttempting to import AutoPRCrew...")
try:
    from autopr.agents.crew import AutoPRCrew
    print("✅ Successfully imported AutoPRCrew")
    print(f"AutoPRCrew class: {AutoPRCrew}")

    # Create a mock LLM provider manager
    class MockLLMProviderManager:
        def get_provider(self, provider_name):
            class MockProvider:
                def complete(self, request):
                    return None
            return MockProvider()

        def complete(self, request):
            return None

    # Patch the get_llm_provider_manager function
    import autopr.agents.crew as crew_module
    original_get_llm = crew_module.get_llm_provider_manager
    crew_module.get_llm_provider_manager = MockLLMProviderManager

    try:
        # Try to create an instance of AutoPRCrew
        print("\nCreating AutoPRCrew instance...")
        crew = AutoPRCrew()
        print(f"✅ Successfully created AutoPRCrew instance: {crew}")
    except Exception as e:
        print(f"❌ Failed to create AutoPRCrew instance: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore the original function
        crew_module.get_llm_provider_manager = original_get_llm

except Exception as e:
    print(f"❌ Failed to import AutoPRCrew: {e}")
    import traceback
    traceback.print_exc()

print("\nScript completed.")
