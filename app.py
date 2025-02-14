# import streamlit as st
# import os
# import shutil
# import logging
# import time
# from datetime import datetime
# from utils.database import ConversationDB
# from utils.query_engine import QueryEngine

# # Configure logging
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)


# # Configure Streamlit
# st.set_page_config(
#     page_title="DocuVerse",
#     page_icon="📚",
#     layout="wide",
#     initial_sidebar_state="auto",
#     menu_items={
#         "Get Help": "https://github.com/yourusername/docuverse",
#         "Report a bug": "https://github.com/yourusername/docuverse/issues",
#         "About": "# DocuVerse\nYour Document Intelligence Assistant",
#     },
# )

# # Add custom CSS directly
# st.markdown(
#     """
# <style>
# .conversation-box {
#     border: 1px solid #ddd;
#     border-radius: 8px;
#     padding: 15px;
#     margin: 10px 0;
#     background-color: #f8f9fa;
# }
# .conversation-header {
#     display: flex;
#     justify-content: space-between;
#     align-items: center;
# }
# .file-list {
#     color: #666;
#     font-size: 0.9em;
#     margin-top: 5px;
# }


# .sidebar-footer {
#     position: fixed;
#     bottom: 0;
#     left: 0;
#     width: 17rem;  /* Match Streamlit's sidebar width */
#     background-color: rgb(240, 242, 246);
#     padding: 1rem 0;
#     text-align: center;
#     border-top: 1px solid #ddd;
#     z-index: 999;
#     font-size: 0.8em;
#     margin-bottom: 3rem;  /* Add space for Streamlit's bottom bar */
# }

# .sidebar-footer hr {
#     margin: 0.5rem 1rem;
#     border: none;
#     border-top: 1px solid #ddd;
# }

# .sidebar-footer p {
#     margin: 0.5rem 0;
#     opacity: 0.7;
# }
# .main-content {
#     margin-bottom: 80px;  /* Add space for footer */
#     position: relative;
# }


# .fixed-chat-input {
#     position: fixed;
#     bottom: 0;
#     left: 0;  /* Match sidebar width */
#     right: 0;
#     padding: 1rem;
#     height: 8rem;
#     background: white;
#     z-index: 100;
# }

# .chat-messages {
#     overflow-y: auto;
#     padding-bottom: 2rem;
# }

# </style>
# """,
#     unsafe_allow_html=True,
# )

# # Set GROQ_API_KEY in environment
# os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# # Initialize Query Engine and Database
# query_engines = {}
# db = ConversationDB()

# # Create upload directory if it doesn't exist
# UPLOAD_DIR = "data/uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# # Update the file uploader supported types
# SUPPORTED_FILE_TYPES = [
#     "txt",
#     "md",
#     "pdf",
#     "docx",  # Text and Documents
#     "ppt",
#     "pptm",
#     "pptx",  # Presentations
#     "csv",  # Data files
#     "epub",  # Ebooks
#     "hwp",  # Korean word processor
#     "ipynb",  # Jupyter notebooks
#     "mbox",  # Email archives
#     "json",  # JSON (handled separately)
# ]

# # Sidebar for Conversation Management
# st.sidebar.title("📚 DocuVerse")
# conversations = db.get_conversations()

# # Initialize selected_session_id
# selected_session_id = None

# if conversations:
#     # Create two columns for the conversation selector
#     col1, col2 = st.sidebar.columns([3, 1])

#     with col1:
#         # Display conversation name with session ID as subtext
#         conversation_options = []
#         for sid, created_at in conversations:
#             name = db.get_conversation_name(sid)
#             conversation_options.append(
#                 {"id": sid, "name": name, "created": created_at[:10]}
#             )

#         selected_index = st.selectbox(
#             "Select conversation:",
#             range(len(conversation_options)),
#             format_func=lambda i: f"{conversation_options[i]['name']}\n"
#             f"<div style='font-size: 0.8em; color: #666;'>{conversation_options[i]['id']}</div>",
#             key="conversation_selector",
#         )

#         if selected_index is not None:
#             selected_session_id = conversation_options[selected_index]["id"]

#     with col2:
#         if selected_session_id and st.button("✏️", help="Rename conversation"):
#             st.session_state.show_rename = True

# # Show rename dialog
# if getattr(st.session_state, "show_rename", False):
#     with st.sidebar:
#         current_name = db.get_conversation_name(selected_session_id)
#         suggested_name = db.suggest_conversation_name(selected_session_id)

#         st.markdown("##### Current name:")
#         st.code(current_name, language=None)

#         if suggested_name != "New Conversation" and current_name == "New Conversation":
#             st.markdown("##### Suggested name:")
#             st.success(suggested_name)

#         new_name = st.text_input(
#             "Enter new name:",
#             value=suggested_name
#             if suggested_name != "New Conversation"
#             else current_name,
#             placeholder="Enter a descriptive name...",
#             key="new_conversation_name",
#         )

#         col1, col2 = st.columns([1, 1])
#         with col1:
#             if st.button("Save"):
#                 if new_name and new_name != current_name:
#                     db.update_conversation_name(selected_session_id, new_name)
#                 st.session_state.show_rename = False
#                 st.rerun()
#         with col2:
#             if st.button("Cancel"):
#                 st.session_state.show_rename = False
#                 st.rerun()

# if st.sidebar.button("Start New Conversation"):
#     # Clean up old session resources if they exist
#     if selected_session_id:
#         try:
#             # Remove session-specific storage and cache
#             session_storage = f"./storage/{selected_session_id}"
#             session_cache = f"./cache/{selected_session_id}"
#             if os.path.exists(session_storage):
#                 shutil.rmtree(session_storage)
#             if os.path.exists(session_cache):
#                 shutil.rmtree(session_cache)
#             # Remove session's query engine
#             if selected_session_id in query_engines:
#                 del query_engines[selected_session_id]
#         except Exception as e:
#             logging.error(f"Error cleaning up session {selected_session_id}: {e}")

#     selected_session_id = db.create_conversation()
#     st.rerun()

# # Get or create query engine for current session
# if selected_session_id and selected_session_id not in query_engines:
#     query_engines[selected_session_id] = QueryEngine(
#         os.getenv("GROQ_API_KEY"), session_id=selected_session_id
#     )

# # Main App
# st.title("🚀 DocuVerse: Your Document Intelligence Assistant")

# # Wrap main content in a div with margin-bottom
# st.markdown('<div class="main-content">', unsafe_allow_html=True)

# tab1, tab2 = st.tabs(["📤 Upload & Chat", "📜 History"])


# def delete_file(file_path: str, file_name: str, session_id: str):
#     """Delete a file and its database entry."""
#     try:
#         # Remove file from disk
#         if os.path.exists(file_path):
#             os.remove(file_path)

#         # Remove file from database
#         db.delete_file(session_id, file_path)

#         # Rebuild index after file deletion
#         query_engine = query_engines.get(session_id)
#         if query_engine:
#             query_engine.index_manager.build_index()
#         return True
#     except Exception as e:
#         st.error(f"Error deleting file: {e}")
#         return False


# def handle_file_upload(uploaded_file, session_id):
#     """Handle single file upload with better error handling"""
#     try:
#         # Create session-specific directory
#         session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
#         os.makedirs(session_upload_dir, exist_ok=True)

#         file_path = os.path.join(session_upload_dir, uploaded_file.name)

#         # Try to add file to database first
#         if db.add_file(session_id, file_path, uploaded_file.name):
#             # Only write file to disk if database insertion was successful
#             with open(file_path, "wb") as f:
#                 f.write(uploaded_file.getbuffer())
#             return True
#         return False
#     except Exception as e:
#         logger.error(f"Error handling file upload: {e}")
#         return False


# def get_session_files(session_id: str):
#     """Get files only for the specific session."""
#     session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
#     if not os.path.exists(session_upload_dir):
#         return []
#     return db.get_conversation_files(session_id)


# # Add this function near the top with other helper functions
# def is_file_uploaded(session_id: str, file_name: str) -> bool:
#     """Check if a file is already uploaded in the session."""
#     session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
#     file_path = os.path.join(session_upload_dir, file_name)
#     return os.path.exists(file_path)


# # Update the file upload section in tab1
# with tab1:
#     st.subheader("📂 Upload Files")

#     if not selected_session_id:
#         st.warning("Please start a new conversation before uploading files.")
#     else:
#         # Create session-specific directory
#         session_upload_dir = os.path.join(UPLOAD_DIR, selected_session_id)
#         os.makedirs(session_upload_dir, exist_ok=True)

#         # Show files only for current session
#         current_files = get_session_files(selected_session_id)

#         uploaded_files = st.file_uploader(
#             "Upload documents to chat about",
#             type=SUPPORTED_FILE_TYPES,
#             accept_multiple_files=True,
#             key=f"uploader_{selected_session_id}",  # Add unique key for each session
#         )

#         if uploaded_files:
#             with st.status("Processing files...") as status:
#                 successful_uploads = 0
#                 failed_uploads = 0

#                 # Create set of existing files
#                 existing_files = {f[1] for f in get_session_files(selected_session_id)}

#                 for uploaded_file in uploaded_files:
#                     # Skip if file is already uploaded
#                     if uploaded_file.name in existing_files:
#                         status.write(
#                             f"⏭️ Skipping already uploaded file: {uploaded_file.name}"
#                         )
#                         continue

#                     status.write(f"Processing: {uploaded_file.name}")
#                     if handle_file_upload(uploaded_file, selected_session_id):
#                         successful_uploads += 1
#                         status.write(f"✅ Processed: {uploaded_file.name}")
#                     else:
#                         failed_uploads += 1
#                         status.write(f"❌ Failed: {uploaded_file.name}")

#                 # Rebuild the index after all files are uploaded
#                 if successful_uploads > 0:
#                     status.write("Rebuilding search index...")
#                     query_engine = query_engines.get(selected_session_id)
#                     if query_engine:
#                         query_engine.index_manager.build_index()

#                 status.update(label="Upload Complete", state="complete")

#                 if successful_uploads > 0:
#                     st.success(f"Successfully processed {successful_uploads} files")
#                 if failed_uploads > 0:
#                     st.error(f"Failed to process {failed_uploads} files")

#     # Update the files display section
#     if selected_session_id:
#         files = get_session_files(selected_session_id)
#         if files:
#             st.subheader("📄 Uploaded Files")
#             # Use a set to track unique file names
#             seen_files = set()
#             for file_path, file_name in files:
#                 # Verify file belongs to current session
#                 if not file_path.startswith(
#                     os.path.join(UPLOAD_DIR, selected_session_id)
#                 ):
#                     continue

#                 if file_name in seen_files:
#                     continue
#                 seen_files.add(file_name)

#                 col1, col2 = st.columns([6, 1])
#                 with col1:
#                     st.text(f"• {file_name}")
#                 with col2:
#                     # Create a unique key using both session_id and file_path
#                     unique_key = f"{selected_session_id}_{file_path}".replace(
#                         "\\", "_"
#                     ).replace("/", "_")
#                     if st.button("🗑️", key=f"delete_file_{unique_key}"):
#                         if st.button("Confirm deletion?", key=f"confirm_{unique_key}"):
#                             if delete_file(file_path, file_name, selected_session_id):
#                                 st.success(f"Deleted {file_name}")
#                                 st.rerun()
#                             else:
#                                 st.error(f"Failed to delete {file_name}")

#     # Chat section
#     st.subheader("💬 Chat")
#     if not selected_session_id:
#         st.info("Please start a new conversation using the sidebar.")
#     else:
#         # Create message container
#         messages_container = st.container()

#         with messages_container:
#             st.markdown('<div class="chat-messages">', unsafe_allow_html=True)

#             # Get all previous messages for context
#             messages = db.get_messages(selected_session_id)
#             conversation_history = []

#             for role, content, timestamp in messages:
#                 formatted_time = datetime.fromisoformat(timestamp).strftime(
#                     "%a, %b %d, %Y at %H:%M"
#                 )
#                 with st.chat_message(role):
#                     st.write(content)
#                     st.caption(
#                         f"{'Sent' if role == 'user' else 'Received'} on {formatted_time}"
#                     )
#                 conversation_history.append({"role": role, "content": content})

#             st.markdown("</div>", unsafe_allow_html=True)

#         # Fixed chat input at bottom (only in Upload & Chat tab)

#         st.markdown(
#             """
#             <div class="fixed-chat-input">
#                 <style>
#                     /* Override Streamlit's default padding for chat input */
#                     .stChatInput {
#                         position:fixed;
#                         bottom: 4.5rem;
#                         z-index: 100;
#                     }
#                 </style>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )

#         # Place chat input
#         question = st.chat_input(
#             "✍️ Ask about your documents...",
#             key="chat_input",
#         )

#         if question:
#             session_files = get_session_files(selected_session_id)
#             if not session_files:
#                 st.error("Please upload some documents first!")
#             else:
#                 with messages_container:
#                     with st.chat_message("user"):
#                         st.write(question)
#                         conversation_history.append(
#                             {"role": "user", "content": question}
#                         )

#                     with st.chat_message("assistant"):
#                         with st.spinner("🧠 Thinking..."):
#                             query_engine = query_engines.get(selected_session_id)
#                             if not query_engine:
#                                 query_engine = QueryEngine(
#                                     os.getenv("GROQ_API_KEY"),
#                                     session_id=selected_session_id,
#                                 )
#                                 query_engines[selected_session_id] = query_engine

#                             # Include conversation history in the query
#                             response = query_engine.query(
#                                 question, conversation_history=conversation_history
#                             )
#                             st.write(response)

#                             # Update conversation history
#                             conversation_history.append(
#                                 {"role": "assistant", "content": response}
#                             )

#                             # Store messages
#                             db.add_message(selected_session_id, "user", question)
#                             db.add_message(selected_session_id, "assistant", response)

#                             # Update conversation name with better timing and feedback
#                             current_name = db.get_conversation_name(selected_session_id)
#                             if current_name == "New Conversation":
#                                 suggested_name = db.suggest_conversation_name(
#                                     selected_session_id
#                                 )
#                                 if suggested_name != "New Conversation":
#                                     with st.status(
#                                         "✨ Generating conversation name...",
#                                         expanded=True,
#                                     ) as status:
#                                         db.update_conversation_name(
#                                             selected_session_id, suggested_name
#                                         )
#                                         status.update(
#                                             label=f"✨ Named conversation: {suggested_name}"
#                                         )
#                                         time.sleep(1)  # Brief pause to show the status
#                                         st.rerun()

#                             # Rerun to update chat history
#                             st.rerun()

# with tab2:
#     st.header("📖 Conversation History")

#     # Get detailed conversation history
#     conversations = db.get_conversation_details()

#     if not conversations:
#         st.info("No conversations yet. Start a new conversation to begin!")

#     # Store selected conversation for viewing in session state
#     if "viewing_conversation" not in st.session_state:
#         st.session_state.viewing_conversation = None

#     for session_id, created_at, msg_count, file_count, files in conversations:
#         # Format the creation date
#         created_date = datetime.fromisoformat(created_at).strftime("%B %d, %Y at %H:%M")

#         # Get conversation name
#         conv_name = db.get_conversation_name(session_id)

#         # Create a container for each conversation
#         with st.container():
#             st.markdown(
#                 f"""
#             <div class="conversation-box">
#                 <div class="conversation-header">
#                     <h3>{conv_name}</h3>
#                     <p style="color: #666; font-size: 0.9em;">{created_date}</p>
#                 </div>
#                 <p>📝 {msg_count} messages • 📎 {file_count} files</p>
#                 <div class="file-list">
#                     {"Files: " + files if files else "No files uploaded"}
#                 </div>
#             </div>
#             """,
#                 unsafe_allow_html=True,
#             )

#             col1, col2 = st.columns([4, 1])
#             with col1:
#                 if st.button("View Details", key=f"view_{session_id}"):
#                     if st.session_state.viewing_conversation == session_id:
#                         st.session_state.viewing_conversation = None  # Toggle off
#                     else:
#                         st.session_state.viewing_conversation = session_id  # Toggle on
#                     st.rerun()

#             with col2:
#                 if st.button("🗑️ Delete", key=f"delete_{session_id}"):
#                     if st.session_state.get("selected_session_id") == session_id:
#                         st.session_state.selected_session_id = None
#                     db.delete_conversation(session_id)
#                     st.rerun()

#             # Show conversation details only if this conversation is selected for viewing
#             if st.session_state.viewing_conversation == session_id:
#                 with st.expander("Conversation Details", expanded=True):
#                     messages = db.get_messages(session_id)
#                     if not messages:
#                         st.info("No messages in this conversation.")
#                     else:
#                         for role, content, timestamp in messages:
#                             formatted_time = datetime.fromisoformat(timestamp).strftime(
#                                 "%a, %b %d, %Y at %H:%M"
#                             )
#                             with st.chat_message(role):
#                                 st.write(content)
#                                 st.caption(
#                                     f"{'Sent' if role == 'user' else 'Received'} on {formatted_time}"
#                                 )


# # Close the main-content div
# st.markdown("</div>", unsafe_allow_html=True)

# # Sidebar Footer
# st.sidebar.markdown("<br>" * 5, unsafe_allow_html=True)
# st.sidebar.markdown(
#     """
#     <div class="sidebar-footer">
#         <hr>
#         <p>
#             Made with ❤️ by DocuVerse Team
#         </p>
#     </div>
#     """,
#     unsafe_allow_html=True,
# )

# # Close Database Connection
# db.close()


import streamlit as st
import os
import shutil
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from utils.database import ConversationDB
from utils.query_engine import QueryEngine

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
    position: relative;
}

.fixed-chat-input {
    position: fixed;
    bottom: 0;
    left: 0;  /* Match sidebar width */
    right: 0;
    padding: 1rem;
    height: 8rem;
    background: white;
    z-index: 100;
}

.chat-messages {
    overflow-y: auto;
    padding-bottom: 2rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# Set GROQ_API_KEY in environment
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# Initialize Query Engine and Database
# Store query engines in session state for persistence between reruns
if "query_engines" not in st.session_state:
    st.session_state["query_engines"] = {}

db = ConversationDB()

# Create upload directory if it doesn't exist
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supported file types for uploader
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

# Show rename dialog in sidebar
if getattr(st.session_state, "show_rename", False):
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
            session_storage = f"./storage/{selected_session_id}"
            session_cache = f"./cache/{selected_session_id}"
            if os.path.exists(session_storage):
                shutil.rmtree(session_storage)
            if os.path.exists(session_cache):
                shutil.rmtree(session_cache)
            if selected_session_id in st.session_state["query_engines"]:
                del st.session_state["query_engines"][selected_session_id]
        except Exception as e:
            logger.error(f"Error cleaning up session {selected_session_id}: {e}")
    selected_session_id = db.create_conversation()
    st.rerun()

# Get or create query engine for current session from session state
if selected_session_id and selected_session_id not in st.session_state["query_engines"]:
    st.session_state["query_engines"][selected_session_id] = QueryEngine(
        os.getenv("GROQ_API_KEY"), session_id=selected_session_id
    )

# Main App
st.title("🚀 DocuVerse: Your Document Intelligence Assistant")
st.markdown('<div class="main-content">', unsafe_allow_html=True)
tab1, tab2 = st.tabs(["📤 Upload & Chat", "📜 History"])


def delete_file(file_path: str, file_name: str, session_id: str):
    """Delete a file and its database entry."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        db.delete_file(session_id, file_path)
        # Rebuild index after deletion
        query_engine = st.session_state["query_engines"].get(session_id)
        if query_engine:
            query_engine.index_manager.build_index()
        return True
    except Exception as e:
        st.error(f"Error deleting file: {e}")
        return False


def handle_file_upload(uploaded_file, session_id):
    """Handle single file upload with error handling."""
    try:
        session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(session_upload_dir, exist_ok=True)
        file_path = os.path.join(session_upload_dir, uploaded_file.name)
        if db.add_file(session_id, file_path, uploaded_file.name):
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return True
        return False
    except Exception as e:
        logger.error(f"Error handling file upload: {e}")
        return False


def get_session_files(session_id: str):
    """Get files only for the specific session."""
    session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
    if not os.path.exists(session_upload_dir):
        return []
    return db.get_conversation_files(session_id)


# (Optional) A helper to check if a file was already uploaded
def is_file_uploaded(session_id: str, file_name: str) -> bool:
    session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
    file_path = os.path.join(session_upload_dir, file_name)
    return os.path.exists(file_path)


# Process file uploads concurrently (if multiple files are uploaded)
def process_uploads(files, session_id):
    results = []
    with ThreadPoolExecutor(max_workers=min(len(files), 4)) as executor:
        futures = {executor.submit(handle_file_upload, f, session_id): f for f in files}
        for future in futures:
            results.append(future.result())
    return results


with tab1:
    st.subheader("📂 Upload Files")
    if not selected_session_id:
        st.warning("Please start a new conversation before uploading files.")
    else:
        session_upload_dir = os.path.join(UPLOAD_DIR, selected_session_id)
        os.makedirs(session_upload_dir, exist_ok=True)
        current_files = get_session_files(selected_session_id)
        uploaded_files = st.file_uploader(
            "Upload documents to chat about",
            type=SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            key=f"uploader_{selected_session_id}",
        )
        if uploaded_files:
            with st.status("Processing files...") as status:
                successful_uploads = 0
                failed_uploads = 0
                existing_files = {f[1] for f in get_session_files(selected_session_id)}
                new_files = [
                    uf for uf in uploaded_files if uf.name not in existing_files
                ]
                for uf in uploaded_files:
                    if uf.name in existing_files:
                        status.write(f"⏭️ Skipping already uploaded file: {uf.name}")
                if new_files:
                    results = process_uploads(new_files, selected_session_id)
                    for uf, result in zip(new_files, results):
                        if result:
                            successful_uploads += 1
                            status.write(f"✅ Processed: {uf.name}")
                        else:
                            failed_uploads += 1
                            status.write(f"❌ Failed: {uf.name}")
                    if successful_uploads > 0:
                        status.write("Rebuilding search index...")
                        query_engine = st.session_state["query_engines"].get(
                            selected_session_id
                        )
                        if query_engine:
                            query_engine.index_manager.build_index()
                status.update(label="Upload Complete", state="complete")
                if successful_uploads > 0:
                    st.success(f"Successfully processed {successful_uploads} files")
                if failed_uploads > 0:
                    st.error(f"Failed to process {failed_uploads} files")

    if selected_session_id:
        files = get_session_files(selected_session_id)
        if files:
            st.subheader("📄 Uploaded Files")
            seen_files = set()
            for file_path, file_name in files:
                if not file_path.startswith(
                    os.path.join(UPLOAD_DIR, selected_session_id)
                ):
                    continue
                if file_name in seen_files:
                    continue
                seen_files.add(file_name)
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.text(f"• {file_name}")
                with col2:
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

    st.subheader("💬 Chat")
    if not selected_session_id:
        st.info("Please start a new conversation using the sidebar.")
    else:
        messages_container = st.container()
        with messages_container:
            st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
            messages = db.get_messages(selected_session_id)
            conversation_history = []
            for role, content, timestamp in messages:
                formatted_time = datetime.fromisoformat(timestamp).strftime(
                    "%a, %b %d, %Y at %H:%M"
                )
                with st.chat_message(role):
                    st.write(content)
                    st.caption(
                        f"{'Sent' if role == 'user' else 'Received'} on {formatted_time}"
                    )
                conversation_history.append({"role": role, "content": content})
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="fixed-chat-input">
                <style>
                    .stChatInput {
                        position:fixed;
                        bottom: 4.5rem;
                        z-index: 100;
                    }
                </style>
            </div>
            """,
            unsafe_allow_html=True,
        )
        question = st.chat_input("✍️ Ask about your documents...", key="chat_input")
        if question:
            session_files = get_session_files(selected_session_id)
            if not session_files:
                st.error("Please upload some documents first!")
            else:
                with messages_container:
                    with st.chat_message("user"):
                        st.write(question)
                        conversation_history.append(
                            {"role": "user", "content": question}
                        )
                    with st.chat_message("assistant"):
                        with st.spinner("🧠 Thinking..."):
                            query_engine = st.session_state["query_engines"].get(
                                selected_session_id
                            )
                            if not query_engine:
                                query_engine = QueryEngine(
                                    os.getenv("GROQ_API_KEY"),
                                    session_id=selected_session_id,
                                )
                                st.session_state["query_engines"][
                                    selected_session_id
                                ] = query_engine
                            response = query_engine.query(
                                question, conversation_history=conversation_history
                            )
                            st.write(response)
                            conversation_history.append(
                                {"role": "assistant", "content": response}
                            )
                            db.add_message(selected_session_id, "user", question)
                            db.add_message(selected_session_id, "assistant", response)
                            current_name = db.get_conversation_name(selected_session_id)
                            if current_name == "New Conversation":
                                suggested_name = db.suggest_conversation_name(
                                    selected_session_id
                                )
                                if suggested_name != "New Conversation":
                                    with st.status(
                                        "✨ Generating conversation name...",
                                        expanded=True,
                                    ) as status:
                                        db.update_conversation_name(
                                            selected_session_id, suggested_name
                                        )
                                        status.update(
                                            label=f"✨ Named conversation: {suggested_name}"
                                        )
                                        time.sleep(1)
                                        st.rerun()
                            st.rerun()

with tab2:
    st.header("📖 Conversation History")
    conversations = db.get_conversation_details()
    if not conversations:
        st.info("No conversations yet. Start a new conversation to begin!")
    if "viewing_conversation" not in st.session_state:
        st.session_state.viewing_conversation = None
    for session_id, created_at, msg_count, file_count, files in conversations:
        created_date = datetime.fromisoformat(created_at).strftime("%B %d, %Y at %H:%M")
        conv_name = db.get_conversation_name(session_id)
        with st.container():
            st.markdown(
                f"""
            <div class="conversation-box">
                <div class="conversation-header">
                    <h3>{conv_name}</h3>
                    <p style="color: #666; font-size: 0.9em;">{created_date}</p>
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
                    st.session_state.viewing_conversation = (
                        None
                        if st.session_state.viewing_conversation == session_id
                        else session_id
                    )
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{session_id}"):
                    if st.session_state.get("selected_session_id") == session_id:
                        st.session_state.selected_session_id = None
                    db.delete_conversation(session_id)
                    st.rerun()
            if st.session_state.viewing_conversation == session_id:
                with st.expander("Conversation Details", expanded=True):
                    messages = db.get_messages(session_id)
                    if not messages:
                        st.info("No messages in this conversation.")
                    else:
                        for role, content, timestamp in messages:
                            formatted_time = datetime.fromisoformat(timestamp).strftime(
                                "%a, %b %d, %Y at %H:%M"
                            )
                            with st.chat_message(role):
                                st.write(content)
                                st.caption(
                                    f"{'Sent' if role == 'user' else 'Received'} on {formatted_time}"
                                )

st.markdown("</div>", unsafe_allow_html=True)

# Sidebar Footer
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

db.close()
