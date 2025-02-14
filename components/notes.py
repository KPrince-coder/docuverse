import streamlit as st
import os
from datetime import datetime


def render_notes():
    """Render the Notes tab with enhanced functionality."""
    st.header("📝 Saved Notes")

    # Get database instance from session state
    db = st.session_state.get("db")
    if not db:
        st.error("Database connection not available")
        return

    # Get all notes from database
    notes = db.get_notes()

    if not notes:
        st.info(
            "No notes saved yet. Use the 'Note' button under an AI response to save one."
        )
        return

    # Render each note
    for title, content, file_path, file_type, created_at, conversation_id in notes:
        with st.expander(f"📝 {title}", expanded=False):
            # Note metadata
            created_date = datetime.fromisoformat(created_at).strftime(
                "%B %d, %Y at %H:%M"
            )
            st.caption(f"Created on {created_date}")
            if conversation_id:
                st.caption(f"From conversation: {conversation_id}")

            # Note content preview
            if file_type == "txt":
                st.markdown(content)
            else:
                st.info(f"This note is saved as a {file_type.upper()} file")

            # Action buttons
            col1, col2, col3 = st.columns(3)

            # Rename button
            with col1:
                if st.button("✏️ Rename", key=f"rename_{file_path}"):
                    new_title = st.text_input(
                        "New title", value=title, key=f"new_title_{file_path}"
                    )
                    if st.button("Save", key=f"save_rename_{file_path}"):
                        if db.update_note_title(file_path, new_title):
                            st.success("Title updated!")
                            st.rerun()
                        else:
                            st.error("Failed to update title")

            # Download button
            with col2:
                try:
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                        st.download_button(
                            label="💾 Download",
                            data=file_data,
                            file_name=os.path.basename(file_path),
                            key=f"download_{file_path}",
                        )
                except Exception as e:
                    st.error(f"Error loading file: {e}")

            # Delete button
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{file_path}"):
                    if st.button(
                        "Confirm deletion?", key=f"confirm_delete_{file_path}"
                    ):
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            if db.delete_note(file_path):
                                st.success("Note deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete note")
                        except Exception as e:
                            st.error(f"Error deleting note: {e}")
