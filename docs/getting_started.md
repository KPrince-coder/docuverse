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

1. Create a `.streamlit/secrets.toml` file with your API keys:

    * Obtain a GROQ\_API\_KEY from [https://console.groq.com/](https://console.groq.com/).
    * Add the key to `.streamlit/secrets.toml`:

        ```toml
        GROQ_API_KEY = "your-api-key-here"
        ```

2. Customize the application settings in `.streamlit/config.toml`:

    * Modify the `.streamlit/config.toml` file to customize the application's appearance.

        ```toml
        [theme]
        primaryColor = "#4f8cc9"
        backgroundColor = "#ffffff"
        secondaryBackgroundColor = "#f0f2f6"
        textColor = "#262730"
        font = "sans serif"
        ```

## Running the Application

Start the Streamlit server:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`
