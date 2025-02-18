import streamlit as st
import os
import shutil
import logging


from components.header import render_header
from components.upload_chat import render_upload_chat
from components.history import render_history
from components.notes import render_notes
from utils.database import ConversationDB
from utils.query_engine import QueryEngine

# Configure logging and Streamlit page config
logging.basicConfig(level=logging.INFO)
st.set_page_config(
    page_title="DocuVerse",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get Help": "https://github.com/KPrince-coder/docuverse#readme",
        "Report a bug": "https://github.com/KPrince-coder/docuverse/issues",
        "About": "# DocuVerse\nYour Document Intelligence Assistant",
    },
)

# Load custom CSS for header, chat, and inline action buttons
with open("components/style.css", "r") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# Render the sticky header
render_header()

# Define available models
AVAILABLE_MODELS = [
    "mixtral-8x7b-32768",  # default
    "deepseek-r1-distill-llama-70b",
    "llama-3.3-70b-versatile",
    "llama-3.3-70b-specdec",
    "llama-3.2-1b-preview",
    "llama-3.2-3b-preview",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "llama-guard-3-8b",
    "gemma2-9b-it",
]

# Sidebar: API Key Management and Model Selection
st.sidebar.title("📚 DocuVerse")


# Function to partially mask the API key
def mask_api_key(api_key):
    if not api_key:
        return ""
    visible_part = api_key[:4]
    masked_part = "*" * (len(api_key) - 4)
    return f"{visible_part}{masked_part}"


# Model Selection
with st.sidebar.expander("🤖 Model Selection", expanded=False):
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "mixtral-8x7b-32768"

    selected_model = st.selectbox(
        "Choose LLM Model",
        options=AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(st.session_state.selected_model),
        help="Select the model to use for chat responses",
    )

    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model
        st.session_state["query_engines"] = {}
        st.success(f"Model changed to {selected_model}")
        st.rerun()

# API Key Management section
with st.sidebar.expander(
    "🔑 API Key Management",
    expanded="GROQ_API_KEY" not in st.secrets,
):
    if "api_key" not in st.session_state:
        st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")

    if not st.session_state.api_key:
        st.warning("Please enter your GROQ API key to use the chat feature.")
        st.markdown("Get your API key from [GROQ Console](https://console.groq.com)")

    # Display the partially masked API key
    masked_api_key = mask_api_key(st.session_state.api_key)

    # API Key input with password mask
    new_api_key = st.text_input(
        "GROQ API Key",
        disabled=True if masked_api_key else False,
        value=masked_api_key,
        type="password",
        help="Enter your GROQ API key to enable chat functionality",
    )

    # Save/Update button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Key"):
            if new_api_key and new_api_key != st.session_state.api_key:
                st.session_state.api_key = new_api_key
                os.environ["GROQ_API_KEY"] = new_api_key
                st.success("API key saved!")
                st.rerun()

    with col2:
        if st.button("🗑️ Clear Key"):
            st.session_state.api_key = ""
            if "GROQ_API_KEY" in os.environ:
                del os.environ["GROQ_API_KEY"]
            st.warning("API key cleared!")
            st.rerun()

# Check for API key in session state
if not st.session_state.get("api_key"):
    st.error("Please add your GROQ API key in the sidebar to use the chat feature.")
    st.stop()

# Set API key from session state
os.environ["GROQ_API_KEY"] = st.session_state.api_key

# Initialize database and query engine container in session state
if "query_engines" not in st.session_state:
    st.session_state["query_engines"] = {}

# For conversation renaming flag and manual rename tracking
if "show_rename" not in st.session_state:
    st.session_state["show_rename"] = False
if "manually_renamed" not in st.session_state:
    st.session_state["manually_renamed"] = set()

db = ConversationDB()
# ensure the database instance is available in the session state
st.session_state["db"] = db

# Sidebar: Conversation management
conversations = db.get_conversations()
selected_session_id = None
if conversations:
    options = [
        {"id": sid, "name": db.get_conversation_name(sid), "created": created[:10]}
        for sid, created in conversations
    ]
    selected_index = st.sidebar.selectbox(
        "Select conversation:",
        range(len(options)),
        format_func=lambda i: f"{options[i]['name']}\n{options[i]['id']}",
        key="conversation_selector",
    )
    selected_session_id = options[selected_index]["id"]

# Conversation renaming functionality
if st.sidebar.button("✏️ Rename Conversation", help="Rename conversation"):
    st.session_state["show_rename"] = True

if st.session_state.get("show_rename") and selected_session_id:
    with st.sidebar:
        current_name = db.get_conversation_name(selected_session_id)
        suggested_name = db.suggest_conversation_name(selected_session_id)
        st.markdown("##### Current name:")
        st.code(current_name, language=None)
        if (
            suggested_name != "✨ New Conversation"
            and current_name == "✨ New Conversation"
        ):
            st.markdown("##### Suggested name:")
            st.success(suggested_name)
        new_name = st.text_input(
            "Enter new name:",
            value=suggested_name
            if suggested_name != "✨ New Conversation"
            else current_name,
            placeholder="Enter a descriptive name...",
            key="new_conversation_name",
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Save"):
                if new_name and new_name != current_name:
                    db.update_conversation_name(selected_session_id, new_name)
                    # Mark conversation as manually renamed
                    st.session_state["manually_renamed"].add(selected_session_id)
                st.session_state["show_rename"] = False
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state["show_rename"] = False
                st.rerun()

if st.sidebar.button("🎬 Start New Conversation"):
    if selected_session_id:
        try:
            session_storage = f"./storage/{selected_session_id}"
            session_cache = f"./cache/{selected_session_id}"
            if os.path.exists(session_storage):
                shutil.rmtree(session_storage)
            if os.path.exists(session_cache):
                shutil.rmtree(session_cache)
            if selected_session_id in st.session_state["query_engines"]:
                del st.session_state["query_engines"][selected_session_id]
        except Exception as e:
            logging.error(f"Error cleaning up session {selected_session_id}: {e}")
    selected_session_id = db.create_conversation()
    st.rerun()

# Modify the QueryEngine initialization to use the selected model
if selected_session_id and selected_session_id not in st.session_state["query_engines"]:
    st.session_state["query_engines"][selected_session_id] = QueryEngine(
        os.getenv("GROQ_API_KEY"),
        session_id=selected_session_id,
        model=st.session_state.selected_model,
    )


# Add a function to check and update conversation name
def update_conversation_name_if_needed(session_id):
    """Update conversation name with suggestion if not manually renamed."""
    if session_id not in st.session_state["manually_renamed"]:
        current_name = db.get_conversation_name(session_id)
        if current_name == "New Conversation":
            suggested_name = db.suggest_conversation_name(session_id)
            if suggested_name != "New Conversation":
                db.update_conversation_name(session_id, suggested_name)
                return True
    return False


# Layout: Three tabs for Upload & Chat, History, and Notes
tab1, tab2, tab3 = st.tabs(["📤 Upload & Chat", "📜 History", "📝 Notes"])

with tab1:
    render_upload_chat(selected_session_id, db)
    # Check for name update after each chat interaction
    if selected_session_id:
        update_conversation_name_if_needed(selected_session_id)

with tab2:
    render_history(db)

with tab3:
    render_notes()


# Move db.close() inside a Streamlit event handler to ensure it runs last
def on_shutdown():
    if "db" in st.session_state:
        st.session_state.db.close()


st.session_state["_on_shutdown"] = on_shutdown

# Keep the sidebar footer
st.sidebar.markdown("<br>" * 5, unsafe_allow_html=True)
st.sidebar.markdown(
    """
    <div class="sidebar-footer">
        <hr>
        <p>
            Made with ❤️ by Prince Kyeremeh
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
