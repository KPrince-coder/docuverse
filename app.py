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
        "Get Help": "https://github.com/yourusername/docuverse",
        "Report a bug": "https://github.com/yourusername/docuverse/issues",
        "About": "# DocuVerse\nYour Document Intelligence Assistant",
    },
)

# Load custom CSS for header, chat, and inline action buttons
with open("components/style.css", "r") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# Render the sticky header
render_header()

# Set API key from secrets
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

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
st.sidebar.title("📚 DocuVerse")
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
        if suggested_name != "New Conversation" and current_name == "New Conversation":
            st.markdown("##### Suggested name:")
            st.success(suggested_name)
        new_name = st.text_input(
            "Enter new name:",
            value=suggested_name
            if suggested_name != "New Conversation"
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

if st.sidebar.button("Start New Conversation"):
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

if selected_session_id and selected_session_id not in st.session_state["query_engines"]:
    st.session_state["query_engines"][selected_session_id] = QueryEngine(
        os.getenv("GROQ_API_KEY"), session_id=selected_session_id
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
            Made with ❤️ by DocuVerse Team
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
