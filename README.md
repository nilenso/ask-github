# ask-github

Ask questions about GitHub repositories using AI.

## Installation

```bash
uv pip install -e .
```

## Usage

### As a Library

The library uses environment variables for API keys. Set them before importing:

```python
import os

# Set API keys programmatically (before importing ask_github)
os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["GITHUB_TOKEN"] = "ghp_..."  # Optional

from ask_github import ask

# Basic usage
response = ask(
    repo_url="https://github.com/owner/repo",
    prompt="What does this repository do?"
)
print(response)

# With custom configuration
response = ask(
    repo_url="https://github.com/torvalds/linux",
    prompt="How is memory management implemented?",
    max_iterations=50,
    model="gpt-4o",
    temperature=0.7,
    max_tokens=4000
)
print(response)
```

**Note**: If you have a `.env` file, the library will automatically load it. Environment variables set programmatically will override `.env` values.

### As a CLI

```bash
# Basic usage
ask-github https://github.com/owner/repo "What does this repository do?"

# With custom max iterations
ask-github https://github.com/owner/repo "Explain the architecture" --max-iterations 50

# With custom LLM configuration
ask-github https://github.com/owner/repo "How does authentication work?" \
  --llm-model gpt-4o \
  --llm-temperature 0.7 \
  --llm-max-tokens 4000

# Combine all options
ask-github https://github.com/torvalds/linux "Explain the scheduler" \
  --max-iterations 30 \
  --llm-model claude-3-5-sonnet-20241022 \
  --llm-temperature 0.5
```

### CLI Options

- `--max-iterations`: Maximum number of agentic loop iterations (default: 150)
- `--llm-*`: Pass any litellm configuration parameter with `--llm-` prefix
  - `--llm-model`: Choose the model (default: gpt-5)
  - `--llm-temperature`: Control randomness (0.0-2.0)
  - `--llm-max-tokens`: Limit response length
  - `--llm-top-p`: Nucleus sampling parameter
  - Any other [litellm completion parameters](https://docs.litellm.ai/docs/completion/input)

## Configuration

### API Keys

Create a `.env` file in the project root with your API keys:

```bash
# Required: LLM provider API key (choose based on model)
OPENAI_API_KEY=sk-...              # For GPT models (gpt-4, gpt-5, etc.)
ANTHROPIC_API_KEY=sk-ant-...       # For Claude models
GEMINI_API_KEY=...                 # For Google Gemini models
COHERE_API_KEY=...                 # For Cohere models

# Optional: GitHub token for higher API rate limits
GITHUB_TOKEN=ghp_...               # Increases GitHub API rate limit from 60 to 5000 req/hour
```

**Which API key do I need?**

- **Default (GPT-5)**: Set `OPENAI_API_KEY`
- **Using Claude**: Set `ANTHROPIC_API_KEY` and pass `--llm-model claude-3-5-sonnet-20241022`
- **Using Gemini**: Set `GEMINI_API_KEY` and pass `--llm-model gemini/gemini-2.0-flash-exp`

See [litellm providers](https://docs.litellm.ai/docs/providers) for other models.

### Environment Variables

Alternatively, export environment variables directly:

```bash
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...
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
