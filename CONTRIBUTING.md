# Contributing to devlog-cli

Thank you for your interest in contributing to devlog-cli! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Git

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/isakanderson-official/devlog-cli.git
   cd devlog-cli
   ```

2. **Install development dependencies**
   ```bash
   # Install package in editable mode with dev dependencies
   pip install -e .[dev]

   # Or install from requirements file
   pip install -r requirements-dev.txt
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

   This will automatically run linting and formatting checks before each commit.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Run specific test files
```bash
pytest tests/unit/test_tasks.py
pytest tests/integration/test_cli_commands.py
```

### Run only unit tests
```bash
pytest tests/unit/
```

### Run only integration tests
```bash
pytest tests/integration/
```

## Code Quality

### Linting
```bash
# Check code style
ruff check devlog/

# Auto-fix issues
ruff check --fix devlog/
```

### Formatting
```bash
# Check formatting
ruff format --check devlog/

# Auto-format code
ruff format devlog/
```

### Type Checking
```bash
mypy devlog/core/ devlog/cli.py
```

### Run all quality checks
```bash
# The pre-commit hook will run these automatically
pre-commit run --all-files
```

## Code Standards

### Style Guidelines
- Follow PEP 8 style guide
- Use descriptive variable names
- Keep functions focused and small
- Add docstrings for public functions
- Line length limit: 100 characters

### Testing Guidelines
- Write tests for all new features
- Maintain or increase code coverage (target: 70%+)
- Unit tests should be fast and isolated
- Integration tests should test real workflows
- Use descriptive test names that explain what is being tested

### Coverage Targets
- Core modules (`devlog/core/`): 90%+ coverage
- CLI module (`devlog/cli.py`): 80%+ coverage
- Overall project: 70%+ coverage
- TUI/UI modules: Excluded from coverage (manual testing)

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following the style guidelines
   - Add tests for new functionality
   - Ensure all tests pass
   - Update documentation if needed

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

   Commit messages should:
   - Start with a verb (Add, Fix, Update, etc.)
   - Be concise but descriptive
   - Reference issue numbers if applicable

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure CI checks pass
   - Wait for code review

## Project Structure

```
devlog-cli/
├── devlog/                 # Main package
│   ├── core/              # Business logic (highly testable)
│   │   ├── tasks.py       # Task operations
│   │   ├── persistence.py # File I/O
│   │   └── config.py      # Configuration
│   ├── ui/                # UI components (not tested)
│   │   ├── colors.py
│   │   ├── drawing.py
│   │   └── input.py
│   ├── cli.py             # CLI commands
│   ├── tui.py             # TUI main loop (not tested)
│   └── views.py           # TUI views (not tested)
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test data
└── .github/workflows/     # CI/CD pipelines
```

## Testing Philosophy

We focus testing efforts where they provide the most value:

- **High priority**: Core business logic (`core/` modules) - pure functions, easy to test
- **Medium priority**: CLI commands - high user value, integration testing
- **Low priority**: TUI/UI - complex to test, manual QA is more effective

## What Not to Do

- Don't commit directly to `main` branch
- Don't skip writing tests for new features
- Don't ignore failing CI checks
- Don't decrease overall code coverage
- Don't add runtime dependencies (keep it stdlib-only)

## Getting Help

- Open an issue for bug reports or feature requests
- Tag issues with appropriate labels
- Ask questions in pull request comments
- Be respectful and constructive

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
