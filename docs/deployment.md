# DocuVerse Deployment Guide

## Local Development

### Requirements

* Python 3.8+
* [uv](https://github.com/astral-sh/uv) package manager
* Streamlit CLI

### Steps

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

## Production Deployment

### Docker Deployment

1. Build the Docker image:

    ```bash
    docker build -t docuverse .
    ```

2. Run the container:

    ```bash
    docker run -p 8501:8501 docuverse
    ```

    * To configure environment variables, use the `-e` flag:

        ```bash
        docker run -p 8501:8501 -e GROQ_API_KEY="your-api-key" docuverse
        ```

### Cloud Deployment

#### AWS EC2

1. Launch an EC2 instance with Ubuntu.
2. Install Docker:

    ```bash
    sudo apt update
    sudo apt install docker.io
    ```

3. Follow Docker deployment steps.

#### Heroku

1. Create a new Heroku app.
2. Add the following buildpacks:

    * heroku/python
    * heroku-community/apt
3. Deploy using Git:

    ```bash
    git push heroku main
    ```

## Configuration

* Set environment variables for production.
* Configure SSL/TLS for secure connections.
* Set up logging and monitoring.

## Scaling

* Use a load balancer for multiple instances.
* Configure auto-scaling based on traffic.
* Use a managed database service for production.
