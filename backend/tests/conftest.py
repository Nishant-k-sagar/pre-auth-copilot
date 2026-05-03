"""
Shared pytest fixtures.

load_dotenv() is called here before any skill imports.
This is what makes the lazy pipeline client safe in tests:
MISTRAL_API_KEY is in os.environ before _get_client() is first called.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Must be before any skill imports

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import types for type annotations
from skill.schema import PreAuthCaseInput, PreAuthSkillOutput  # noqa: E402


def run_pipeline_sync(case_input: PreAuthCaseInput) -> PreAuthSkillOutput:
    """Run the async pipeline synchronously for pytest sync fixtures."""
    from skill.pipeline import run_pipeline
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop is not None:
        # If an event loop is already running, use nest_asyncio or run in executor
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run, 
                run_pipeline(case_input)
            )
            return future.result()
    else:
        return asyncio.run(run_pipeline(case_input))