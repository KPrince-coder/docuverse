import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Dict, Any, Optional
from utils.user_manager import UserManager
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalStorageManager:
    """Manages browser-local storage for user data persistence."""

    def __init__(self):
        self.user_manager = UserManager()
        self._init_local_storage()

    def _init_local_storage(self):
        """Initialize local storage with user isolation and persistence."""
        components.html(
            """
            <script>
            const LOCAL_STORAGE_KEY = 'docuverse_data';

            // Handle storage events for real-time sync
            window.addEventListener('storage', (e) => {
                if (e.key === LOCAL_STORAGE_KEY) {
                    const data = JSON.parse(e.newValue || '{}');
                    window.parent.postMessage({
                        type: 'local_storage_update',
                        data: data
                    }, '*');
                }
            });

            window.handleLocalStorage = {
                save: function(key, data, userId) {
                    try {
                        let store = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '{}');
                        if (!store[userId]) store[userId] = {};
                        
                        // Handle special keys
                        if (key === 'user_sessions') {
                            store[userId].sessions = data.sessions;
                        } else {
                            store[userId][key] = data;
                        }
                        
                        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(store));
                        return true;
                    } catch (e) {
                        console.error('Error saving to localStorage:', e);
                        return false;
                    }
                },
                load: function(key, userId) {
                    try {
                        const store = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '{}');
                        const userData = store[userId] || {};
                        return userData[key];
                    } catch (e) {
                        console.error('Error loading from localStorage:', e);
                        return null;
                    }
                }
            };
            </script>
            """,
            height=0,
        )

    def save_data(self, key: str, data: Any) -> bool:
        """Save data with user isolation."""
        user_id = UserManager.get_user_id()
        js_code = f"""
            const data = {json.dumps(data)};
            window.handleLocalStorage.save('{key}', data, '{user_id}');
        """
        try:
            components.html(f"<script>{js_code}</script>", height=0)
            return True
        except Exception as e:
            st.error(f"Error saving to local storage: {e}")
            return False

    def load_data(self, key: str) -> Optional[Any]:
        """Load data with better persistence."""
        user_id = UserManager.get_user_id()

        # Check session state first
        state_key = f"{user_id}_{key}"
        if state_key in st.session_state:
            return st.session_state[state_key]

        # Try to load from local storage
        js_code = f"""
            const data = window.handleLocalStorage.load('{key}', '{user_id}');
            if (data !== null) {{
                window.parent.postMessage({{
                    type: 'local_storage_data',
                    userId: '{user_id}',
                    key: '{key}',
                    data: data
                }}, '*');
            }}
        """
        try:
            components.html(f"<script>{js_code}</script>", height=0)
            # Save to session state for future access
            if data := self._wait_for_data(key, user_id):
                st.session_state[state_key] = data
                return data
        except Exception as e:
            logger.error(f"Error loading from local storage: {e}")
        return None

    def _wait_for_data(self, key: str, user_id: str, timeout: int = 1) -> Optional[Any]:
        """Wait for data from local storage."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if hasattr(st.session_state, "_local_storage_data"):
                data = st.session_state._local_storage_data.get((user_id, key))
                if data is not None:
                    return data
            time.sleep(0.1)
        return None

    def clear_data(self, session_id: Optional[str] = None) -> bool:
        """Clear local storage data."""
        js_code = (
            f"window.handleLocalStorage.clear('{session_id}');"
            if session_id
            else "window.handleLocalStorage.clear();"
        )
        try:
            components.html(f"<script>{js_code}</script>", height=0)
            return True
        except Exception as e:
            st.error(f"Error clearing local storage: {e}")
            return False

    def sync_notes(self, notes: list, session_id: Optional[str] = None):
        """Sync notes with local storage."""
        key = f"notes_{session_id}" if session_id else "notes"
        return self.save_data(key, notes)

    def sync_chats(self, chats: list, session_id: Optional[str] = None):
        """Sync chat history with local storage."""
        key = f"chats_{session_id}" if session_id else "chats"
        return self.save_data(key, chats)

    def sync_settings(self, settings: Dict[str, Any], session_id: Optional[str] = None):
        """Sync user settings with local storage."""
        key = f"settings_{session_id}" if session_id else "settings"
        return self.save_data(key, settings)

    def restore_session_data(self, user_id: str) -> dict:
        """Restore all session data for a user."""
        stored_data = {"sessions": [], "chats": {}, "notes": {}, "files": {}}

        # Load user sessions
        sessions_data = self.load_data("user_sessions")
        if sessions_data and sessions_data.get("user_id") == user_id:
            stored_data["sessions"] = sessions_data.get("sessions", [])

            # Load data for each session
            for session_id in stored_data["sessions"]:
                for data_type in ["chats", "notes", "files"]:
                    key = f"{data_type}_{session_id}"
                    data = self.load_data(key)
                    if data:
                        stored_data[data_type][session_id] = data

        return stored_data
