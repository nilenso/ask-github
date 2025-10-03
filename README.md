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
os.environ["GITHUB_TOKEN"] = "ghp_..."  # Optional, for higher rate limits

from ask_github import ask

# Basic usage
response = ask(
    repo_url="https://github.com/owner/repo",
    prompt="What does this repository do?"
)
print(response)

# Access a private repository
response = ask(
    repo_url="https://github.com/owner/private-repo",
    prompt="Explain the authentication flow",
    github_token="ghp_your_token_here"
)
print(response)

# With custom configuration
response = ask(
    repo_url="https://github.com/torvalds/linux",
    prompt="How is memory management implemented?",
    max_iterations=50,
    github_token="ghp_your_token_here",  # Optional: pass token directly
    model="gpt-4o",
    temperature=0.7,
    max_tokens=4000
)
print(response)
```

**Note**: If you have a `.env` file, the library will automatically load it. Environment variables set programmatically will override `.env` values. The `github_token` parameter takes precedence over the environment variable.

### As a CLI

```bash
# Basic usage
ask-github https://github.com/owner/repo "What does this repository do?"

# With custom max iterations
ask-github https://github.com/owner/repo "Explain the architecture" --max-iterations 50

# Access a private repository
ask-github https://github.com/owner/private-repo "Explain the code" \
  --github-token ghp_your_token_here

# With custom LLM configuration
ask-github https://github.com/owner/repo "How does authentication work?" \
  --llm-model gpt-4o \
  --llm-temperature 0.7 \
  --llm-max-tokens 4000

# Combine all options
ask-github https://github.com/torvalds/linux "Explain the scheduler" \
  --max-iterations 30 \
  --github-token ghp_your_token_here \
  --llm-model claude-3-5-sonnet-20241022 \
  --llm-temperature 0.5
```

### CLI Options

- `--max-iterations`: Maximum number of agentic loop iterations (default: 20)
- `--github-token`: GitHub personal access token for authentication and private repo access (uses GITHUB_TOKEN env var if not provided)
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

# Optional: GitHub token
GITHUB_TOKEN=ghp_...               # For private repos and higher rate limits (60 → 5000 req/hour)
```

**Which API key do I need?**

- **Default (GPT-5)**: Set `OPENAI_API_KEY`
- **Using Claude**: Set `ANTHROPIC_API_KEY` and pass `--llm-model claude-3-5-sonnet-20241022`
- **Using Gemini**: Set `GEMINI_API_KEY` and pass `--llm-model gemini/gemini-2.0-flash-exp`

See [litellm providers](https://docs.litellm.ai/docs/providers) for other models.

### GitHub Token

A GitHub personal access token is:
- **Required** for accessing private repositories
- **Optional** for public repositories (but recommended for higher rate limits)

**Creating a GitHub token:**

**Option 1: Fine-grained tokens (recommended)**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Set token name and expiration
4. Under "Repository access", select:
   - "Only select repositories" and choose your repos, OR
   - "All repositories" for broader access
5. Under "Repository permissions", set:
   - **Contents**: Read-only (required for reading files)
   - **Metadata**: Read-only (automatically included)
6. Copy the token (starts with `github_pat_`)

**Option 2: Classic tokens** (simpler but less secure)
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - For **public repos only**: No scopes needed (just generate empty token)
   - For **private repos**: Check `repo` scope
4. Copy the token (starts with `ghp_`)

**Using the token:**

You can provide the token in three ways (in order of precedence):
1. Via parameter: `ask(..., github_token="ghp_...")`
2. Via CLI argument: `--github-token ghp_...`
3. Via environment variable: `GITHUB_TOKEN=ghp_...` in `.env` file

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
