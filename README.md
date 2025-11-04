# ask-github

An agentic semantic search tool that works over GitHub and GitLab APIs instead of the filesystem.
Perfect for people like product managers, business users, and developers who want quick insights into unfamiliar codebases.
Originally created for experimental use in [storymachine](https://github.com/nilenso/storymachine), but surprisingly effective for everyday code exploration.

- The API calls are just tools given to the model
- The prompt is a one-liner asking it to use those API tools instead of filesystem.
- Supports parallel tool calls, because they're just network calls
- It is not made to be super efficient, no benchmarks or performance numbers, etc. Works well enough.

## Installation

```bash
uv pip install -e .
```

## Usage

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Optional: For private repos or higher rate limits
GITHUB_TOKEN=ghp_...
GITLAB_TOKEN=glpat_...

Basic usage:
ask-github <repo-url> "<your-question>"

# Ask about any repository
uv run ask-github https://github.com/karpathy/nanochat "What exactly does the speedrun.sh script do?"
uv run ask-github https://github.com/cline/cline "How is semantic code search implemented?"
uv run ask-github https://github.com/nilenso/ask-github "What GitLab operations are supported?"
```

Options:
- `--max-iterations`: Control search depth (default: 20)
- `--max-workers`: Parallel file operations (default: 15)
- `--token`: GitHub/GitLab token for private repos or higher rate limits
- `--llm-model`: Choose AI model (default: gpt-5)
- `--llm-temperature`: Control response randomness

It can also be used as a python library instead of a CLI. 
See the [detailed usage guide](docs/usage.md) for all options and configuration.

## Supported Platforms

- GitHub (public and private repositories)
- GitLab (public and private projects)

Both platforms support analyzing specific branches, commits, and refs.

## License

MIT
