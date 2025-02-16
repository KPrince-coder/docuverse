# Contributing to DocuVerse

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork:

    ```bash
    git clone https://github.com/YOUR_USERNAME/docuverse.git
    ```

3. Create a new branch:

    ```bash
    git checkout -b feature/your-feature-name
    ```

## Development Workflow

1. Install dependencies:

    ```bash
    uv sync
    ```

2. Make your changes following the coding standards.
3. Run tests:

    ```bash
    pytest
    ```

4. Commit your changes with descriptive messages:

    ```bash
    git commit -m "feat: Add your feature"
    ```

5. Push your branch:

    ```bash
    git push origin feature/your-feature-name
    ```

6. Open a pull request on GitHub.

## Coding Standards

* Follow PEP 8 for Python code.
* Use type hints where applicable.
* Write docstrings for all public functions.
* Keep functions small and focused.
* Write unit tests for new features.

## Pull Request Guidelines

* Include a clear description of changes.
* Reference related issues.
* Ensure all tests pass.
* Update documentation if needed.
* Keep commits atomic and meaningful.

## Code Review Process

1. Maintainers will review your PR.
2. Address any feedback.
3. PR will be merged once approved.

## Reporting Issues

* Check existing issues before creating new ones.
* Provide detailed reproduction steps.
* Include relevant logs and screenshots.
