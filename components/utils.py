import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import streamlit as st
from utils.query_engine import QueryEngine

logger = logging.getLogger(__name__)


def handle_file_upload(uploaded_file, session_id, db):
    """Handle file upload with optimized chunking and async processing."""
    try:
        UPLOAD_DIR = "data/uploads"
        session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(session_upload_dir, exist_ok=True)
        file_path = os.path.join(session_upload_dir, uploaded_file.name)

        if db.add_file(session_id, file_path, uploaded_file.name):
            # Use a larger chunk size for better performance
            CHUNK_SIZE = 1024 * 1024 * 4  # 4MB chunks

            def write_chunks():
                with open(file_path, "wb") as f:
                    while chunk := uploaded_file.read(CHUNK_SIZE):
                        f.write(chunk)

            # Run file writing in thread pool
            with ThreadPoolExecutor() as executor:
                future = executor.submit(write_chunks)
                future.result(timeout=300)  # 5 minute timeout
            return True
        return False
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return False


def process_uploads(files, session_id, db):
    """Process multiple file uploads with optimized concurrency."""
    results = []
    max_workers = min(len(files), os.cpu_count() * 2)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all file uploads
        futures = {
            executor.submit(handle_file_upload, f, session_id, db): f.name
            for f in files
        }

        # Start index building in background while files upload
        query_engine = st.session_state["query_engines"].get(session_id)
        if query_engine:
            index_thread = threading.Thread(
                target=query_engine.index_manager.build_index, daemon=True
            )
            index_thread.start()

        # Process upload results as they complete
        for future in as_completed(futures):
            file_name = futures[future]
            try:
                result = future.result(timeout=600)  # 10 minute timeout per file
                results.append(result)
                if result:
                    logger.info(f"Successfully uploaded: {file_name}")
                else:
                    logger.error(f"Failed to upload: {file_name}")
            except Exception as e:
                logger.error(f"Upload failed for {file_name}: {e}")
                results.append(False)

    return results


def rerun_assistant_message(session_id, assistant_timestamp, user_question, db):
    """
    Rerun the assistant response for a given user question.
    Delete the existing assistant message (identified by its timestamp)
    and add a new response from the query engine.
    """
    delete_chat_message(session_id, assistant_timestamp, db)
    # Reinitialize the query engine to force a fresh response.
    st.session_state["query_engines"][session_id] = QueryEngine(
        os.getenv("GROQ_API_KEY"), session_id=session_id
    )
    query_engine = st.session_state["query_engines"].get(session_id)
    if query_engine:
        new_response = query_engine.query(user_question, conversation_history=[])
        db.add_message(session_id, "assistant", new_response)


def delete_chat_message(session_id, timestamp, db):
    """Delete a single chat message identified by its timestamp."""
    try:
        cur = db.conn.cursor()
        cur.execute(
            "DELETE FROM messages WHERE session_id = ? AND timestamp = ?",
            (session_id, timestamp),
        )
        db.conn.commit()
        cur.close()
        return True
    except Exception:
        return False


def delete_chat_message_pair(session_id, user_timestamp, assistant_timestamp, db):
    """Delete a pair of chat messages (user and assistant) identified by their timestamps."""
    success_user = delete_chat_message(session_id, user_timestamp, db)
    success_assistant = delete_chat_message(session_id, assistant_timestamp, db)
    return success_user and success_assistant


def save_note_and_get_path(user_question, assistant_response, note_title, file_type):
    """Save a note with database integration."""
    NOTES_DIR = "data/notes"
    os.makedirs(NOTES_DIR, exist_ok=True)

    # Get database connection
    db = st.session_state.get("db")
    if not db:
        st.error("Database connection not available")
        return None

    try:
        # Clean up title for filename
        safe_title = "".join(
            c for c in note_title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        filename = f"{safe_title}.{file_type}"
        file_path = os.path.join(NOTES_DIR, filename)

        content = f"# {user_question}\n\n---\n\n{assistant_response}"

        # Save the file based on type
        if file_type == "txt":
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif file_type == "pdf":
            try:
                from fpdf import FPDF

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in content.split("\n"):
                    pdf.cell(200, 10, txt=line, ln=True)
                pdf.output(file_path)
            except ImportError:
                st.error(
                    "FPDF library not installed. Please install fpdf2 to save as PDF."
                )
                return None
        elif file_type == "docx":
            try:
                from docx import Document

                document = Document()
                document.add_heading(user_question, level=1)
                document.add_paragraph(assistant_response)
                document.save(file_path)
            except ImportError:
                st.error(
                    "python-docx not installed. Please install python-docx to save as DOCX."
                )
                return None

        # Add note to database
        success = db.add_note(
            title=note_title,
            content=content,
            file_path=file_path,
            file_type=file_type,
            conversation_id=st.session_state.get("selected_session_id"),
        )

        if success:
            return file_path
        else:
            if os.path.exists(file_path):
                os.remove(file_path)  # Clean up file if database operation failed
            return None

    except Exception as e:
        st.error(f"Error saving note: {e}")
        # Clean up file if it was created
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return None
