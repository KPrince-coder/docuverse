import streamlit as st
from datetime import datetime


def render_history(db):
    """Render the History tab."""
    st.header("📖 Conversation History")

    with st.spinner("Loading conversation history..."):
        conv_details = db.get_conversation_details()

    if not conv_details:
        st.info("No conversations yet. Start a new conversation to begin!")
        return

    if "viewing_conversation" not in st.session_state:
        st.session_state.viewing_conversation = None

    # Custom CSS for better layout and styling
    st.markdown(
        """
        <style>
        .conversation-box {
            border: 1px solid #ddd;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 5px;
        }
        .conversation-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            margin-bottom: 0.5rem;
        }
        .conversation-name {
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .conversation-date {
            flex-shrink: 0;
            color: #666;
            font-size: 0.9em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    for session_id, created_at, msg_count, file_count, files in conv_details:
        # Format the conversation creation date safely
        try:
            formatted_date = datetime.fromisoformat(created_at).strftime(
                "%a, %b %d, %Y at %H:%M"
            )
        except Exception:
            formatted_date = created_at

        conversation_name = db.get_conversation_name(session_id)
        file_list = f"Files: {files}" if files else "No files uploaded"

        st.markdown(
            f"""
            <div class="conversation-box">
                <div class="conversation-header">
                    <div class="conversation-name">
                        <h3>{conversation_name}</h3>
                    </div>
                    <div class="conversation-date">
                        {formatted_date}
                    </div>
                </div>
                <p>📝 {msg_count} messages • 📎 {file_count} files</p>
                <div class="file-list">
                    {file_list}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns([4, 1])
        with cols[0]:
            if st.button("View Details", key=f"view_{session_id}"):
                st.session_state.viewing_conversation = (
                    None
                    if st.session_state.viewing_conversation == session_id
                    else session_id
                )
                st.rerun()
        with cols[1]:
            if st.button("🗑️ Delete", key=f"delete_{session_id}"):
                db.delete_conversation(session_id)
                st.rerun()

        if st.session_state.viewing_conversation == session_id:
            with st.expander("Conversation Details", expanded=True):
                with st.spinner("Loading messages..."):
                    msgs = db.get_messages(session_id)
                if not msgs:
                    st.info("No messages in this conversation.")
                else:
                    for role, content, timestamp in msgs:
                        try:
                            formatted = datetime.fromisoformat(timestamp).strftime(
                                "%a, %b %d, %Y at %H:%M"
                            )
                        except Exception:
                            formatted = timestamp
                        st.chat_message(role).write(content)
                        st.caption(
                            f"{'Sent' if role == 'user' else 'Received'} on {formatted}"
                        )
