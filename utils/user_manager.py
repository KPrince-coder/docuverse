import streamlit as st
import hashlib
import uuid
import json
from typing import Optional
import streamlit.components.v1 as components


class UserManager:
    """Manages user identification and data isolation."""

    def __init__(self):
        self._init_user_id()

    def _init_user_id(self):
        """Initialize or retrieve user ID using browser fingerprint."""
        components.html(
            """
            <script>
            function getBrowserFingerprint() {
                const fingerprint = {
                    userAgent: navigator.userAgent,
                    language: navigator.language,
                    platform: navigator.platform,
                    screenResolution: `${window.screen.width}x${window.screen.height}`,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                };
                
                // Create a stable fingerprint hash
                const fingerprintStr = JSON.stringify(fingerprint);
                const hash = Array.from(
                    new Uint8Array(
                        new TextEncoder().encode(fingerprintStr)
                    )
                ).map(b => b.toString(16).padStart(2, '0')).join('');
                
                // Store in localStorage
                localStorage.setItem('docuverse_user_id', hash);
                
                // Send to Streamlit
                window.parent.postMessage({
                    type: 'user_fingerprint',
                    hash: hash
                }, '*');
            }
            
            // Generate fingerprint on load
            getBrowserFingerprint();
            </script>
            """,
            height=0,
        )

        # Get or create user ID
        if "user_id" not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())

    @staticmethod
    def get_user_id() -> str:
        """Get current user's ID."""
        if "user_id" not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())
        return st.session_state.user_id

    @staticmethod
    def get_data_key(key: str) -> str:
        """Get user-specific storage key."""
        user_id = UserManager.get_user_id()
        return f"{user_id}_{key}"

    @staticmethod
    def clear_user_data():
        """Clear all user data from local storage."""
        components.html(
            """
            <script>
            const userId = localStorage.getItem('docuverse_user_id');
            if (userId) {
                const store = JSON.parse(localStorage.getItem('docuverse_data') || '{}');
                delete store[userId];
                localStorage.setItem('docuverse_data', JSON.stringify(store));
            }
            </script>
            """,
            height=0,
        )
