# DocuVerse Database Documentation

## Database Schema

### Conversations Table

* **id**: Primary key (UUID) - Unique identifier for the conversation.
* **name**: Conversation name (String) - User-defined name for the conversation.
* **created_at**: Timestamp of creation (DateTime) - Date and time when the conversation was created.
* **updated_at**: Timestamp of last update (DateTime) - Date and time when the conversation was last updated.

### Messages Table

* **id**: Primary key (UUID) - Unique identifier for the message.
* **conversation_id**: Foreign key to Conversations table (UUID) - Establishes the relationship between the message and the conversation it belongs to.
* **content**: Message content (Text) - The actual text of the message.
* **role**: Message role (user/assistant) (String) - Indicates whether the message was sent by the user or the AI assistant.
* **created_at**: Timestamp of creation (DateTime) - Date and time when the message was created.

### Documents Table

* **id**: Primary key (UUID) - Unique identifier for the document.
* **conversation_id**: Foreign key to Conversations table (UUID) - Establishes the relationship between the document and the conversation it is associated with.
* **file_name**: Original file name (String) - The original name of the uploaded file.
* **file_path**: Storage path (String) - The path to the stored file.
* **file_type**: File extension (String) - The file extension (e.g., ".pdf", ".txt").
* **created_at**: Timestamp of creation (DateTime) - Date and time when the document was uploaded.

## Database Operations

### Conversation Management

* **Create new conversation**: Creates a new entry in the Conversations table with a unique ID and a user-defined name.
* **Update conversation name**: Modifies the name field of an existing conversation in the Conversations table.
* **Delete conversation and associated data**: Removes a conversation from the Conversations table and all associated messages and documents from the Messages and Documents tables.
* **Retrieve conversation history**: Retrieves all messages associated with a specific conversation from the Messages table.

### Message Handling

* **Store user and assistant messages**: Adds new messages to the Messages table, including the message content, role (user or assistant), and timestamp.
* **Retrieve message history for a conversation**: Retrieves all messages associated with a specific conversation from the Messages table, ordered by creation timestamp.
* **Delete messages**: Removes specific messages from the Messages table.

### Document Management

* **Store document metadata**: Adds new documents to the Documents table, including the file name, storage path, file type, and timestamp.
* **Retrieve documents for a conversation**: Retrieves all documents associated with a specific conversation from the Documents table.
* **Delete documents**: Removes specific documents from the Documents table.

## Database Implementation

The database is implemented using SQLite through the ConversationDB class, which provides:

* **Connection management**: Establishes and manages connections to the SQLite database.
* **CRUD operations**: Provides methods for creating, reading, updating, and deleting data in the database tables.
* **Schema migrations**: Manages database schema migrations to ensure compatibility across different versions of the application.
* **Query optimization**: Implements query optimization techniques to improve database performance.

## ER Diagram

(Add ER diagram here)
