import streamlit as st
import logging
import os

# Local imports
from core.adk_config import APP_NAME_FOR_ADK, USER_ID, MODEL_GEMINI # Import constants for debug info
from core.adk_utils import run_adk_sync

def setup_page_config():
    """Sets up the Streamlit page configuration."""
    st.set_page_config(
        page_title="Employee Information Assistant",
        layout="wide",
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

def display_header():
    """Displays the main header and introductory text."""
    st.markdown('<div class="title">🤖 Employee Skill Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Ask me to add, update, delete, or view employee skills</div>', unsafe_allow_html=True)
    st.markdown("""
        This application uses the Google Agent Development Kit (ADK) to provide a chat interface
        for managing employee skills in a PostgreSQL database.
    """)

def display_chat_interface(adk_runner, current_session_id):
    """
    Implements the core chat interface for user interaction.

    Args:
        adk_runner: The initialized ADK Runner instance.
        current_session_id: The current ADK session ID.
    """
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

print("Streamlit UI: Page config, header, and chat interface functions defined.")