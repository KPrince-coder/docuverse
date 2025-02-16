# Getting Started with DocuVerse

## Prerequisites

* Python 3.8 or higher
* [uv](https://github.com/astral-sh/uv) package manager
* Git (optional)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/KPrince-coder/docuverse.git
    ```

2. Navigate to the project directory:

    ```bash
    cd docuverse
    ```

3. Install dependencies using uv:

    ```bash
    uv sync
    ```

## Configuration

1. Configure API Key:
   * Obtain a GROQ API key from [GROQ Console](https://console.groq.com)
   * Add via sidebar "🔑 API Key Management"
   * Or add to `.streamlit/secrets.toml`:

     ```toml
     GROQ_API_KEY = "your-api-key-here"
     ```

2. Select Model:
   * Open "🤖 Model Selection" in sidebar
   * Choose preferred model
   * Default: mixtral-8x7b-32768

3. Start Using:
   * Upload documents
   * Select conversation
   * Begin chatting

## Running the Application

Start the Streamlit server:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`
