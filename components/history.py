import streamlit as st
from datetime import datetime


def render_history(db):
    """Render the History tab."""
    st.header("📖 Conversation History")
    conv_details = db.get_conversation_details()
    if not conv_details:
        st.info("No conversations yet. Start a new conversation to begin!")
        return

    if "viewing_conversation" not in st.session_state:
        st.session_state.viewing_conversation = None

    # Add custom CSS for better layout
    st.markdown(
        """
        <style>
        .conversation-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;  /* Add space between name and date */
        }
        .conversation-name {
            flex: 1;  /* Take available space */
            min-width: 0;  /* Allow text truncation */
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .conversation-date {
            flex-shrink: 0;  /* Prevent date from shrinking */
            color: #666;
            font-size: 0.9em;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    for session_id, created_at, msg_count, file_count, files in conv_details:
        # Format the date like the chat screen
        formatted_date = datetime.fromisoformat(created_at).strftime(
            "%a, %b %d, %Y at %H:%M"
        )

        st.markdown(
            f"""
            <div class="conversation-box">
                <div class="conversation-header">
                    <div class="conversation-name">
                        <h3>{db.get_conversation_name(session_id)}</h3>
                    </div>
                    <div class="conversation-date">
                        {formatted_date}
                    </div>
                </div>
                <p>📝 {msg_count} messages • 📎 {file_count} files</p>
                <div class="file-list">
                    {"Files: " + files if files else "No files uploaded"}
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
                msgs = db.get_messages(session_id)
                if not msgs:
                    st.info("No messages in this conversation.")
                else:
                    for role, content, timestamp in msgs:
                        formatted = datetime.fromisoformat(timestamp).strftime(
                            "%a, %b %d, %Y at %H:%M"
                        )
                        st.chat_message(role).write(content)
                        st.caption(
                            f"{'Sent' if role == 'user' else 'Received'} on {formatted}"
                        )
