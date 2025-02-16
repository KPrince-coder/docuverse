# DocuVerse User Guide

## Getting Started

1. **Prerequisites:** Ensure you have Python 3.7+ installed.
2. **Launch the application:** Run the `app.py` file using Streamlit. Open your terminal, navigate to the application directory, and run the command `streamlit run app.py`.
3. **Access the application:** The application will open in your web browser. If it doesn't open automatically, navigate to the URL displayed in the terminal (usually `http://localhost:8501`).
4. **Create a new conversation or continue an existing one:** Start a new conversation or select an existing one from the conversation history.
5. **Upload documents to begin interacting:** Upload your documents to start asking questions and getting insights.

## Uploading Documents

To upload documents:

1. Click the "Upload" button.
2. Select your file.

    * **Supported formats:** PDF, TXT, and CSV.
    * **File size limit:** 10MB.
3. Wait for processing to complete. Processing time depends on file size and complexity.
4. Refer to [uploaded\_file\_interface.png](ui/uploaded_file_interface.png) for a visual reference of the upload interface.

## Chat Interface

The chat interface allows you to:

* Ask questions about your documents.
* Get AI-generated responses.
* View conversation history.

The chat interface consists of the following elements:

1. **Input field:** Type your questions or prompts in the input field.
2. **Send button:** Click the send button to submit your query.
3. **Response display:** The AI-generated responses will be displayed in the chat window.
4. **Conversation history:** View your previous conversations by clicking on the conversation history button.

Refer to [chat\_interface.png](ui/chat_interface.png) for a visual reference of the chat interface.

## Notes Feature

The notes feature enables you to:

* Create and edit notes.
* Associate notes with conversations.
* Use markdown formatting.

The notes feature provides a convenient way to capture and organize your thoughts and insights. You can:

1. **Create new notes:** Start a new note by clicking the "New Note" button.
2. **Edit existing notes:** Modify the content of your notes using the built-in editor.
3. **Format notes:** Use Markdown syntax to format your notes, including headings, lists, and links.
4. **Associate notes with conversations:** Link your notes to specific conversations for easy reference.
5. **Organize notes:** Use tags or categories to organize your notes and make them easier to find.

Refer to [sample\_note\_opened.png](ui/sample_note_opened.png) for a visual reference of the notes interface.

## Conversation History

Manage your conversations by:

* Renaming conversations ([conversation\_renaming.png](ui/conversation_renaming.png)).
* Switching between conversations ([select\_conversation\_dialog.png](ui/select_conversation_dialog.png)).
* Deleting old conversations.
* Viewing history ([conversation\_history.png](ui/conversation_history.png)).

The conversation history feature allows you to:

1. **Rename conversations:** Give your conversations meaningful names to easily identify them.
2. **Switch between conversations:** Quickly switch between different conversations to continue where you left off.
3. **Delete old conversations:** Remove conversations that are no longer needed to keep your history organized.
4. **View history:** Review the complete history of your conversations, including questions and responses.

## Tips for Effective Use

* Use clear and specific questions.
* Break down complex queries into smaller questions.
* Utilize notes to track important insights.
* Refer to the sample UI images in the ui/ folder for guidance.

Here are some additional tips for effective use:

1. **Be specific:** Ask precise questions to get the most relevant answers.
2. **Use keywords:** Include relevant keywords in your questions to help the AI understand your intent.
3. **Provide context:** Give the AI enough context to answer your questions accurately.
4. **Experiment with different prompts:** Try different phrasing and approaches to see what works best.
5. **Review the documentation:** Refer to the documentation for detailed information on features and usage.

## Troubleshooting

If you encounter issues:

* Check the Troubleshooting Guide.
* Verify file formats and sizes.
* Ensure proper internet connection.
* Contact support if needed.

Here are some common issues and solutions:

1. **Application not launching:**
    * Ensure you have Python 3.7+ installed.
    * Verify that you have installed all the required dependencies using `pip install -r requirements.txt`.
    * Check the terminal for any error messages.
2. **File upload issues:**
    * Make sure your file is in a supported format (PDF, TXT, CSV).
    * Verify that your file size is within the limit (10MB).
    * Check your internet connection.
3. **Chat interface not responding:**
    * Ensure that the application is running.
    * Check your internet connection.
    * Try refreshing the page.
4. **Notes feature not working:**
    * Make sure you are logged in.
    * Check your browser's local storage settings.
