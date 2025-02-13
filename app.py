import streamlit as st
import os
import shutil
import logging
from datetime import datetime
from utils.database import ConversationDB
from utils.query_engine import QueryEngine

# Configure Streamlit
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

# Add custom CSS directly
st.markdown(
    """
<style>
.conversation-box {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    background-color: #f8f9fa;
}
.conversation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.file-list {
    color: #666;
    font-size: 0.9em;
    margin-top: 5px;
}


.sidebar-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 17rem;  /* Match Streamlit's sidebar width */
    background-color: rgb(240, 242, 246);
    padding: 1rem 0;
    text-align: center;
    border-top: 1px solid #ddd;
    z-index: 999;
    font-size: 0.8em;
    margin-bottom: 3rem;  /* Add space for Streamlit's bottom bar */
}

.sidebar-footer hr {
    margin: 0.5rem 1rem;
    border: none;
    border-top: 1px solid #ddd;
}

.sidebar-footer p {
    margin: 0.5rem 0;
    opacity: 0.7;
}
.main-content {
    margin-bottom: 80px;  /* Add space for footer */
}
</style>
""",
    unsafe_allow_html=True,
)

# Set GROQ_API_KEY in environment
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# Initialize Query Engine and Database
query_engines = {}
db = ConversationDB()

# Create upload directory if it doesn't exist
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Update the file uploader supported types
SUPPORTED_FILE_TYPES = [
    "txt",
    "md",
    "pdf",
    "docx",  # Text and Documents
    "ppt",
    "pptm",
    "pptx",  # Presentations
    "csv",  # Data files
    "epub",  # Ebooks
    "hwp",  # Korean word processor
    "ipynb",  # Jupyter notebooks
    "mbox",  # Email archives
    "json",  # JSON (handled separately)
]

# Sidebar for Conversation Management
st.sidebar.title("📚 DocuVerse")
conversations = db.get_conversations()

# Initialize selected_session_id
selected_session_id = None

if conversations:
    # Create two columns for the conversation selector
    col1, col2 = st.sidebar.columns([3, 1])

    with col1:
        # Display conversation name with session ID as subtext
        conversation_options = []
        for sid, created_at in conversations:
            name = db.get_conversation_name(sid)
            conversation_options.append(
                {"id": sid, "name": name, "created": created_at[:10]}
            )

        selected_index = st.selectbox(
            "Select conversation:",
            range(len(conversation_options)),
            format_func=lambda i: f"{conversation_options[i]['name']}\n"
            f"<div style='font-size: 0.8em; color: #666;'>{conversation_options[i]['id']}</div>",
            key="conversation_selector",
        )

        if selected_index is not None:
            selected_session_id = conversation_options[selected_index]["id"]

    with col2:
        if selected_session_id and st.button("✏️", help="Rename conversation"):
            st.session_state.show_rename = True

# Show rename dialog
if getattr(st.session_state, "show_rename", False):
    with st.sidebar:
        current_name = db.get_conversation_name(selected_session_id)
        suggested_name = db.suggest_conversation_name(selected_session_id)

        new_name = st.text_input(
            "Rename conversation:",
            value=current_name,
            placeholder=suggested_name,
            key="new_conversation_name",
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Save"):
                if new_name and new_name != current_name:
                    db.update_conversation_name(selected_session_id, new_name)
                st.session_state.show_rename = False
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.show_rename = False
                st.rerun()

if st.sidebar.button("Start New Conversation"):
    # Clean up old session resources if they exist
    if selected_session_id:
        try:
            # Remove session-specific storage and cache
            session_storage = f"./storage/{selected_session_id}"
            session_cache = f"./cache/{selected_session_id}"
            if os.path.exists(session_storage):
                shutil.rmtree(session_storage)
            if os.path.exists(session_cache):
                shutil.rmtree(session_cache)
            # Remove session's query engine
            if selected_session_id in query_engines:
                del query_engines[selected_session_id]
        except Exception as e:
            logging.error(f"Error cleaning up session {selected_session_id}: {e}")

    selected_session_id = db.create_conversation()
    st.rerun()

# Get or create query engine for current session
if selected_session_id and selected_session_id not in query_engines:
    query_engines[selected_session_id] = QueryEngine(
        os.getenv("GROQ_API_KEY"), session_id=selected_session_id
    )

# Main App
st.title("🚀 DocuVerse: Your Document Intelligence Assistant")

# Wrap main content in a div with margin-bottom
st.markdown('<div class="main-content">', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Upload & Chat", "History"])


def delete_file(file_path: str, file_name: str, session_id: str):
    """Delete a file and its database entry."""
    try:
        # Remove file from disk
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove file from database
        db.delete_file(session_id, file_path)

        # Rebuild index after file deletion
        query_engine = query_engines.get(session_id)
        if query_engine:
            query_engine.index_manager.build_index()
        return True
    except Exception as e:
        st.error(f"Error deleting file: {e}")
        return False


with tab1:
    # File upload section
    st.subheader("📂 Upload Files")

    if not selected_session_id:
        st.warning("Please start a new conversation before uploading files.")
    else:
        uploaded_files = st.file_uploader(
            "Upload documents to chat about",
            type=SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
        )

        if uploaded_files:
            with st.status("Processing files..."):
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

                    # Try to add file to database first
                    if db.add_file(selected_session_id, file_path, uploaded_file.name):
                        # Only write file to disk if database insertion was successful
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.write(f"Processing: {uploaded_file.name}")
                    else:
                        st.warning(
                            f"File {uploaded_file.name} already exists in this conversation. Skipping..."
                        )
                        continue

                # Rebuild the index after uploading new files
                query_engine = query_engines.get(selected_session_id)
                if query_engine:
                    query_engine.index_manager.build_index()
                st.success("Files processed successfully!")

    # Show current conversation's files
    if selected_session_id:
        files = db.get_conversation_files(selected_session_id)
        if files:
            st.subheader("📄 Uploaded Files")
            # Use a set to track unique file names
            seen_files = set()
            for file_path, file_name in files:
                if file_name in seen_files:
                    continue
                seen_files.add(file_name)

                col1, col2 = st.columns([6, 1])
                with col1:
                    st.text(f"• {file_name}")
                with col2:
                    # Create a unique key using both session_id and file_path
                    unique_key = f"{selected_session_id}_{file_path}".replace(
                        "\\", "_"
                    ).replace("/", "_")
                    if st.button("🗑️", key=f"delete_file_{unique_key}"):
                        if st.button("Confirm deletion?", key=f"confirm_{unique_key}"):
                            if delete_file(file_path, file_name, selected_session_id):
                                st.success(f"Deleted {file_name}")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete {file_name}")

    # Chat section
st.subheader("💬 Chat")
if not selected_session_id:
    st.info("Please start a new conversation using the sidebar.")
else:
    # Create a container for all chat content
    chat_container = st.container()

    # Display existing messages first
    with chat_container:
        messages = db.get_messages(selected_session_id)
        for role, content, timestamp in messages:
            with st.chat_message(role):
                st.write(content)
                st.caption(f"Sent at {timestamp[:16]}")

    # Then handle new messages
    question = st.chat_input("Ask about your documents...")
    if question:
        if not os.listdir(UPLOAD_DIR):
            st.error("Please upload some documents first!")
        else:
            with chat_container:
                # Show user message
                with st.chat_message("user"):
                    st.write(question)

                # Get and show AI response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        query_engine = query_engines.get(selected_session_id)
                        if query_engine:
                            response = query_engine.query(question)
                            st.write(response)

                            # Store both messages
                            db.add_message(selected_session_id, "user", question)
                            db.add_message(selected_session_id, "assistant", response)

                            # Suggest name for new conversations
                            current_name = db.get_conversation_name(selected_session_id)
                            if current_name == "New Conversation":
                                suggested_name = db.suggest_conversation_name(
                                    selected_session_id
                                )
                                db.update_conversation_name(
                                    selected_session_id, suggested_name
                                )

                            # Rerun to update chat history
                            st.rerun()
                        else:
                            st.error(
                                "Session not initialized properly. Please try refreshing the page."
                            )


with tab2:
    st.header("📖 Conversation History")

    # Get detailed conversation history
    conversations = db.get_conversation_details()

    if not conversations:
        st.info("No conversations yet. Start a new conversation to begin!")

    for session_id, created_at, msg_count, file_count, files in conversations:
        # Format the creation date
        created_date = datetime.fromisoformat(created_at).strftime("%B %d, %Y at %H:%M")

        # Create a container for each conversation
        with st.container():
            st.markdown(
                f"""
            <div class="conversation-box">
                <div class="conversation-header">
                    <h3>Conversation from {created_date}</h3>
                </div>
                <p>📝 {msg_count} messages • 📎 {file_count} files</p>
                <div class="file-list">
                    {"Files: " + files if files else "No files uploaded"}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button("View Details", key=f"view_{session_id}"):
                    messages = db.get_messages(session_id)
                    for role, content, timestamp in messages:
                        with st.chat_message(role):
                            st.write(content)
                            st.caption(f"Sent at {timestamp[:16]}")

            with col2:
                if st.button("🗑️ Delete", key=f"delete_{session_id}"):
                    if st.session_state.get("selected_session_id") == session_id:
                        st.session_state.selected_session_id = None
                    db.delete_conversation(session_id)
                    st.rerun()

# Close the main-content div
st.markdown("</div>", unsafe_allow_html=True)

# Sidebar Footer

# Add some empty space in the sidebar to prevent content overlap
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

# Close Database Connection
db.close()
