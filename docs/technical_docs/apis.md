# DocuVerse API Documentation

## External API Integrations

### LLM API

* **Provider**: GROQ
* **Endpoint**: <https://api.groq.com/v1/chat/completions>
* **Authentication**: API Key (stored in `.streamlit/secrets.toml`)
* **Usage**:

  * Send user queries
  * Receive AI-generated responses
  * Handle conversation context
* **Request Format**:

    ```json
    {
      "model": "mixtral-8x7b-32768",
      "messages": [
        {
          "role": "user",
          "content": "Your query here"
        }
      ]
    }
    ```

* **Response Format**:

    ```json
    {
      "choices": [
        {
          "message": {
            "content": "AI response here"
          }
        }
      ]
    }
    ```

* **Available Models**: mixtral-8x7b-32768

### Embedding API

* **Provider**: Sentence Transformers
* **Model**: all-mpnet-base-v2
* **Usage**:

  * Generate document embeddings
  * Create vector representations of text
  * Enable semantic search capabilities
* **Input**: Text string
* **Output**: 768-dimensional vector embedding

## API Usage Patterns

### Query Processing

1. **User input is received through the Streamlit interface**: The user enters a query in the chat interface.
2. **Input is preprocessed and sent to the LLM API**: The query is preprocessed (e.g., cleaned, tokenized) and sent to the GROQ API.
3. **Response is received and displayed to the user**: The AI-generated response is received from the GROQ API and displayed in the chat interface.
4. **Conversation context is maintained for follow-up queries**: The conversation history is stored and used to provide context for subsequent queries.

### Document Processing

1. **Uploaded documents are processed using the Embedding API**: When a user uploads a document, the text is extracted and sent to the Sentence Transformers API.
2. **Document embeddings are stored in ChromaDB**: The Sentence Transformers API generates embeddings for the document, which are then stored in the ChromaDB vector database.
3. **Queries are matched against document embeddings for relevant results**: When a user submits a query, the query is also embedded using the Sentence Transformers API, and the resulting embedding is used to search for relevant documents in ChromaDB.

## Error Handling

* **API rate limiting**: Implement retry logic with exponential backoff to handle rate limits gracefully.
* **Network connectivity issues**: Implement error handling to catch network errors and display informative messages to the user.
* **Invalid API responses**: Validate API responses to ensure they conform to the expected format.
* **Authentication failures**: Check the API key and ensure it is valid.

## Rate Limits and Quotas

* **GROQ API**: 100 requests per minute

  * Monitor usage through the GROQ API dashboard.
  * Implement retry logic with exponential backoff to handle rate limits.
* **Embedding API**: No explicit rate limits
