# import streamlit as st
# import os
# from typing import Optional, Tuple
# import pymupdf  # Correct import for PyMuPDF
# from docx import Document
# import logging
# from datetime import datetime

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class FileReader:
#     """Class to handle different file types reading operations."""

#     @staticmethod
#     def read_txt(file_path: str) -> Tuple[Optional[str], Optional[str]]:
#         """Read content from a text file.

#         Args:
#             file_path: Path to the text file

#         Returns:
#             Tuple of (content, error_message)
#         """
#         try:
#             with open(file_path, "rb") as f:
#                 content = f.read().decode("utf-8", errors="replace")
#             return content, None
#         except Exception as e:
#             logger.error(f"Error reading text file {file_path}: {e}")
#             return None, f"Error reading text file: {str(e)}"

#     @staticmethod
#     def read_pdf(file_path: str) -> Tuple[Optional[str], Optional[str]]:
#         """Read content from a PDF file.

#         Args:
#             file_path: Path to the PDF file

#         Returns:
#             Tuple of (content, error_message)
#         """
#         try:
#             pdf_content = []
#             # Correct PyMuPDF usage
#             doc = pymupdf.open(file_path)
#             for page in doc:
#                 pdf_content.append(page.get_text())
#             doc.close()  # Properly close the document
#             return "\n\n".join(pdf_content), None
#         except Exception as e:
#             logger.error(f"Error reading PDF file {file_path}: {e}")
#             return None, f"Error reading PDF file: {str(e)}"

#     @staticmethod
#     def read_docx(file_path: str) -> Tuple[Optional[str], Optional[str]]:
#         """Read content from a DOCX file.

#         Args:
#             file_path: Path to the DOCX file

#         Returns:
#             Tuple of (content, error_message)
#         """
#         try:
#             doc = Document(file_path)
#             content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
#             return content, None
#         except Exception as e:
#             logger.error(f"Error reading DOCX file {file_path}: {e}")
#             return None, f"Error reading DOCX file: {str(e)}"


# def get_file_content(file_path: str) -> Tuple[Optional[str], Optional[str]]:
#     """Get content from a file based on its extension.

#     Args:
#         file_path: Path to the file

#     Returns:
#         Tuple of (content, error_message)
#     """
#     file_extension = os.path.splitext(file_path)[1].lower()

#     file_handlers = {
#         ".txt": FileReader.read_txt,
#         ".pdf": FileReader.read_pdf,
#         ".docx": FileReader.read_docx,
#     }

#     handler = file_handlers.get(file_extension)
#     if handler:
#         return handler(file_path)
#     return None, f"Unsupported file type: {file_extension}"


# def render_notes():
#     """Render the Notes tab with improved note management."""
#     st.header("📝 Saved Notes")

#     # Get database instance from session state
#     db = st.session_state.get("db")
#     if not db:
#         st.error("Database connection not available")
#         return

#     notes = db.get_notes()
#     if not notes:
#         st.info(
#             "No notes saved yet. Use the 'Note' button under an AI response to save one."
#         )
#         return

#     # Ensure rename states are initialized
#     if "note_rename" not in st.session_state:
#         st.session_state.note_rename = {}

#     for title, content, file_path, file_type, created_at, conversation_id in notes:
#         with st.expander(f"📝 {title}", expanded=False):
#             # Note metadata
#             created_date = datetime.fromisoformat(created_at).strftime(
#                 "%B %d, %Y at %H:%M"
#             )
#             st.caption(f"Created on {created_date}")

#             # Note content preview
#             if file_type == "txt":
#                 st.markdown(content)
#             else:
#                 st.info(f"This note is saved as a {file_type.upper()} file")

#             # Action buttons in columns
#             col1, col2, col3 = st.columns(3)

#             # Rename functionality
#             with col1:
#                 if file_path in st.session_state.note_rename:
#                     # Show rename input and confirm/cancel buttons
#                     new_title = st.text_input(
#                         "New title", value=title, key=f"new_title_{file_path}"
#                     )
#                     if st.button("Save", key=f"save_rename_{file_path}"):
#                         if db.update_note_title(file_path, new_title):
#                             st.success("Title updated!")
#                             del st.session_state.note_rename[file_path]
#                             st.rerun()
#                     if st.button("Cancel", key=f"cancel_rename_{file_path}"):
#                         del st.session_state.note_rename[file_path]
#                         st.rerun()
#                 else:
#                     if st.button("✏️ Rename", key=f"rename_{file_path}"):
#                         st.session_state.note_rename[file_path] = True
#                         st.rerun()

#             # Download button
#             with col2:
#                 try:
#                     with open(file_path, "rb") as f:
#                         st.download_button(
#                             label="💾 Download",
#                             data=f.read(),
#                             file_name=os.path.basename(file_path),
#                             key=f"download_{file_path}",
#                         )
#                 except Exception as e:
#                     st.error(f"Error loading file: {e}")

#             # Delete button with confirmation
#             with col3:
#                 if st.button("🗑️ Delete", key=f"delete_{file_path}"):
#                     if st.button(
#                         "Confirm deletion?", key=f"confirm_delete_{file_path}"
#                     ):
#                         try:
#                             if os.path.exists(file_path):
#                                 os.remove(file_path)
#                             if db.delete_note(file_path):
#                                 st.success("Note deleted!")
#                                 st.rerun()
#                         except Exception as e:
#                             st.error(f"Error deleting note: {e}")


import streamlit as st
import os
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

    # Get database instance from session state
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

    # Track rename states
    if "note_rename" not in st.session_state:
        st.session_state.note_rename = {}

    # Track pending note deletion
    if "pending_delete_note" not in st.session_state:
        st.session_state.pending_delete_note = None

    for title, db_content, file_path, file_type, created_at, conversation_id in notes:
        # Ensure the displayed title includes the extension (e.g., "paul.txt")
        display_title = title
        if not display_title.endswith(f".{file_type}"):
            display_title += f".{file_type}"

        with st.expander(f"📝 {display_title}", expanded=False):
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

            # ----------------- RENAME -----------------
            with col1:
                if file_path in st.session_state.note_rename:
                    # Show rename input and confirm/cancel buttons
                    new_title = st.text_input(
                        "New title", value=title, key=f"new_title_{file_path}"
                    )
                    if st.button("Save", key=f"save_rename_{file_path}"):
                        if db.update_note_title(file_path, new_title):
                            st.success("Title updated!")
                            del st.session_state.note_rename[file_path]
                            st.rerun()
                    if st.button("Cancel", key=f"cancel_rename_{file_path}"):
                        del st.session_state.note_rename[file_path]
                        st.rerun()
                else:
                    if st.button("✏️ Rename", key=f"rename_{file_path}"):
                        st.session_state.note_rename[file_path] = True
                        st.rerun()

            # ----------------- DOWNLOAD (no rerun) -----------------
            with col2:
                try:
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                    b64 = base64.b64encode(file_data).decode()
                    download_filename = os.path.basename(file_path)
                    download_button_html = f'''
                        <a href="data:file/octet-stream;base64,{b64}" download="{download_filename}">
                            <button style="cursor: pointer;">💾 Download</button>
                        </a>
                    '''
                    st.markdown(download_button_html, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error loading file for download: {e}")

            # ----------------- DELETE (2-step confirmation) -----------------
            with col3:
                if st.session_state.pending_delete_note == file_path:
                    # Show confirm/cancel buttons
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button("Confirm", key=f"confirm_delete_{file_path}"):
                            try:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                if db.delete_note(file_path):
                                    st.success("Note deleted!")
                                    st.session_state.pending_delete_note = None
                                    st.rerun()
                                else:
                                    st.error("Failed to delete from database.")
                            except Exception as e:
                                st.error(f"Error deleting note: {e}")
                    with cancel_col:
                        if st.button("Cancel", key=f"cancel_delete_{file_path}"):
                            st.session_state.pending_delete_note = None
                            st.rerun()
                else:
                    if st.button("🗑️ Delete", key=f"delete_{file_path}"):
                        st.session_state.pending_delete_note = file_path
                        st.rerun()
