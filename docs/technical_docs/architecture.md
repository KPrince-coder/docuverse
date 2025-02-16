# DocuVerse Architecture Overview

## System Components

### Frontend

* **Streamlit UI**: Provides the web interface for user interaction. This is the main entry point for users to interact with the application.
* **Components**:

  * **Header**: Application header and navigation. This component provides the application's title, navigation links, and user authentication features.
  * **Upload & Chat**: Document upload and chat interface. This component allows users to upload documents and interact with the LLM through a chat interface.
  * **History**: Conversation history management. This component allows users to view, manage, and resume past conversations.
  * **Notes**: Note-taking functionality. This component allows users to create, edit, and organize notes related to their conversations.

### Backend

* **Query Engine**: Handles document processing and LLM interactions. This component is responsible for processing user queries, retrieving relevant information from the document index, and interacting with the LLM to generate responses.
* **Database**: Stores conversation history and document metadata. This component stores all conversation history, document metadata, and user information.
* **Index Manager**: Manages document embeddings and vector storage. This component is responsible for creating and managing document embeddings, storing them in a vector database, and retrieving them for query processing.

## Data Flow

1. **User uploads documents through the Streamlit interface:** The user uploads documents through the Streamlit UI, which supports various file formats such as PDF, TXT, and CSV.
2. **Documents are processed and indexed by the Index Manager:** The Index Manager extracts text from the uploaded documents, generates embeddings using a pre-trained language model, and stores the embeddings in a vector database (ChromaDB).
3. **User queries are handled by the Query Engine:** When a user submits a query, the Query Engine retrieves relevant document embeddings from the vector database based on the query.
4. **Responses are generated using the LLM and returned to the user:** The Query Engine uses the retrieved document embeddings and the user's query to prompt the LLM (Large Language Model) to generate a response. The response is then displayed to the user in the Streamlit UI.
5. **Conversations are stored in the database for future reference:** The complete conversation, including the user's query and the LLM's response, is stored in the database (SQLite) for future reference and to maintain conversation history.

## Technology Stack

* **Frontend**:
  * Streamlit: 1.29.0
  * HTML/CSS
* **Backend**:
  * Python: 3.8+
  * Langchain
  * ChromaDB
* **Database**: SQLite (via ConversationDB)
* **AI**: Large Language Model (LLM) integration

## Architecture Diagram

(Add architecture diagram here)
