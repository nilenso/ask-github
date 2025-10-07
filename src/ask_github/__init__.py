from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
import litellm
from litellm import completion

from . import github

# Load environment variables from .env file
load_dotenv()

# Enable litellm logging
os.environ['LITELLM_LOG'] = 'INFO'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Tool definitions for LiteLLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_repo_info",
            "description": "Get repository information including default branch and metadata",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"}
                },
                "required": ["owner", "repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "path": {"type": "string", "description": "Path to the file"},
                    "ref": {"type": "string", "description": "Branch/tag/commit reference (optional)"}
                },
                "required": ["owner", "repo", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List contents of a directory in the repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "path": {"type": "string", "description": "Path to the directory"},
                    "ref": {"type": "string", "description": "Branch/tag/commit reference (optional)"}
                },
                "required": ["owner", "repo", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tree",
            "description": "Get the full file tree of the repository. Useful for finding files or understanding repository structure",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "ref": {"type": "string", "description": "Branch/tag/commit reference"},
                    "recursive": {"type": "boolean", "description": "Get full recursive tree (default true)"}
                },
                "required": ["owner", "repo", "ref"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for code in the repository. Supports GitHub code search syntax",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "query": {"type": "string", "description": "Search query (supports filename:, extension:, etc.)"},
                    "per_page": {"type": "integer", "description": "Results per page (default 30)"},
                    "page": {"type": "integer", "description": "Page number (default 1)"}
                },
                "required": ["owner", "repo", "query"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict[str, Any], github_token: str | None = None) -> Any:
    """Execute a tool by name with given arguments."""
    logger.info(f"[execute_tool] Calling {tool_name} with args: {json.dumps(arguments, indent=2)}")
    logger.info(f"[execute_tool] GitHub token present: {github_token is not None}, starts with: {github_token[:15] + '...' if github_token else 'None'}")

    # Add github_token to arguments
    tool_args = {**arguments, "github_token": github_token}

    # Dispatch to GitHub API functions
    # TODO: Add platform detection and dispatch to gitlab/github based on URL
    if tool_name == "get_repo_info":
        return github.get_repo_info(**tool_args)
    elif tool_name == "read_file":
        return github.read_file(**tool_args)
    elif tool_name == "list_directory":
        return github.list_directory(**tool_args)
    elif tool_name == "list_tree":
        return github.list_tree(**tool_args)
    elif tool_name == "search_code":
        return github.search_code(**tool_args)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def ask(repo_url: str, prompt: str, max_iterations: int = 20, github_token: str | None = None, **litellm_config) -> str:
    """
    Ask a question about a GitHub repository.

    Args:
        repo_url: URL of the GitHub repository
        prompt: Question or prompt about the repository
        max_iterations: Maximum number of agentic loop iterations (default: 20)
        github_token: GitHub personal access token for API authentication and private repo access
                     If not provided, will use GITHUB_TOKEN environment variable
        **litellm_config: Additional configuration for litellm.completion()
                         (e.g., model, temperature, max_tokens, etc.)

    Returns:
        Text response to the question
    """
    # Parse repository URL
    # TODO: Add platform detection (GitHub/GitLab) based on URL
    owner, repo = github.parse_repo_url(repo_url)

    # Set default litellm config values
    llm_params = {
        "model": "gpt-5",
        "tools": TOOLS,
        "parallel_tool_calls": True,
    }
    # Override with user-provided config
    llm_params.update(litellm_config)

    # Initialize conversation with system message and user prompt
    messages = [
        {
            "role": "system",
            "content": f"Use GitHub API tools to answer the given questions by exploring and analyzing the repository {owner}/{repo}. Use the API tools like you would use filesystem tools to list and read files. Make tool calls in parallel, and read only enough files to answer the questions."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    # Agentic loop with tool use
    for iteration in range(max_iterations):
        # Call LiteLLM with parallel tool calls enabled
        response = completion(
            messages=messages,
            **llm_params
        )

        message = response.choices[0].message

        # Build assistant message content for conversation
        assistant_msg = {"role": "assistant", "content": []}

        # Handle reasoning/thinking content
        if hasattr(message, "content") and message.content:
            if isinstance(message.content, str):
                assistant_msg["content"].append({"type": "text", "text": message.content})
            elif isinstance(message.content, list):
                assistant_msg["content"].extend(message.content)

        # Add tool calls if present
        if hasattr(message, "tool_calls") and message.tool_calls:
            assistant_msg["tool_calls"] = message.tool_calls
            messages.append(assistant_msg)
        else:
            # No tool calls means we have the final answer
            messages.append(assistant_msg)
            # Extract text from content
            if isinstance(message.content, str):
                return message.content
            elif isinstance(message.content, list):
                text_parts = [block.get("text", "") for block in message.content if isinstance(block, dict) and block.get("type") == "text"]
                return " ".join(text_parts)
            return ""

        # Execute tool calls in parallel
        def execute_single_tool(tool_call):
            """Execute a single tool call and return the result."""
            try:
                arguments = json.loads(tool_call.function.arguments)
                result = execute_tool(tool_call.function.name, arguments, github_token)
                return {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, indent=2)
                }
            except Exception as e:
                logger.error(f"Error executing tool {tool_call.function.name}: {str(e)}")
                return {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Error executing tool: {str(e)}"
                }

        # Use ThreadPoolExecutor to execute tool calls in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tool calls
            futures = {executor.submit(execute_single_tool, tc): tc for tc in message.tool_calls}

            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                messages.append(result)

    return "Maximum iterations reached. Unable to provide a complete answer."
