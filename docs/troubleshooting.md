# DocuVerse Troubleshooting Guide

## Common Issues and Solutions

### Application Won't Start

* **Error**: "Port 8501 already in use"

  * Solution: Kill the existing process or use a different port.

        ```bash
        lsof -i :8501
        kill <PID>
        ```

* **Error**: Missing dependencies

  * Solution: Reinstall requirements.

        ```bash
        uv sync
        ```

* **Error**: "Streamlit not found"

  * Solution: Install Streamlit.

        ```bash
        pip install streamlit
        ```

### Document Upload Issues

* **Error**: "File type not supported"

  * Solution: Ensure file is in supported formats (PDF, TXT, CSV).
* **Error**: "File too large"

  * Solution: Split large files or increase upload limit in config.

### Chat Functionality Problems

* **Issue**: No response from AI

  * Check API key in `.streamlit/secrets.toml`.
  * Verify internet connection.
  * Check API usage limits.
  * Ensure the GROQ\_API\_KEY is valid and has sufficient usage quota.

### Database Errors

* **Error**: "Database connection failed"

  * Solution: Verify database file permissions.
  * Check for corrupted database files.

        ```bash
        sqlite3 data/database.db "PRAGMA integrity_check;"
        ```

## Debugging Tips

1. Check Streamlit logs for error messages.
2. Verify environment variables.
3. Test API connectivity.
4. Clear browser cache and cookies.
5. Restart the Streamlit server.
6. Check the browser console for JavaScript errors.
7. Use the Streamlit debugger to step through the code.

## Getting Help

* Check the [GitHub Issues](https://github.com/KPrince-coder/docuverse/issues) page.
* Search the documentation.
* Contact support with detailed error logs and steps to reproduce the issue.
