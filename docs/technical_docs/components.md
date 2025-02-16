# DocuVerse Components Documentation

## Overview

The application is built using modular Streamlit components, each handling a specific functionality. This approach promotes code reusability, maintainability, and testability.

## Main Components

### Header

* **Location**: components/header.py
* **Purpose**: Provides the main application header and navigation.
* **Features**:

  * Application title: Displays the name of the application.
  * Theme toggle (light/dark mode): Allows users to switch between light and dark themes.
  * User profile section: Displays user information and provides access to user settings.
* **Implementation Details**:

  * Uses Streamlit's `st.header` and `st.columns` functions to create the header layout.
  * The theme toggle is implemented using Streamlit's `st.session_state` to persist the user's theme preference.
  * The user profile section is a placeholder for future user authentication and management features.

### Upload & Chat

* **Location**: components/upload_chat.py
* **Purpose**: Handles document upload and chat interface.
* **Features**:

  * File upload widget supporting PDF, TXT, and CSV formats: Allows users to upload documents in various formats.
  * Chat input and display with interactive UI: Provides a chat interface for users to interact with the LLM.
  * Document processing status with progress indicators: Displays the status of document processing, including progress indicators.
  * Response generation with context-aware replies: Generates context-aware replies based on the user's queries and the uploaded documents.
* **Sample UI screenshots available in ui/ folder**:

  * chat\_interface.png: Main chat interface
  * uploaded\_file\_interface.png: File upload and processing view
* **Implementation Details**:

  * Uses Streamlit's `st.file_uploader` function to handle file uploads.
  * The chat interface is implemented using Streamlit's `st.text_input` and `st.chat_message` functions.
  * Document processing is handled using the `IndexManager` class.
  * Response generation is handled using the `QueryEngine` class.

### History

* **Location**: components/history.py
* **Purpose**: Manages conversation history.
* **Features**:

  * List of past conversations: Displays a list of all past conversations.
  * Conversation renaming: Allows users to rename conversations.
  * Conversation switching: Allows users to switch between conversations.
  * Conversation deletion: Allows users to delete conversations.
* **Implementation Details**:

  * Uses Streamlit's `st.expander` function to display the conversation history.
  * Conversation data is retrieved from the database using the `ConversationDB` class.
  * Conversation renaming and deletion are handled using Streamlit's `st.button` and `st.session_state` functions.

### Notes

* **Location**: components/notes.py
* **Purpose**: Provides note-taking functionality.
* **Features**:

  * Create and edit notes: Allows users to create and edit notes using a simple text editor.
  * Associate notes with conversations: Allows users to link notes to specific conversations for easy reference.
  * Markdown support: Supports Markdown formatting for creating rich text notes.
  * Automatic saving: Automatically saves notes as the user types.
* **Implementation Details**:

  * Uses Streamlit's `st.text_area` function to create the note editor.
  * Note data is stored in Streamlit's `st.session_state` to persist notes across sessions.
  * Markdown rendering is handled using the `markdown` library.

## Component Interactions

* Components communicate through Streamlit session state: Streamlit session state is used to share data between components. For example, the `conversation_id` is stored in session state to track the current conversation.
* Data flows between components via shared state variables: Shared state variables are used to pass data between components. For example, the `messages` variable is used to store the message history for a conversation.
* Each component maintains its own state and UI logic: Each component is responsible for managing its own state and UI logic. This promotes modularity and testability.
* UI components follow a consistent design pattern with:

  * Clear visual hierarchy
  * Responsive layouts
  * Interactive elements with feedback
  * Accessible controls

## Styling

* Global styles defined in styles.css: Contains global styles for the application, such as font families, color palettes, and base styles.
* Component-specific styles in components/style.css: Contains styles specific to individual components, such as button styles, form styles, and layout styles.
* Responsive design for different screen sizes: The application uses a responsive design to adapt to different screen sizes and devices.
* UI components include:

  * Consistent color scheme: A consistent color scheme is used throughout the application to provide a cohesive look and feel.
  * Clear typography hierarchy: A clear typography hierarchy is used to improve readability and visual organization.
  * Interactive states (hover, active, disabled): Interactive states are used to provide feedback to the user when they interact with UI elements.
  * Accessible contrast ratios: Accessible contrast ratios are used to ensure that the UI is accessible to users with visual impairments.
* Sample UI designs available in ui/ folder
