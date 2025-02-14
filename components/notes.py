import streamlit as st
import os
import time
from typing import Optional, Tuple
import pymupdf  # Correct import for PyMuPDF
from docx import Document
import logging
from datetime import datetime
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileReader:
    """Class to handle different file types reading operations."""

    @staticmethod
    def read_txt(file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Read content from a text file.

        Args:
            file_path: Path to the text file

        Returns:
            Tuple of (content, error_message)
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read().decode("utf-8", errors="replace")
            return content, None
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return None, f"Error reading text file: {str(e)}"

    @staticmethod
    def read_pdf(file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Read content from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (content, error_message)
        """
        try:
            pdf_content = []
            doc = pymupdf.open(file_path)
            for page in doc:
                pdf_content.append(page.get_text())
            doc.close()
            return "\n\n".join(pdf_content), None
        except Exception as e:
            logger.error(f"Error reading PDF file {file_path}: {e}")
            return None, f"Error reading PDF file: {str(e)}"

    @staticmethod
    def read_docx(file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Read content from a DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Tuple of (content, error_message)
        """
        try:
            doc = Document(file_path)
            content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return content, None
        except Exception as e:
            logger.error(f"Error reading DOCX file {file_path}: {e}")
            return None, f"Error reading DOCX file: {str(e)}"


def get_file_content(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Get content from a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        Tuple of (content, error_message)
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    file_handlers = {
        ".txt": FileReader.read_txt,
        ".pdf": FileReader.read_pdf,
        ".docx": FileReader.read_docx,
    }

    handler = file_handlers.get(file_extension)
    if handler:
        return handler(file_path)
    return None, f"Unsupported file type: {file_extension}"


def render_notes():
    """Render the Notes tab with improved note management."""
    st.header("📝 Saved Notes")

    db = st.session_state.get("db")
    if not db:
        st.error("Database connection not available")
        return

    notes = db.get_notes()
    if not notes:
        st.info(
            "No notes saved yet. Use the 'Note' button under an AI response to save one."
        )
        return

    # Track rename and delete states
    if "note_rename" not in st.session_state:
        st.session_state.note_rename = {}
    if "pending_note_deletion" not in st.session_state:
        st.session_state.pending_note_deletion = None

    for title, content, file_path, file_type, created_at, conversation_id in notes:
        # Skip if file doesn't exist anymore
        if not os.path.exists(file_path):
            # Clean up database entry if file is missing
            db.delete_note(file_path)
            continue

        with st.expander(f"📝 {title}.{file_type}", expanded=False):
            # Note metadata
            created_date = datetime.fromisoformat(created_at).strftime(
                "%B %d, %Y at %H:%M"
            )
            st.caption(f"Created on {created_date}")

            # Read the actual file content using PyMuPDF or python-docx if needed
            file_content, error = get_file_content(file_path)
            if error:
                st.error(error)
            else:
                # Show the content in the UI
                # For large PDFs/docx, consider a text area or other approach
                st.markdown(file_content)

            # Action buttons in columns
            col1, col2, col3 = st.columns(3)

            # Rename functionality
            with col1:
                if file_path in st.session_state.note_rename:
                    new_title = st.text_input(
                        "New title", value=title, key=f"new_title_{file_path}"
                    )
                    if st.button("Save", key=f"save_rename_{file_path}"):
                        if db.update_note_title(file_path, new_title):
                            # Update the file name on disk
                            new_file_path = os.path.join(
                                os.path.dirname(file_path), f"{new_title}.{file_type}"
                            )
                            try:
                                os.rename(file_path, new_file_path)
                                st.success("Title updated!")
                                del st.session_state.note_rename[file_path]
                                st.rerun()
                            except Exception as e:
                                logger.error(f"Error renaming file: {e}")
                                st.error("Failed to rename file")
                    if st.button("Cancel", key=f"cancel_rename_{file_path}"):
                        del st.session_state.note_rename[file_path]
                        st.rerun()
                else:
                    if st.button("✏️ Rename", key=f"rename_{file_path}"):
                        st.session_state.note_rename[file_path] = True
                        st.rerun()

            # Download functionality
            with col2:
                try:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="💾 Download",
                            data=f.read(),
                            file_name=os.path.basename(file_path),
                            key=f"download_{file_path}",
                        )
                except Exception as e:
                    st.error(f"Error loading file: {e}")

            # Delete functionality with confirmation
            with col3:
                if st.session_state.pending_note_deletion == file_path:
                    # Show confirmation buttons
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button("✓", key=f"confirm_delete_{file_path}"):
                            try:
                                # Delete file from disk first
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                # Then remove from database
                                if db.delete_note(file_path):
                                    st.success("Note deleted!")
                                    st.session_state.pending_note_deletion = None
                                    time.sleep(
                                        0.5
                                    )  # Brief pause to show success message
                                    st.rerun()
                                else:
                                    st.error("Failed to delete note from database")
                            except Exception as e:
                                logger.error(f"Error deleting note: {e}")
                                st.error(f"Failed to delete note: {str(e)}")
                    with cancel_col:
                        if st.button("×", key=f"cancel_delete_{file_path}"):
                            st.session_state.pending_note_deletion = None
                            st.rerun()
                else:
                    if st.button("🗑️", key=f"delete_{file_path}"):
                        st.session_state.pending_note_deletion = file_path
                        st.rerun()
