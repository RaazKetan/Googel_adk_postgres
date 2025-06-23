import streamlit as st
import os
import logging

# Local imports
from core.adk_config import initialize_adk, root_agent, APP_NAME_FOR_ADK, USER_ID
from core.adk_utils import run_adk_sync
from ui.streamlit_ui import setup_page_config, display_header, display_chat_interface

# Configure logging
logging.basicConfig(level=logging.ERROR)

def main():
    """
    Main function to run the Streamlit Employee Skill Assistant application.
    """
    setup_page_config()
    display_header()
    st.divider()

    # --- API Key Availability Check (Re-added for clarity, but you can remove if handling differently) ---
    # api_key = os.environ.get("GOOGLE_API_KEY")
    # if not api_key or "YOUR_GOOGLE_API_KEY" in api_key:
    #     st.error(
    #         "**Action Required: Google API Key Not Found or Invalid!** \n\n"
    #         "1. Create a file named `.env` in the same directory as your script.\n"
    #         "2. Add the following line to the `.env` file:\n"
    #         "   `GOOGLE_API_KEY='YOUR_ACTUAL_GEMINI_API_KEY'`\n"
    #         "3. Replace `YOUR_ACTUAL_GEMINI_API_KEY` with your valid key from Google AI Studio.\n"
    #         "4. **Restart the Streamlit application.**",
    #         icon="⚠️"
    #     )
    #     st.stop() # Halt further execution if key is missing/invalid

    # --- Initialize ADK Runner and Session ---
    try:
        adk_runner, current_session_id = initialize_adk()
    except Exception as e:
        st.error(f"**Fatal Error:** Could not initialize the ADK Runner or Session Service: {e}", icon="🚨")
        st.error("Please check the terminal logs for more details, ensure your API key is valid (if used), and restart the application.")
        logging.exception("Critical ADK Initialization failed in Streamlit UI context.")
        st.divider()
        st.stop() # Stop the app if ADK fails to initialize

   

    # --- Chat Interface ---
    display_chat_interface(adk_runner, current_session_id)

    st.divider()
    # --- Debug Info ---
    with st.expander("🛠️ Debug Info"):
        st.caption(f"Session ID: `{current_session_id}`")
        st.caption(f"Model: `{os.environ.get('MODEL_GEMINI', 'gemini-1.5-pro')}`")
        st.caption("App Name for ADK: `greeting_app` (defined in adk_config.py)")
        st.caption("ADK Root Agent Name: `greeting_agent` (defined in adk_config.py)")


if __name__ == "__main__":
    main()