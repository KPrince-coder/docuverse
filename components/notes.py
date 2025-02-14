# import streamlit as st
# import os


# def render_notes():
#     """Render the Notes tab: list saved notes with options to view, rename, download, and delete."""
#     st.header("📝 Saved Notes")
#     NOTES_DIR = "data/notes"
#     if not os.path.exists(NOTES_DIR):
#         os.makedirs(NOTES_DIR)
#     note_files = sorted(os.listdir(NOTES_DIR))
#     if not note_files:
#         st.info(
#             "No notes saved yet. Use the 'Note' button under an AI response to save one."
#         )
#     else:
#         for nf in note_files:
#             note_path = os.path.join(NOTES_DIR, nf)
#             with st.expander(nf, expanded=False):
#                 try:
#                     with open(note_path, "rb") as f:
#                         content_bytes = f.read()
#                     # If it's a text file, preview it; otherwise, inform user.
#                     if nf.lower().endswith(".txt"):
#                         content = content_bytes.decode("utf-8", errors="replace")
#                         st.markdown(content)
#                     else:
#                         st.info(
#                             "Preview not available for this file type. Please download to view the note."
#                         )
#                 except Exception as e:
#                     st.error(f"Error reading note: {e}")
#                 cols = st.columns([1, 1, 1])
#                 # Rename (Edit Name) button
#                 with cols[0]:
#                     if st.button("Edit Name", key=f"edit_{nf}"):
#                         new_name = st.text_input("New note name", value=nf)
#                         col_confirm, col_cancel = st.columns(2)
#                         with col_confirm:
#                             if st.button("Confirm", key=f"confirm_{nf}"):
#                                 new_path = os.path.join(NOTES_DIR, new_name)
#                                 try:
#                                     os.rename(note_path, new_path)
#                                     st.success("Renamed successfully")
#                                     st.rerun()
#                                 except Exception as e:
#                                     st.error(f"Rename failed: {e}")
#                         with col_cancel:
#                             if st.button("Cancel", key=f"cancel_{nf}"):
#                                 st.rerun()
#                 # Download button
#                 with cols[1]:
#                     with open(note_path, "rb") as f:
#                         file_data = f.read()
#                     st.download_button(label="Download", data=file_data, file_name=nf)
#                 # Delete button
#                 with cols[2]:
#                     if st.button("Delete", key=f"delete_{nf}"):
#                         try:
#                             os.remove(note_path)
#                             st.success("Note deleted")
#                             st.rerun()
#                         except Exception as e:
#                             st.error(f"Deletion failed: {e}")


import streamlit as st
import os
from typing import Optional, Tuple
import pymupdf  # Correct import for PyMuPDF
from docx import Document
import logging

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
            # Correct PyMuPDF usage
            doc = pymupdf.open(file_path)
            for page in doc:
                pdf_content.append(page.get_text())
            doc.close()  # Properly close the document
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
        return

    for nf in note_files:
        note_path = os.path.join(NOTES_DIR, nf)
        with st.expander(nf, expanded=False):
            try:
                # Get file content based on type
                content, error = get_file_content(note_path)

                if error:
                    st.error(error)
                elif content:
                    # For text-based content (txt, pdf, docx), display the content
                    st.markdown(content)
                else:
                    st.info(
                        "Preview not available for this file type. Please download to view the note."
                    )

            except Exception as e:
                logger.error(f"Error processing file {note_path}: {e}")
                st.error(f"Error reading note: {e}")

            # Action buttons
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
                                logger.error(f"Error renaming file {note_path}: {e}")
                                st.error(f"Rename failed: {e}")

                    with col_cancel:
                        if st.button("Cancel", key=f"cancel_{nf}"):
                            st.rerun()

            # Download button
            with cols[1]:
                try:
                    with open(note_path, "rb") as f:
                        file_data = f.read()
                    st.download_button(label="Download", data=file_data, file_name=nf)
                except Exception as e:
                    logger.error(f"Error preparing download for {note_path}: {e}")
                    st.error("Download failed")

            # Delete button
            with cols[2]:
                if st.button("Delete", key=f"delete_{nf}"):
                    try:
                        os.remove(note_path)
                        st.success("Note deleted")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error deleting file {note_path}: {e}")
                        st.error(f"Deletion failed: {e}")
