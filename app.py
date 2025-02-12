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
/* Chat container styles */
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

/* Footer styles */
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: white;
    padding: 1rem;
    border-top: 1px solid #ddd;
    z-index: 100;
}

/* Main content area styles */
.main-content {
    margin-bottom: 120px; /* Add space for the fixed footer */
    padding-bottom: 2rem;
}

/* Chat message styles */
.chat-message {
    margin-bottom: 1rem;
    padding: 1rem;
    border-radius: 8px;
}

.user-message {
    background-color: #e3f2fd;
    margin-left: 20%;
}

.assistant-message {
    background-color: #f5f5f5;
    margin-right: 20%;
}

/* Ensure chat input is at the bottom */
div[data-testid="stForm"] {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: white;
    padding: 1rem;
    border-top: 1px solid #ddd;
    z-index: 99;
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
            for _, file_name in files:
                st.text(f"• {file_name}")

    # Create a container for the main content
    main_content = st.container()

    with main_content:
        # Display conversation history
        if selected_session_id:
            messages = db.get_messages(selected_session_id)
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            for role, content, timestamp in messages:
                message_class = "user-message" if role == "user" else "assistant-message"
                st.markdown(
                    f'<div class="chat-message {message_class}">{content}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

    # Create a form for the chat input
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area("Type your message:", key="user_input", height=100)
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            uploaded_file = st.file_uploader(
                "Upload a document",
                type=SUPPORTED_FILE_TYPES,
                help="Upload a document to chat with",
            )
        with col2:
            submit_button = st.form_submit_button("Send")

        if submit_button and user_input:
            if not selected_session_id:
                selected_session_id = db.create_conversation()

            # Handle file upload
            if uploaded_file:
                file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                db.add_file(selected_session_id, file_path, uploaded_file.name)
                query_engine.index_manager.build_index()  # Rebuild index with new file

            # Store user message
            db.add_message(selected_session_id, "user", user_input)

            try:
                # Get response from query engine
                response = query_engine.query(user_input)
                # Store assistant response
                db.add_message(selected_session_id, "assistant", str(response))
            except Exception as e:
                error_message = f"Error: {str(e)}"
                st.error(error_message)
                db.add_message(selected_session_id, "assistant", error_message)

            st.rerun()

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
