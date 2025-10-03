# ask-github

Ask questions about GitHub repositories using AI.

## Installation

```bash
uv pip install -e .
```

## Usage

### As a Library

```python
from ask_github import ask

response = ask(
    repo_url="https://github.com/owner/repo",
    prompt="What does this repository do?"
)
print(response)
```

### As a CLI

```bash
ask-github https://github.com/owner/repo "What does this repository do?"
```

## Development

This project uses [uv](https://github.com/astral-sh/uv) as the package manager.

```bash
# Install dependencies
uv pip install -e .

# Run the CLI
uv run ask-github https://github.com/owner/repo "Your question here"
```

## License

TBD
