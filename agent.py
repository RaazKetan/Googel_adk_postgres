import os
import asyncio
from typing import Any, Dict, Optional
import streamlit as st
import time
import logging
import pandas as pd
import json

from dotenv import load_dotenv
from db import get_connection

# Google ADK Components
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types as genai_types
from decimal import Decimal

# Load environment variables from .env file
load_dotenv()
# Configure logging to suppress most ADK internal logs, showing only errors
logging.basicConfig(level=logging.ERROR)

# Constants
GREETING_FETCH_CACHE_STATE_KEY = "greeting_fetch_cache_state"
MODEL_GEMINI = "gemini-2.5-flash"
APP_NAME_FOR_ADK= "greeting_app"
USER_ID = "ketanraj" # Consider making this dynamic in a real app

print("Imports and Configuration done")
#--------------------------------------------------------------------
# Add Employee 
#--------------------------------------------------------------------
def run_sql_query(tool_context: ToolContext, query: str) -> Dict[str, Any]:
    """
    Executes an arbitrary SQL query an returns the result or status

    Args:
        tool_context (ToolContext): ADK tool context.
        query (str): SQL query to execute.

    Returns:
        Dict[str, Any]: Success/error and data if available.
    """
    print(f"--- SQL Query Execution: Running query: {query} ---")
    
    try: 
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(query)
            if cur.description: # Select query
                columns = [desc[0] for desc in cur.description]
                
                def convert_row(row):
                    return {
                    col: float(val) if isinstance(val, Decimal) else val 
                    for col, val in zip(columns, row)
                }
                rows = cur.fetchall()
                result = [convert_row(row) for row in rows]
                return {"status": "success", "results": result}
            else:
                conn.commit()
                return {"status": "success", "message": f"{cur.rowcount} rows affected."}
    except Exception as e:
        print(f"--- SQL Query Execution: Error executing query: {e} ---")
        logging.exception("SQL query execution failed:")
        return {"status": "error", "message": str(e)}
    finally:
        if conn:
            conn.close()
            print("--- SQL Query Execution: Database connection closed ---")
#--------------------------------------------------------------------
                
# Complete root_agent definition
root_agent = LlmAgent(
    name="greeting_agent",
    model=MODEL_GEMINI,
    description="An agent to manage employee data and skills in a PostgreSQL database.",
    instruction="""
You help manage employee data in a PostgreSQL database using a single tool: 'run_sql_query'.
Be concise and clear in your responses.

Use 'run_sql_query' to:
- Insert new employees and their skills.
- Update existing employee skills (but NOT the name).
- Delete employees by name.
- Query employees and their tech stack.

Database schema:
1. employees(id SERIAL PRIMARY KEY, name TEXT NOT NULL)
2. employee_skills(id SERIAL PRIMARY KEY, employee_id INT REFERENCES employees(id), tech TEXT NOT NULL, experience_years NUMERIC NOT NULL)

Example logic:
- Add: INSERT into employees, then insert into employee_skills
- Update: Use employee name to get id, then UPDATE employee_skills
- Delete: DELETE FROM employees WHERE name = '...'
- Query: SELECT ... JOIN ...
- Search: Search employee_skills, employee for tech and experience
    - If employee does not exist, return a friendly message.
    - If employee exists, return their skills and experience.
    - If employee has no skills, return a message indicating that.
    - If employee has no experience, return a message indicating that.
    - If employee has no tech stack, return a message indicating that.

If required data is missing (like experience or tech stack), ask the user for it first.

Be cautious, never assume data structure. Always fetch `employee_id` by name before modifying `employee_skills`.
Refer to the Employee table first to get the `employee_id` for any operations on `employee_skills`.
if not then go to employee_skills table to get the employee_id.
Always return results in a clean, user-friendly format.
If the query is not understood, respond with "I don't know how to do that." and  ask for clarification.
Do not attempt to do anything outside of the database operations described above.
""",
    tools=[run_sql_query],
)
# ADK Session and Runner Setup

@st.cache_resource
def initialize_adk():
    """
    Initializes the ADK Runner and InMemorySessionService for the application.
    Manages the unique ADK session ID within the Streamlit session state.

    Returns:
        tuple: (Runner instance, active ADK session ID)
    """
    print("--- ADK Init: Attempting to initialize Runner and Session Service... ---")
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME_FOR_ADK,
        session_service = session_service
    )
    print("--- ADK Init: Runner and Session Service initialized successfully ---")

    adk_session_key  = "adk_session_id"
    if adk_session_key not in st.session_state:
        session_id = f"streamlit_adk_session_{int(time.time())}_{os.urandom(4).hex()}"
        st.session_state[adk_session_key] = session_id
        print(f"--- ADK Init: Created new session with ID: {st.session_state[adk_session_key]} ---")
        try:
            # Create the initial session record within the ADK session service
            asyncio.run(session_service.create_session(
                app_name=APP_NAME_FOR_ADK,
                user_id=USER_ID,
                session_id=session_id,
                state={}
                ))
            print(f"--- ADK Init: Successfully created new session in ADK SessionService. ---")
        except Exception as e:
            print(f"--- ADK Init: FATAL ERROR - Could not create initial session in ADK SessionService: {e} ---")
            logging.exception("ADK Session Service create_session failed:")
            raise # Re-raise to stop app if session can't be created
    else:
        session_id = st.session_state[adk_session_key]
        print(f"--- ADK Init: Reusing existing ADK session ID from Streamlit state: {session_id} ---")
        # For InMemorySessionService, check if session actually exists (might be lost on script restart)
        if not session_service.get_session(app_name=APP_NAME_FOR_ADK, user_id=USER_ID, session_id=session_id):
            print(f"--- ADK Init: WARNING - Session {session_id} not found in InMemorySessionService memory (likely due to script restart). Recreating session. State will be lost. ---")
            try:
                session_service.create_session(
                    app_name=APP_NAME_FOR_ADK,
                    user_id=USER_ID,
                    session_id=session_id,
                    state={}# Recreated session starts with empty state
                )
            except Exception as e:
                print(f"--- ADK Init: ERROR - Could not recreate missing session {session_id} in ADK SessionService: {e} ---")
                logging.exception("ADK Session Service recreation failed:")

    print(f"--- ADK Init: Initialization sequence complete. Runner is ready. Active Session ID: {session_id} ---")
    return runner, session_id

async def run_adk_async(runner:Runner, session_id:str, user_message_text:str)-> str:
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
    print(f"--- ADK Run: Updated ADK session state with Streamlit inputs: {session.state} ---")

    # Format the user's message for the ADK runner
    content = genai_types.Content(
        role='user',
        parts=[genai_types.Part(text=user_message_text)]
    )
    final_response_text = "[Agent encountered an issue and did not produce a final response]"
    start_time = time.time() # Start timing

    try:
        async for event in runner.run_async(user_id=USER_ID, session_id = session_id, new_message=content):
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

print("âœ… ADK Runner initialization and helper functions defined.")

# Streamlit User Interface Setup

st.set_page_config(
    page_title=" Employee Information Assistant",
    layout="wide",
    initial_sidebar_state="collapsed" # Ensure sidebar is collapsed by default
)
st.title("👨🏼‍🚀 Greeting & Chat Assistant (Powered by ADK & Gemini)")
st.markdown("""
    This application uses the Google Agent Development Kit (ADK) to provide a chat interface
    for greeting you and allowing general chat.
    \n\n
    **Note:** Ensure you have set up your Google API key correctly in the .env file to use this application.
""")
st.divider()
# --- API Key Availability Check ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key or "YOUR_GOOGLE_API_KEY" in api_key:
    st.error(
        "**Action Required: Google API Key Not Found or Invalid!** \n\n"
        "1. Create a file named .env in the same directory as your script.\n"
        "2. Add the following line to the .env file:\n"
        "   GOOGLE_API_KEY='YOUR_ACTUAL_GEMINI_API_KEY'\n"
        "3. Replace YOUR_ACTUAL_GEMINI_API_KEY with your valid key from Google AI Studio.\n"
        "4. **Restart the Streamlit application.**",
        icon="☢️"
    )
    st.stop() # Halt further execution if key is missing/invalid


# --- Initialize ADK Runner and Session ---
try:
    adk_runner, current_session_id = initialize_adk()
except Exception as e:
    st.error(f"**Fatal Error:** Could not initialize the ADK Runner or Session Service: {e}", icon="👀")
    st.error("Please check the terminal logs for more details, ensure your API key is valid (if used), and restart the application.")
    logging.exception("Critical ADK Initialization failed in Streamlit UI context.")
    st.stop() # Stop the app if ADK fails to initialize

st.divider()

# --- Chat Interface Implementation ---
st.set_page_config(
    page_title="Employee Skill Manager",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    .main { background-color: #f5f7fa; }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: #374151;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #6b7280;
    }
    .chat-box {
        padding: 1rem;
        border-radius: 1rem;
        background: white;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">🤖 Employee Skill Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask me to add, update, delete, or view employee skills</div>', unsafe_allow_html=True)
st.divider()

# Initialize ADK
try:
    adk_runner, current_session_id = initialize_adk()
except Exception as e:
    st.error("❌ Failed to initialize ADK. Check logs.")
    logging.exception(e)
    st.stop()

# Initialize chat history
message_key = "chat_history_employee_assistant"
if message_key not in st.session_state:
    st.session_state[message_key] = []

# Display messages
for msg in st.session_state[message_key]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Single input for user
if user_prompt := st.chat_input("Try: Add John with 2 years React and 1 year Python"):
    st.chat_message("user").markdown(user_prompt)
    st.session_state[message_key].append({"role": "user", "content": user_prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent_response = run_adk_sync(adk_runner, current_session_id, user_prompt)
                st.markdown(agent_response)
            except Exception as e:
                error_msg = f"⚠️ Error: {e}"
                st.error(error_msg)
                agent_response = error_msg
                logging.exception(e)

    st.session_state[message_key].append({"role": "assistant", "content": agent_response})

# View employee table
st.divider()
# Debug Info
with st.expander("🛠️ Debug Info"):
    st.caption(f"Session ID: `{current_session_id}`")
    st.caption(f"Model: `{os.environ.get('MODEL_GEMINI', 'gemini-2.5-flash')}`")
    st.caption("App: `employee_skill_manager`")
