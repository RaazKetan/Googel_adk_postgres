import asyncio
import time
import logging
from typing import Any, Dict, Optional

from google.adk.runners import Runner
from google.genai import types as genai_types

# Local imports from adk_config to access constants
from core.adk_config import APP_NAME_FOR_ADK, USER_ID

async def run_adk_async(runner: Runner, session_id: str, user_message_text: str) -> str:
    """
    Asynchronously executes one turn of the ADK agent conversation.

    Args:
        runner: The initialized ADK Runner.
        session_id: The current ADK session ID.
        user_message_text: The text input from the user for this turn.

    Returns:
        The agent's final text response as a string.
    """
    print(f"\n--- ADK Run: Starting async execution for session {session_id} ---")
    print(f"--- ADK Run: Processing User Query (truncated): '{user_message_text[:150]}...' ---")

    # Retrieve the ADK session object to update its state
    session = await runner.session_service.get_session(app_name=APP_NAME_FOR_ADK, user_id=USER_ID, session_id=session_id)
    if not session:
        return "Error: ADK session not found. Please refresh the page."

    print(f"--- ADK Run: Session state BEFORE agent run: {session.state} ---")
    # No direct update from Streamlit inputs needed here as it's handled by ADK internally based on messages
    print(f"--- ADK Run: ADK session state is managed by the runner. ---")

    # Format the user's message for the ADK runner
    content = genai_types.Content(
        role='user',
        parts=[genai_types.Part(text=user_message_text)]
    )
    final_response_text = "[Agent encountered an issue and did not produce a final response]"
    start_time = time.time() # Start timing

    try:
        async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=content):
            if event.is_final_response():
                print(f"--- ADK Run: Final response event received. ---")
                # Extract text from the final response event
                if event.content and event.content.parts and hasattr(event.content.parts[0], 'text'):
                    final_response_text = event.content.parts[0].text
                else:
                    final_response_text = "[Agent finished but produced no text output]"
                    print(f"--- ADK Run: WARNING - Final event received, but no text content found. Event: {event} ---")
                break # Stop iterating after the final response
    except Exception as e:
        print(f"--- ADK Run: !! EXCEPTION during agent execution: {e} !! ---")
        logging.exception("ADK runner.run_async failed:")
        final_response_text = f"Sorry, an error occurred while processing your request: {e}"

    end_time = time.time()
    duration = end_time - start_time
    print(f"--- ADK Run: Turn execution completed in {duration:.2f} seconds. ---")
    print(f"--- ADK Run: Final Response (truncated): '{final_response_text[:150]}...' ---")
    return final_response_text

def run_adk_sync(runner: Runner, session_id: str, user_message_text: str) -> str:
    """
    Synchronous wrapper that executes the asynchronous run_adk_async function.
    """
    return asyncio.run(run_adk_async(runner, session_id, user_message_text))

print("ADK Utilities: run_adk_async and run_adk_sync functions defined.")