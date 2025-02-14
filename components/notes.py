import streamlit as st
import os


def render_notes():
    """Render the Notes tab: list saved notes with options to view, rename, download, and delete."""
    st.header("📝 Saved Notes")
    NOTES_DIR = "data/notes"
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)
    note_files = sorted(os.listdir(NOTES_DIR))
    if not note_files:
        st.info(
            "No notes saved yet. Use the 'Note' button under an AI response to save one."
        )
    else:
        for nf in note_files:
            note_path = os.path.join(NOTES_DIR, nf)
            with st.expander(nf, expanded=False):
                try:
                    with open(note_path, "rb") as f:
                        content_bytes = f.read()
                    # If it's a text file, preview it; otherwise, inform user.
                    if nf.lower().endswith(".txt"):
                        content = content_bytes.decode("utf-8", errors="replace")
                        st.markdown(content)
                    else:
                        st.info(
                            "Preview not available for this file type. Please download to view the note."
                        )
                except Exception as e:
                    st.error(f"Error reading note: {e}")
                cols = st.columns([1, 1, 1])
                # Rename (Edit Name) button
                with cols[0]:
                    if st.button("Edit Name", key=f"edit_{nf}"):
                        new_name = st.text_input("New note name", value=nf)
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("Confirm", key=f"confirm_{nf}"):
                                new_path = os.path.join(NOTES_DIR, new_name)
                                try:
                                    os.rename(note_path, new_path)
                                    st.success("Renamed successfully")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Rename failed: {e}")
                        with col_cancel:
                            if st.button("Cancel", key=f"cancel_{nf}"):
                                st.rerun()
                # Download button
                with cols[1]:
                    with open(note_path, "rb") as f:
                        file_data = f.read()
                    st.download_button(label="Download", data=file_data, file_name=nf)
                # Delete button
                with cols[2]:
                    if st.button("Delete", key=f"delete_{nf}"):
                        try:
                            os.remove(note_path)
                            st.success("Note deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Deletion failed: {e}")
