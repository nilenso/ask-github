# ask-github

An agentic semantic search tool that lets you explore and understand code repositories using AI, without cloning them locally. Instead of filesystem access, it uses GitHub and GitLab APIs to navigate and analyze code.

Perfect for product managers, business users, and developers who want quick insights into unfamiliar codebases.

## Why use this?

- **No cloning required**: Ask questions about any repository without downloading it
- **Works across hosting platforms**: Supports both GitHub and GitLab
- **Agentic exploration**: The AI agent autonomously navigates the repository to find relevant code
- **Fast and parallel**: Reads multiple files concurrently for quick answers

Originally created for experimental use in [storymachine](https://github.com/nilenso/storymachine), but surprisingly effective for everyday code exploration.

## Installation

```bash
uv pip install -e .
```

## Quick Start

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Ask about any repository
ask-github https://github.com/postgres/postgres "How is autovacuum implemented?"
ask-github https://github.com/torvalds/linux "How does the ls command work?"
ask-github https://github.com/anthropics/ask-github "What GitLab operations are supported?"
```

## Example Use Cases

**Understanding complex systems:**
```bash
ask-github https://github.com/postgres/postgres "Explain the query planner architecture"
```

**Learning from real-world implementations:**
```bash
ask-github https://github.com/django/django "How does Django handle database migrations?"
```

**Exploring specific features:**
```bash
ask-github https://github.com/torvalds/linux "How is the process scheduler implemented?"
```

**Checking framework capabilities:**
```bash
ask-github https://github.com/rails/rails "What caching strategies does Rails support?"
```

## CLI Usage

Basic usage:
```bash
ask-github <repo-url> "<your-question>"
```

With options:
```bash
ask-github https://github.com/owner/repo "Your question" \
  --max-iterations 30 \
  --llm-model gpt-4o
```

Common options:
- `--max-iterations`: Control search depth (default: 20)
- `--max-workers`: Parallel file operations (default: 15)
- `--token`: GitHub/GitLab token for private repos or higher rate limits
- `--llm-model`: Choose AI model (default: gpt-5)
- `--llm-temperature`: Control response randomness

See the [detailed usage guide](docs/usage.md) for all options and configuration.

## Library Usage

```python
from ask_github import ask

# Simple query
response = ask(
    repo_url="https://github.com/owner/repo",
    prompt="How does authentication work?"
)
print(response)

# With custom options
response = ask(
    repo_url="https://github.com/owner/repo",
    prompt="Explain the API design",
    max_iterations=30,
    model="claude-3-5-sonnet-20241022",
    temperature=0.7
)
print(response)
```

For complete library documentation and advanced usage, see the [detailed usage guide](docs/usage.md).

## Configuration

Create a `.env` file:
```bash
# Required: LLM API key
OPENAI_API_KEY=sk-...

# Optional: For private repos or higher rate limits
GITHUB_TOKEN=ghp_...
GITLAB_TOKEN=glpat_...
```

See the [usage guide](docs/usage.md) for detailed setup instructions and token creation.

## Supported Platforms

- GitHub (public and private repositories)
- GitLab (public and private projects)

Both platforms support analyzing specific branches, commits, and refs.

## License

MIT
