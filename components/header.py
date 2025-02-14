import streamlit as st


def render_header():
    """Render the sticky header."""
    st.markdown(
        '<div class="fixed-header">📚 DocuVerse: Your Document Intelligence Assistant</div>',
        unsafe_allow_html=True,
    )
