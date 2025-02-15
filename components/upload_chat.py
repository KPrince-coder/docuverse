import streamlit as st
import os
import threading
import time
import logging
from datetime import datetime


from .utils import (
    process_uploads,
    rerun_assistant_message,
    delete_chat_message_pair,
    save_note_and_get_path,
)

# Configure logger
logger = logging.getLogger(__name__)

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


@st.dialog("Save Note")
def save_note_modal(db):
    """Modal dialog for saving notes with auto-generated title."""
    try:
        # Generate default title from user's question
        user_question = st.session_state.note_to_save["user"]
        default_title = generate_note_title(user_question)

        # Allow user to edit title with auto-generated default
        note_title = st.text_input(
            "Note Title",
            value=default_title,
            placeholder="Enter a title for your note",
            key="note_title_input",
            help="A title has been generated from your question. Feel free to modify it.",
        )

        file_type = st.selectbox(
            "File Type", options=["txt", "pdf", "docx"], key="note_file_type"
        )

        col_confirm, col_cancel = st.columns(2)

        with col_confirm:
            if st.button("Save", key="confirm_save_note"):
                if not note_title:
                    st.error("Please enter a title for the note")
                    return

                saved_path = save_note_and_get_path(
                    st.session_state.note_to_save["user"],
                    st.session_state.note_to_save["assistant"],
                    note_title,
                    file_type,
                    db,
                )

                if saved_path:
                    st.success("Note saved!")
                    st.session_state.note_to_save = None
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to save note")

        with col_cancel:
            if st.button("Cancel", key="cancel_note"):
                st.session_state.note_to_save = None
                st.rerun()

    except Exception as e:
        logger.error(f"Error in save_note_modal: {e}")
        st.error("Failed to save note")


def generate_note_title(question: str, max_length: int = 50) -> str:
    """Generate a clean title from the user's question."""
    # Remove common question starters
    starters = [
        "what is",
        "what are",
        "how to",
        "can you",
        "please",
        "tell me about",
        "explain",
        "i want to",
        "could you",
        "would you",
    ]

    clean_question = question.lower().strip()
    for starter in starters:
        if clean_question.startswith(starter):
            clean_question = clean_question[len(starter) :].strip()
            break

    # Capitalize words and clean up
    title = " ".join(word.capitalize() for word in clean_question.split())

    # Truncate if too long
    if len(title) > max_length:
        cutoff = title[:max_length].rfind(" ")
        if cutoff == -1:
            cutoff = max_length
        title = title[:cutoff].strip() + "..."

    # Remove any invalid characters
    title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_", "."))

    return title.strip()


def render_action_buttons(
    cols,
    ai_msg_content,
    ai_msg_timestamp,
    user_msg_content,
    user_msg_timestamp,
    session_id,
    db,
):
    """Render action buttons with improved styling."""
    button_style = """
        <style>
        .stButton > button {
            background-color: transparent;
            border: none;
            padding: 0px 8px;
            font-size: 12px;
            color: #666;
            height: 25px;
        }
        .stButton > button:hover {
            background-color: #f0f0f0;
            color: #333;
        }
        </style>
    """
    st.markdown(button_style, unsafe_allow_html=True)

    # Note button
    if cols[0].button("📝", key=f"note_{ai_msg_timestamp}", help="Save as note"):
        st.session_state.note_to_save = {
            "user": user_msg_content,
            "assistant": ai_msg_content,
            "timestamp": ai_msg_timestamp,
        }
        save_note_modal(db)

    # Rerun button
    if cols[1].button(
        "🔄", key=f"rerun_{ai_msg_timestamp}", help="Regenerate response"
    ):
        with st.spinner("🧠 Thinking..."):
            rerun_assistant_message(session_id, ai_msg_timestamp, user_msg_content, db)
        st.rerun()

    # Delete button
    if cols[2].button("🗑️", key=f"delete_{ai_msg_timestamp}", help="Delete message"):
        if delete_chat_message_pair(
            session_id, user_msg_timestamp, ai_msg_timestamp, db
        ):
            st.rerun()


def render_upload_chat(session_id, db):
    """Render the Upload & Chat tab."""
    if not session_id:
        st.warning("Please start a new conversation before uploading files.")
        return

    UPLOAD_DIR = "data/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # File Upload Section
    st.subheader("📂 Upload Files")
    uploaded_files = st.file_uploader(
        "Upload documents to chat about",
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
        key=f"uploader_{session_id}",
    )
    if uploaded_files:
        with st.status("Processing files...") as status:
            existing_files = {f[1] for f in db.get_conversation_files(session_id)}
            new_files = [uf for uf in uploaded_files if uf.name not in existing_files]
            if new_files:
                results = process_uploads(new_files, session_id, db)
                successful = sum(1 for r in results if r)
                failed = len(new_files) - successful
                status.write(f"✅ Processed: {successful} files")
                if failed:
                    status.write(f"❌ Failed: {failed} files")
            st.success("Upload Complete")

    # Display Uploaded Files Section
    files = db.get_conversation_files(session_id)
    if files:
        st.subheader("📄 Uploaded Files")
        if "pending_delete" not in st.session_state:
            st.session_state.pending_delete = None

        for file_path, file_name in files:
            col1, col2 = st.columns([6, 1])
            with col1:
                st.text(f"• {file_name}")
            with col2:
                delete_key = f"delete_{file_path}"

                if st.session_state.pending_delete == file_path:
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button("✓", key=f"confirm_{delete_key}"):
                            try:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                if db.delete_file(session_id, file_path):
                                    query_engine = st.session_state[
                                        "query_engines"
                                    ].get(session_id)
                                    if query_engine:
                                        threading.Thread(
                                            target=query_engine.index_manager.build_index,
                                            daemon=True,
                                        ).start()
                                    st.success(f"Deleted {file_name}")
                                    st.session_state.pending_delete = None
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Failed to delete from database")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    with cancel_col:
                        if st.button("×", key=f"cancel_{delete_key}"):
                            st.session_state.pending_delete = None
                            st.rerun()
                else:
                    if st.button("🗑️", key=delete_key):
                        st.session_state.pending_delete = file_path
                        st.rerun()

    # Chat Section
    st.subheader("💬 Chat")
    messages_container = st.container()

    with messages_container:
        st.markdown(
            '<div id="chat_container" class="chat-messages">', unsafe_allow_html=True
        )

        messages = db.get_messages(session_id)
        conversation_history = []
        i = 0

        while i < len(messages):
            role, content, timestamp = messages[i]

            if (
                role == "user"
                and i + 1 < len(messages)
                and messages[i + 1][0] == "assistant"
            ):
                user_msg = messages[i]
                ai_msg = messages[i + 1]

                # Render user message
                with st.chat_message("user"):
                    st.write(user_msg[1])
                    formatted_user = datetime.fromisoformat(user_msg[2]).strftime(
                        "%a, %b %d, %Y at %H:%M"
                    )
                    st.caption(f"Sent on {formatted_user}")

                # Render assistant message with action buttons
                with st.chat_message("assistant"):
                    st.write(ai_msg[1])
                    formatted_ai = datetime.fromisoformat(ai_msg[2]).strftime(
                        "%a, %b %d, %Y at %H:%M"
                    )
                    st.caption(f"Received on {formatted_ai}")

                    cols = st.columns(3, gap="small")
                    render_action_buttons(
                        cols,
                        ai_msg[1],  # ai content
                        ai_msg[2],  # ai timestamp
                        user_msg[1],  # user content
                        user_msg[2],  # user timestamp
                        session_id,
                        db,
                    )

                conversation_history.extend(
                    [
                        {
                            "role": "user",
                            "content": user_msg[1],
                            "timestamp": user_msg[2],
                        },
                        {
                            "role": "assistant",
                            "content": ai_msg[1],
                            "timestamp": ai_msg[2],
                        },
                    ]
                )
                i += 2
            else:
                with st.chat_message(role):
                    st.write(content)
                    formatted = datetime.fromisoformat(timestamp).strftime(
                        "%a, %b %d, %Y at %H:%M"
                    )
                    st.caption(
                        f"{'Sent' if role == 'user' else 'Received'} on {formatted}"
                    )
                conversation_history.append(
                    {"role": role, "content": content, "timestamp": timestamp}
                )
                i += 1

        st.markdown("</div>", unsafe_allow_html=True)

    # Chat Input
    st.markdown(
        """
        <div class="fixed-chat-input">
            <style>
                .stChatInput { position: fixed; bottom: 4.5rem; z-index: 100; }
            </style>
        </div>
        """,
        unsafe_allow_html=True,
    )

    question = st.chat_input("✍️ Ask about your documents...", key="chat_input")
    if question:
        with messages_container:
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                with st.spinner("🧠 Thinking..."):
                    query_engine = st.session_state["query_engines"].get(session_id)
                    response = query_engine.query(
                        question, conversation_history=conversation_history
                    )
                    st.write(response)
                    db.add_message(session_id, "user", question)
                    db.add_message(session_id, "assistant", response)

                    # Update conversation name if not manually renamed
                    if session_id not in st.session_state.get(
                        "manually_renamed", set()
                    ):
                        current_name = db.get_conversation_name(session_id)
                        if current_name == "New Conversation":
                            suggested_name = db.suggest_conversation_name(session_id)
                            if suggested_name != "New Conversation":
                                db.update_conversation_name(session_id, suggested_name)

                    st.rerun()
