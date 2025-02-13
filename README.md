# Docuverse

## Overview

Docuverse is a Streamlit application that allows users to upload documents, query them using a Large Language Model (LLM), and have conversations with the documents. It uses Langchain to interact with LLMs and ChromaDB for vector storage.

## Features

* **Document Upload:** Users can upload documents in various formats (e.g., PDF, TXT, CSV).
* **Querying:** Users can query the uploaded documents using natural language.
* **Conversational Interface:** Users can have conversations with the documents, asking follow-up questions and getting more detailed answers.
* **Data Visualization:** The application can display data from uploaded CSV files.

## Technologies Used

* **Streamlit:** A Python library for creating interactive web applications.
* **Langchain:** A framework for developing applications powered by language models.
* **ChromaDB:** A vector database for storing and retrieving document embeddings.
* **Sentence Transformers:** A library for generating sentence embeddings.
* **Python:** The programming language used to develop the application.

## File Structure

```markdown
.
├── .streamlit/
│   ├── config.toml       # Streamlit configuration file
│   └── secrets.toml      # Streamlit secrets file
├── app.py                # Main Streamlit application file
├── cache/                # Directory for caching data
├── data/                 # Directory for storing data
│   ├── conversations.db  # Database for storing conversations
│   ├── Gemini_(chatbot).pdf # Example PDF document
│   ├── uploads/          # Directory for storing uploaded documents
│   └── world_population.csv # Example CSV file
├── README.md             # This file
├── styles.css            # Custom CSS styles for the application
├── utils/                # Directory for utility modules
│   ├── __init__.py       # Initialization file for the utils package
│   ├── database.py       # Module for database operations
│   ├── index_manager.py  # Module for managing document indexes
│   ├── models/           # Directory for storing models
│   │   └── models--BAAI--bge-small-en/ # Model files
│   └── query_engine.py   # Module for querying documents
├── pyproject.toml        # Project configuration file
└── uv.lock               # Lock file for uv package manager
```

## Installation

1. Clone the repository:

    ```bash
    git clone <repository_url>
    ```

2. Navigate to the project directory:

    ```bash
    cd <project_directory>
    ```

3. Install the dependencies using uv:

    ```bash
    uv sync
    ```

## Usage

1. Run the Streamlit application:

    ```bash
    streamlit run app.py
    ```

2. Open the application in your browser at the URL displayed in the terminal.
3. Upload documents using the file upload widget.
4. Query the documents using the text input widget.
5. Have conversations with the documents by asking follow-up questions.

## Configuration

The application can be configured using the `.streamlit/config.toml` and `.streamlit/secrets.toml` files.

* `.streamlit/config.toml`: Contains Streamlit configuration options.
* `.streamlit/secrets.toml`: Contains sensitive information such as API keys.

## Data Storage

The application stores data in the `data/` directory.

* `data/conversations.db`: Stores the conversations between the user and the documents.
* `data/uploads/`: Stores the uploaded documents.

## Models

The application uses the `BAAI/bge-small-en` sentence transformer model, which is stored in the `utils/models/` directory.

## Contributing

Contributions are welcome! Please submit a pull request with your changes.

## License

[MIT](LICENSE)
