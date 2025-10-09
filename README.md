# ask-github

Ask questions about GitHub or GitLab repositories using AI.

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
os.environ["GITHUB_TOKEN"] = "ghp_..."  # Optional, for GitHub repos
os.environ["GITLAB_TOKEN"] = "glpat_..."  # Optional, for GitLab repos

from ask_github import ask

# Basic usage (GitHub, uses default branch)
response = ask(
    repo_url="https://github.com/owner/repo",
    prompt="What does this repository do?"
)
print(response)

# Basic usage (GitLab)
response = ask(
    repo_url="https://gitlab.com/owner/repo",
    prompt="What does this repository do?"
)
print(response)

# Analyze a specific branch (GitHub)
response = ask(
    repo_url="https://github.com/owner/repo/tree/feature-branch",
    prompt="What changes are in this branch?"
)
print(response)

# Analyze a specific branch (GitLab)
response = ask(
    repo_url="https://gitlab.com/owner/repo/-/tree/feature-branch",
    prompt="What changes are in this branch?"
)
print(response)

# Analyze a specific commit
response = ask(
    repo_url="https://github.com/owner/repo/commit/abc123def",
    prompt="What was changed in this commit?"
)
print(response)

# Access a private GitHub repository
response = ask(
    repo_url="https://github.com/owner/private-repo",
    prompt="Explain the authentication flow",
    token="ghp_your_token_here"
)
print(response)

# Access a private GitLab repository
response = ask(
    repo_url="https://gitlab.com/owner/private-repo",
    prompt="Explain the CI/CD pipeline",
    token="glpat_your_token_here"
)
print(response)

# With custom configuration (GitHub)
response = ask(
    repo_url="https://github.com/torvalds/linux",
    prompt="How is memory management implemented?",
    max_iterations=50,
    max_workers=20,  # Increase parallelism for faster analysis
    token="ghp_your_token_here",  # Optional: pass token directly
    model="gpt-4o",
    temperature=0.7,
    max_tokens=4000
)
print(response)

# With custom configuration (GitLab)
response = ask(
    repo_url="https://gitlab.com/gitlab-org/gitlab",
    prompt="How does the merge request approval system work?",
    max_iterations=50,
    token="glpat_your_token_here",
    model="claude-3-5-sonnet-20241022",
    temperature=0.7,
    max_tokens=4000
)
print(response)
```

**Note**: If you have a `.env` file, the library will automatically load it. Environment variables set programmatically will override `.env` values. The `token` parameter takes precedence over environment variables. The platform (GitHub/GitLab) is automatically detected from the repository URL.

### As a CLI

```bash
# Basic usage (GitHub, uses default branch)
ask-github https://github.com/owner/repo "What does this repository do?"

# Basic usage (GitLab)
ask-github https://gitlab.com/owner/repo "What does this repository do?"

# Analyze a specific branch (GitHub)
ask-github https://github.com/owner/repo/tree/feature-branch "What changes are in this branch?"

# Analyze a specific branch (GitLab)
ask-github https://gitlab.com/owner/repo/-/tree/feature-branch "What changes are in this branch?"

# Analyze a specific commit
ask-github https://github.com/owner/repo/commit/abc123 "What was changed in this commit?"

# With custom max iterations
ask-github https://github.com/owner/repo "Explain the architecture" --max-iterations 50

# Access a private GitHub repository
ask-github https://github.com/owner/private-repo "Explain the code" \
  --token ghp_your_token_here

# Access a private GitLab repository
ask-github https://gitlab.com/owner/private-repo "Explain the CI/CD setup" \
  --token glpat_your_token_here

# With custom LLM configuration (GitHub)
ask-github https://github.com/owner/repo "How does authentication work?" \
  --llm-model gpt-4o \
  --llm-temperature 0.7 \
  --llm-max-tokens 4000

# With custom LLM configuration (GitLab)
ask-github https://gitlab.com/gitlab-org/gitlab "Explain the database schema" \
  --llm-model claude-3-5-sonnet-20241022 \
  --llm-temperature 0.7 \
  --llm-max-tokens 4000

# Combine all options (GitHub)
ask-github https://github.com/torvalds/linux "Explain the scheduler" \
  --max-iterations 30 \
  --max-workers 20 \
  --token ghp_your_token_here \
  --llm-model claude-3-5-sonnet-20241022 \
  --llm-temperature 0.5

# Combine all options (GitLab)
ask-github https://gitlab.com/gitlab-org/gitlab-runner "How does the runner architecture work?" \
  --max-iterations 30 \
  --token glpat_your_token_here \
  --llm-model gpt-4o \
  --llm-temperature 0.5
```

### Supported URL Formats

Both GitHub and GitLab URLs are supported:

**GitHub:**
- `https://github.com/owner/repo` - Uses default branch
- `https://github.com/owner/repo/tree/branch-name` - Specific branch
- `https://github.com/owner/repo/blob/branch-name/path/to/file` - Specific branch
- `https://github.com/owner/repo/commit/sha` - Specific commit

**GitLab:**
- `https://gitlab.com/owner/repo` - Uses default branch
- `https://gitlab.com/owner/repo/-/tree/branch-name` - Specific branch
- `https://gitlab.com/owner/repo/-/blob/branch-name/path/to/file` - Specific branch
- `https://gitlab.com/owner/repo/-/commit/sha` - Specific commit

Simply paste any repository URL and the tool will automatically detect and use the appropriate branch or commit.

### CLI Options

- `--max-iterations`: Maximum number of agentic loop iterations (default: 20)
- `--max-workers`: Maximum number of parallel tool calls (default: 15)
- `--token`: API token for authentication and private repo access (uses GITHUB_TOKEN or GITLAB_TOKEN env var if not provided)
- `--github-token`: (Deprecated) Use `--token` instead. Kept for backwards compatibility
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

# Optional: Repository platform tokens
GITHUB_TOKEN=ghp_...               # For GitHub repos (higher rate limits: 60 → 5000 req/hour)
GITLAB_TOKEN=glpat_...             # For GitLab repos (private repos and higher rate limits)
```

**Which API key do I need?**

- **Default (GPT-5)**: Set `OPENAI_API_KEY`
- **Using Claude**: Set `ANTHROPIC_API_KEY` and pass `--llm-model claude-3-5-sonnet-20241022`
- **Using Gemini**: Set `GEMINI_API_KEY` and pass `--llm-model gemini/gemini-2.0-flash-exp`

See [litellm providers](https://docs.litellm.ai/docs/providers) for other models.

### Platform Tokens

#### GitHub Token

A GitHub personal access token is:
- **Required** for accessing private repositories
- **Optional** for public repositories (but recommended for higher rate limits: 60 → 5000 requests/hour)

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

#### GitLab Token

A GitLab personal access token is:
- **Required** for accessing private projects
- **Optional** for public projects (but recommended for higher rate limits)

**Creating a GitLab token:**

1. Go to GitLab User Settings → Access Tokens
2. Click "Add new token"
3. Set token name and expiration (optional)
4. Select scopes:
   - **read_api**: Read-only access to API (recommended for this tool)
   - **read_repository**: Read-only access to repositories
5. Click "Create personal access token"
6. Copy the token (starts with `glpat_`)

**Using tokens:**

You can provide tokens in three ways (in order of precedence):
1. Via parameter: `ask(..., token="ghp_..." or "glpat_...")`
2. Via CLI argument: `--token ghp_...` or `--token glpat_...`
3. Via environment variable: `GITHUB_TOKEN=ghp_...` or `GITLAB_TOKEN=glpat_...` in `.env` file

The platform (GitHub/GitLab) is automatically detected from the repository URL.

### Environment Variables

Alternatively, export environment variables directly:

```bash
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...
export GITLAB_TOKEN=glpat_...
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
