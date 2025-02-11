import streamlit as st
import os
import time
from utils.database import ConversationDB
from utils.query_engine import QueryEngine

st.set_page_config(
    page_title="DocuVerse", page_icon="📚", layout="wide", initial_sidebar_state="auto"
)


# Inject custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("styles.css")

# Initialize Query Engine and Database
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
query_engine = QueryEngine(GROQ_API_KEY)
db = ConversationDB()

# Create upload directory if it doesn't exist
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Sidebar for Conversation Management
st.sidebar.title("📚 DocuVerse")
conversations = db.get_conversations()
if conversations:
    selected_session_id = st.sidebar.selectbox(
        "Select a conversation:",
        [f"{sid} ({created_at[:10]})" for sid, created_at in conversations],
    )
    selected_session_id = selected_session_id.split(" ")[0]
else:
    selected_session_id = None

if st.sidebar.button("Start New Conversation"):
    selected_session_id = db.create_conversation()
    st.experimental_rerun()

# Main App
st.title("🚀 DocuVerse: Your Document Intelligence Assistant")

tab1, tab2, tab3 = st.tabs(["Upload", "Query", "History"])

with tab1:
    st.header("📂 Upload Files")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "pptx", "txt", "csv", "json"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        # Create a placeholder for the loading animation
        loading_placeholder = st.empty()
        loading_placeholder.markdown(
            """
        <div style="text-align:center; margin-top:20px;">
            <div class="loader"></div>
            <div class="loading-text">Processing files...</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Simulate file processing with a delay
        progress_bar = st.progress(0)
        for i, uploaded_file in enumerate(uploaded_files):
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            time.sleep(0.5)  # Simulate processing time
            progress_bar.progress((i + 1) / len(uploaded_files))

        # Rebuild the index after uploading new files
        query_engine.index_manager.build_index()

        # Clear the loading animation
        loading_placeholder.empty()
        st.success("Files uploaded and processed successfully!")

with tab2:
    st.header("🔍 Query Documents")
    question = st.text_input("Enter your question here:")
    if st.button("Ask"):
        if question and selected_session_id:
            response = query_engine.query(question)
            st.markdown(
                f"""
            <div class="response-box">
                <h3>Response:</h3>
                <p>{response}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
            db.add_message(selected_session_id, "user", question)
            db.add_message(selected_session_id, "assistant", response)
        else:
            st.warning("Please start a conversation or enter a question.")

with tab3:
    st.header("📖 Conversation History")
    if selected_session_id:
        messages = db.get_messages(selected_session_id)
        for role, content, timestamp in messages:
            st.write(f"**{role.capitalize()} ({timestamp[:16]}):** {content}")

# Footer
st.markdown(
    """
<hr style="border:1px solid #635BFF">
<footer style="text-align:center; margin-top:20px;">
    Made with ❤️ by [Your Name] | <a href="https://github.com/yourusername">GitHub</a> | <a href="https://linkedin.com/in/yourprofile">LinkedIn</a>
</footer>
""",
    unsafe_allow_html=True,
)

# Close Database Connection
db.close()
