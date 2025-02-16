import streamlit as st
import os

from datetime import datetime

from components.utils import (
    process_uploads,
    rerun_assistant_message,
    delete_chat_message_pair,
    save_note_and_get_path,
)


# Define the modal using the st.dialog decorator.
@st.dialog("Save Note")
def save_note_modal():
    note_title = st.text_input(
        "Note Title", value=f"Note {st.session_state.note_to_save['timestamp']}"
    )
    file_type = st.selectbox("File Type", options=["txt", "pdf", "docx"])
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Confirm", key="confirm save note"):
            saved_path = save_note_and_get_path(
                st.session_state.note_to_save["user"],
                st.session_state.note_to_save["assistant"],
                note_title,
                file_type,
            )
            if saved_path:
                st.success(f"Note saved as {saved_path}")
            else:
                st.error("Failed to save note.")
            st.session_state.note_to_save = None
            st.rerun()
    with col_cancel:
        if st.button("Cancel", key="cancel note saving"):
            st.session_state.note_to_save = None
            st.rerun()


def render_upload_chat(session_id, db):
    """Render the Upload & Chat tab."""
    if not session_id:
        st.warning("Please start a new conversation before uploading files.")
        return

    # Check for API key before allowing chat
    if not st.session_state.get("api_key"):
        st.warning(
            "Please enter your GROQ API key in the sidebar to use the chat feature."
        )
        return

    UPLOAD_DIR = "data/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    st.subheader("📂 Upload Files")
    uploaded_files = st.file_uploader(
        "Upload documents to chat about",
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

    # Display Uploaded Files
    files = db.get_conversation_files(session_id)
    if files:
        st.subheader("📄 Uploaded Files")
        for file_path, file_name in files:
            st.text(f"• {file_name}")

    # Chat Section: Group messages as pairs (user prompt and its AI response)
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
            # Group a user message with the following assistant message if available.
            role, content, timestamp = messages[i]
            if (
                role == "user"
                and i + 1 < len(messages)
                and messages[i + 1][0] == "assistant"
            ):
                user_msg = messages[i]
                ai_msg = messages[i + 1]
                with st.chat_message("user"):
                    st.write(user_msg[1])
                    formatted_user = datetime.fromisoformat(user_msg[2]).strftime(
                        "%a, %b %d, %Y at %H:%M"
                    )
                    st.caption(f"Sent on {formatted_user}")
                with st.chat_message("assistant"):
                    st.write(ai_msg[1])
                    formatted_ai = datetime.fromisoformat(ai_msg[2]).strftime(
                        "%a, %b %d, %Y at %H:%M"
                    )
                    st.caption(f"Received on {formatted_ai}")
                    cols = st.columns(3, gap="small")
                    # Save Note button appears only for an AI response following a user message.
                    if cols[0].button("Note", key=f"note_{ai_msg[2]}"):
                        st.session_state.note_to_save = {
                            "user": user_msg[1],
                            "assistant": ai_msg[1],
                            "timestamp": ai_msg[2],
                        }
                        save_note_modal()  # Open the modal dialog.
                    else:
                        cols[0].empty()
                    # Rerun button: reinitialize query engine to avoid cached response.
                    if cols[1].button("Rerun", key=f"rerun_{ai_msg[2]}"):
                        with st.spinner("🧠 Thinking..."):
                            rerun_assistant_message(
                                session_id, ai_msg[2], user_msg[1], db
                            )
                        st.rerun()
                    else:
                        cols[1].empty()
                    # Delete button: deletes both the user prompt and the AI response.
                    if cols[2].button("Delete", key=f"delete_{ai_msg[2]}"):
                        if delete_chat_message_pair(
                            session_id, user_msg[2], ai_msg[2], db
                        ):
                            st.rerun()
                    else:
                        cols[2].empty()
                conversation_history.append(
                    {"role": "user", "content": user_msg[1], "timestamp": user_msg[2]}
                )
                conversation_history.append(
                    {"role": "assistant", "content": ai_msg[1], "timestamp": ai_msg[2]}
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
                    st.rerun()
