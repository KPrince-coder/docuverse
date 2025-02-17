import streamlit as st


def render_header():
    """Render the sticky header."""
    st.markdown(
        """<header class="fixed-header">
            <h1>📚 DocuVerse</h1>
            <p class="sub-text">Your Document Intelligence Assistant</p>
        </header>
        """,
        unsafe_allow_html=True,
    )
