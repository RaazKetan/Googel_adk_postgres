import os
import asyncio
import time
import logging
from decimal import Decimal # Ensure Decimal is imported
from typing import Any, Dict

import streamlit as st
from dotenv import load_dotenv

# Google ADK Components
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext
from google.genai import types as genai_types

# Local import for database operations
from core.db_operations import get_connection

# Load environment variables from .env file
load_dotenv()
# Configure logging to suppress most ADK internal logs, showing only errors
logging.basicConfig(level=logging.ERROR)

# Constants
MODEL_GEMINI = os.environ.get("MODEL_GEMINI", "gemini-1.5-pro") # Allow overriding via .env
APP_NAME_FOR_ADK = "greeting_app"
USER_ID = "ketanraj" # Consider making this dynamic in a real app

print("ADK Configuration: Constants defined and .env loaded.")

# --------------------------------------------------------------------
# ADK Tool: run_sql_query
# --------------------------------------------------------------------
def run_sql_query(tool_context: ToolContext, query: str) -> Dict[str, Any]:
    """
    Executes an arbitrary SQL query and returns the result or status.

    Args:
        tool_context (ToolContext): ADK tool context.
        query (str): SQL query to execute.

    Returns:
        Dict[str, Any]: Success/error and data if available.
    """
    print(f"--- SQL Query Execution: Running query: {query} ---")

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(query)
            if cur.description: # Select query
                columns = [desc[0] for desc in cur.description]

                def convert_value(value):
                    """Converts Decimal objects to float, otherwise returns value as is."""
                    if isinstance(value, Decimal):
                        return float(value)
                    return value

                def convert_row(row):
                    """Converts a database row into a dictionary with JSON-serializable values."""
                    return {
                        col: convert_value(val)
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


# --------------------------------------------------------------------
# ADK Agent Definition
# --------------------------------------------------------------------
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
print("ADK Configuration: root_agent defined with run_sql_query tool.")

# --------------------------------------------------------------------
# ADK Session and Runner Setup
# --------------------------------------------------------------------
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
        if not asyncio.run(session_service.get_session(app_name=APP_NAME_FOR_ADK, user_id=USER_ID, session_id=session_id)):
            print(f"--- ADK Init: WARNING - Session {session_id} not found in InMemorySessionService memory (likely due to script restart). Recreating session. State will be lost. ---")
            try:
                asyncio.run(session_service.create_session(
                    app_name=APP_NAME_FOR_ADK,
                    user_id=USER_ID,
                    session_id=session_id,
                    state={}# Recreated session starts with empty state
                ))
            except Exception as e:
                print(f"--- ADK Init: ERROR - Could not recreate missing session {session_id} in ADK SessionService: {e} ---")
                logging.exception("ADK Session Service recreation failed:")

    print(f"--- ADK Init: Initialization sequence complete. Runner is ready. Active Session ID: {session_id} ---")
    return runner, session_id

print("ADK Configuration: Runner initialization functions defined.")