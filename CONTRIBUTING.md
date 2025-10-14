# Contributing to PDF Chat with Ollama

Thank you for your interest in contributing to PDF Chat with Ollama! This document provides guidelines and information for contributors.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/pdf-chat-ollama.git
   cd pdf-chat-ollama
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Code Style

This project follows the Google Python Style Guide and uses several tools to enforce consistency:

- **Black** for code formatting (line length: 80 characters)
- **Ruff** for linting
- **MyPy** for type checking
- **Pre-commit** for automated checks

### Running Checks

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy .

# Run all checks
pre-commit run --all-files
```

## Testing

We use pytest for testing. Run tests with:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pdf_chat_ollama

# Run specific test file
pytest tests/test_specific.py
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run checks**
   ```bash
   pre-commit run --all-files
   pytest
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Commit Message Guidelines

Use clear, descriptive commit messages:

- Use imperative mood ("Add feature" not "Added feature")
- Keep the first line under 50 characters
- Use the body to explain what and why, not how

Examples:
- `Add support for multiple PDF formats`
- `Fix memory leak in vector store`
- `Update documentation for new API`

## Issue Guidelines

When creating issues:

- Use the provided templates
- Provide clear reproduction steps
- Include environment information
- Add relevant logs or error messages

## Development Guidelines

- **Documentation**: Update docstrings and README for new features
- **Type Hints**: All functions should have proper type hints
- **Error Handling**: Use specific exceptions and provide helpful error messages
- **Testing**: Aim for good test coverage, especially for new features
- **Backwards Compatibility**: Consider impact on existing users

## Questions?

Feel free to open an issue for questions or discussions about the project.
