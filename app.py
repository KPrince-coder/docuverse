import streamlit as st
import os
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
</style>
""",
    unsafe_allow_html=True,
)

# Set GROQ_API_KEY in environment
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# Initialize Query Engine and Database
query_engine = QueryEngine(os.getenv("GROQ_API_KEY"))
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
if conversations:
    selected_session_id = st.sidebar.selectbox(
        "Select a conversation:",
        [f"{sid} ({created_at[:10]})" for sid, created_at in conversations],
    )
    selected_session_id = selected_session_id.split(" ")[0]
else:
    selected_session_id = None

if st.sidebar.button("Start New Conversation"):
    selected_session_id = db.create_conversation()
    st.rerun()

# Main App
st.title("🚀 DocuVerse: Your Document Intelligence Assistant")

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
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    # Track the file in the database
                    db.add_file(selected_session_id, file_path, uploaded_file.name)
                    st.write(f"Processing: {uploaded_file.name}")

                # Rebuild the index after uploading new files
                query_engine.index_manager.build_index()
                st.success("Files processed successfully!")

    # Show current conversation's files
    if selected_session_id:
        files = db.get_conversation_files(selected_session_id)
        if files:
            st.subheader("📄 Uploaded Files")
            for file_path, file_name in files:
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.text(f"• {file_name}")
                with col2:
                    if st.button("🗑️", key=f"delete_file_{file_name}"):
                        if st.button("Confirm deletion?", key=f"confirm_{file_name}"):
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
        # Display chat history
        messages = db.get_messages(selected_session_id)
        for role, content, timestamp in messages:
            with st.chat_message(role):
                st.write(content)
                st.caption(f"Sent at {timestamp[:16]}")

        # Chat input
        if question := st.chat_input("Ask about your documents..."):
            if not os.listdir(UPLOAD_DIR):
                st.error("Please upload some documents first!")
            else:
                # Add user message to chat
                with st.chat_message("user"):
                    st.write(question)

                # Get AI response with context
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = query_engine.query(question)
                        st.write(response)

                # Store the conversation
                db.add_message(selected_session_id, "user", question)
                db.add_message(selected_session_id, "assistant", str(response))

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

# Footer
st.markdown(
    """
    <hr>
    <p style="text-align:center">
        Made with ❤️ by DocuVerse Team
    </p>
    """,
    unsafe_allow_html=True,
)

# Close Database Connection
db.close()
