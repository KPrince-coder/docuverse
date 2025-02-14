import os
from concurrent.futures import ThreadPoolExecutor
import threading
import streamlit as st
from utils.query_engine import QueryEngine


def handle_file_upload(uploaded_file, session_id, db):
    """Handle file upload with optimized 1MB chunking."""
    try:
        UPLOAD_DIR = "data/uploads"
        session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(session_upload_dir, exist_ok=True)
        file_path = os.path.join(session_upload_dir, uploaded_file.name)
        if db.add_file(session_id, file_path, uploaded_file.name):
            CHUNK_SIZE = 1024 * 1024  # 1MB
            with open(file_path, "wb") as f:
                while True:
                    chunk = uploaded_file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
            return True
        return False
    except Exception:
        return False


def process_uploads(files, session_id, db):
    """Process multiple file uploads concurrently."""
    results = []
    with ThreadPoolExecutor(max_workers=min(len(files), 4)) as executor:
        futures = {
            executor.submit(handle_file_upload, f, session_id, db): f for f in files
        }
        for future in futures:
            results.append(future.result())
    # Trigger background indexing so the user can interact immediately.
    query_engine = st.session_state["query_engines"].get(session_id)
    if query_engine:
        threading.Thread(
            target=query_engine.index_manager.build_index, daemon=True
        ).start()
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
    """
    Save a note that combines the user question as header and the assistant response.
    Returns the path of the saved note, or None on error.
    """
    NOTES_DIR = "data/notes"
    os.makedirs(NOTES_DIR, exist_ok=True)
    filename = f"{note_title}.{file_type}"
    file_path = os.path.join(NOTES_DIR, filename)
    try:
        content = f"# {user_question}\n\n---\n\n{assistant_response}"
        if file_type == "txt":
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif file_type == "pdf":
            try:
                from fpdf import FPDF
            except ImportError:
                return None
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in content.split("\n"):
                pdf.cell(200, 10, txt=line, ln=True)
            pdf.output(file_path)
        elif file_type == "docx":
            try:
                from docx import Document
            except ImportError:
                return None
            document = Document()
            document.add_heading(user_question, level=1)
            document.add_paragraph(assistant_response)
            document.save(file_path)
        return file_path
    except Exception:
        return None
