import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Dict, Any, Optional


class LocalStorageManager:
    """Manages browser-local storage for user data persistence."""

    def __init__(self):
        self._init_local_storage()

    def _init_local_storage(self):
        """Initialize local storage with improved session handling."""
        components.html(
            """
            <script>
            // Initialize storage if not exists
            if (!localStorage.getItem('docuverse_data')) {
                localStorage.setItem('docuverse_data', JSON.stringify({
                    sessions: {},
                    lastSync: Date.now()
                }));
            }

            // Create communication functions
            window.handleLocalStorage = {
                save: function(key, data) {
                    try {
                        let store = JSON.parse(localStorage.getItem('docuverse_data'));
                        if (key.includes('_')) {
                            // Handle session-specific data
                            const [type, sessionId] = key.split('_');
                            if (!store.sessions[sessionId]) {
                                store.sessions[sessionId] = {};
                            }
                            store.sessions[sessionId][type] = data;
                        } else {
                            // Handle global data
                            store[key] = data;
                        }
                        localStorage.setItem('docuverse_data', JSON.stringify(store));
                        return true;
                    } catch (e) {
                        console.error('Error saving to localStorage:', e);
                        return false;
                    }
                },
                load: function(key) {
                    try {
                        let store = JSON.parse(localStorage.getItem('docuverse_data'));
                        if (key.includes('_')) {
                            // Handle session-specific data
                            const [type, sessionId] = key.split('_');
                            return store.sessions[sessionId]?.[type];
                        }
                        return store[key];
                    } catch (e) {
                        console.error('Error loading from localStorage:', e);
                        return null;
                    }
                },
                clear: function(sessionId) {
                    try {
                        let store = JSON.parse(localStorage.getItem('docuverse_data'));
                        if (sessionId) {
                            // Clear session-specific data
                            delete store.sessions[sessionId];
                        } else {
                            // Clear all data
                            store = { sessions: {}, lastSync: Date.now() };
                        }
                        localStorage.setItem('docuverse_data', JSON.stringify(store));
                        return true;
                    } catch (e) {
                        console.error('Error clearing localStorage:', e);
                        return false;
                    }
                }
            };
            </script>
            """,
            height=0,
        )

    def save_data(self, key: str, data: Any) -> bool:
        """Save data to local storage."""
        js_code = f"""
            const data = {json.dumps(data)};
            window.handleLocalStorage.save('{key}', data);
        """
        try:
            components.html(f"<script>{js_code}</script>", height=0)
            return True
        except Exception as e:
            st.error(f"Error saving to local storage: {e}")
            return False

    def load_data(self, key: str) -> Optional[Any]:
        """Load data from local storage."""
        js_code = f"""
            const data = window.handleLocalStorage.load('{key}');
            if (data) {{
                window.parent.postMessage({{
                    type: 'local_storage_data',
                    key: '{key}',
                    data: data
                }}, '*');
            }}
        """
        try:
            components.html(f"<script>{js_code}</script>", height=0)
            # Note: This is a placeholder. In practice, you'd need to handle
            # the postMessage response in the Streamlit frontend
            return None
        except Exception as e:
            st.error(f"Error loading from local storage: {e}")
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
