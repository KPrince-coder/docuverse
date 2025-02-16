# DocuVerse

DocuVerse is an intelligent document management and analysis platform that allows users to interact with their documents through natural language queries. Built with Streamlit, Python, and modern AI technologies, it provides an intuitive interface for document processing, querying, and analysis.

## Features

* **Document upload and processing (PDF, TXT, CSV)**: Allows users to upload documents in various formats and process them for analysis.
* **Natural language querying**: Enables users to ask questions about their documents using natural language.
* **Conversation history management**: Stores and manages conversation history for future reference.
* **Note-taking functionality**: Provides a built-in note-taking feature for users to capture insights and ideas.
* **Data visualization for CSV files**: Allows users to visualize data from CSV files using charts and graphs.

## Documentation

* [Getting Started](docs/getting_started.md): Provides instructions on how to install and configure DocuVerse.
* [User Guide](docs/user_guide.md): Explains how to use the DocuVerse application.
* [Technical Documentation](docs/technical_docs/architecture.md): Describes the system architecture and components.
* [API Documentation](docs/technical_docs/apis.md): Provides documentation for the external APIs used by DocuVerse.
* [Database Documentation](docs/technical_docs/database.md): Describes the database schema and operations.
* [Components Documentation](docs/technical_docs/components.md): Provides documentation for the Streamlit components used in the application.
* [Deployment Guide](docs/deployment.md): Provides instructions on how to deploy DocuVerse to production.
* [Troubleshooting](docs/troubleshooting.md): Provides solutions to common issues and problems.
* [Contributing Guidelines](docs/contributing.md): Provides guidelines for contributing to the DocuVerse project.

## Quick Start

1. Clone the repository:

    ```bash
    git clone https://github.com/KPrince-coder/docuverse.git
    ```

2. Navigate to the project directory:

    ```bash
    cd docuverse
    ```

3. Install dependencies:

    ```bash
    uv sync
    ```

4. Configure environment variables in `.streamlit/secrets.toml`:

    * Set the `GROQ_API_KEY` in `.streamlit/secrets.toml`.
5. Run the application:

    ```bash
    streamlit run app.py
    ```

## Requirements

* Python 3.8+
* Streamlit
* GROQ API key

## License

MIT License - See [LICENSE](LICENSE) for details
