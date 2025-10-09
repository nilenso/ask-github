from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import os
from typing import Any, Literal
from urllib.parse import urlparse

from dotenv import load_dotenv
import litellm
from litellm import completion

from . import github, gitlab

# Load environment variables from .env file
load_dotenv()

# Enable litellm logging
# os.environ['LITELLM_LOG'] = 'INFO'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Platform = Literal["github", "gitlab"]


def detect_platform(repo_url: str) -> Platform:
    """Detect the platform (GitHub or GitLab) from the repository URL."""
    parsed = urlparse(repo_url)
    hostname = parsed.hostname or ""

    if "github.com" in hostname:
        return "github"
    elif "gitlab.com" in hostname:
        return "gitlab"
    else:
        # Default to GitHub for unknown domains
        logger.debug(f"Unknown platform for URL {repo_url}, defaulting to GitHub")
        return "github"


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


def _get_module(platform: Platform):
    """Get the platform-specific module (github or gitlab)."""
    return github if platform == "github" else gitlab


def _get_auth_token(platform: Platform, token: str | None = None, github_token: str | None = None) -> str | None:
    """
    Get authentication token for the platform.

    Args:
        platform: The platform (github or gitlab)
        token: Explicitly provided token
        github_token: Legacy token parameter (deprecated)

    Returns:
        The authentication token or None
    """
    auth_token = token or github_token
    if not auth_token:
        env_var = "GITHUB_TOKEN" if platform == "github" else "GITLAB_TOKEN"
        auth_token = os.getenv(env_var)
        if auth_token:
            logger.debug(f"Using {env_var} from environment")
    return auth_token


def _get_ref(module, owner: str, repo: str, ref: str | None, auth_token: str | None) -> str:
    """
    Get the git reference (branch/tag/commit) to use.

    Args:
        module: Platform module (github or gitlab)
        owner: Repository owner
        repo: Repository name
        ref: Reference from URL (may be None)
        auth_token: Authentication token

    Returns:
        The resolved reference (branch name, tag, or commit SHA)
    """
    if ref is None:
        repo_info = module.get_repo_info(owner, repo, github_token=auth_token)
        ref = repo_info.get("default_branch", "main")
        logger.debug(f"No ref in URL, using default branch: {ref}")
    else:
        logger.debug(f"Using ref from URL: {ref}")
    return ref


def execute_tool(tool_name: str, arguments: dict[str, Any], platform: Platform, token: str | None = None, default_ref: str | None = None) -> Any:
    """Execute a tool by name with given arguments on the specified platform."""
    logger.info(f"{tool_name}({', '.join(f'{k}={v}' for k, v in arguments.items())})")
    logger.debug(f"[execute_tool] Platform: {platform}, Token present: {token is not None}")

    # Add token to arguments (parameter name is github_token for API compatibility)
    tool_args = {**arguments, "github_token": token}

    # Tools that accept a ref parameter
    tools_with_ref = ["read_file", "list_directory", "list_tree"]

    # If the tool accepts ref and none was provided, use the default ref
    if tool_name in tools_with_ref and "ref" not in arguments and default_ref:
        tool_args["ref"] = default_ref
        logger.debug(f"[execute_tool] Injecting default ref: {default_ref}")

    # Select platform module
    module = _get_module(platform)

    # Dispatch to platform-specific API functions
    if tool_name == "get_repo_info":
        return module.get_repo_info(**tool_args)
    elif tool_name == "read_file":
        return module.read_file(**tool_args)
    elif tool_name == "list_directory":
        return module.list_directory(**tool_args)
    elif tool_name == "list_tree":
        return module.list_tree(**tool_args)
    elif tool_name == "search_code":
        return module.search_code(**tool_args)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def ask(repo_url: str, prompt: str, max_iterations: int = 20, max_workers: int = 15, token: str | None = None, github_token: str | None = None, **litellm_config) -> str:
    """
    Ask a question about a GitHub or GitLab repository.

    Args:
        repo_url: URL of the GitHub or GitLab repository (can include branch, e.g., /tree/branch-name)
        prompt: Question or prompt about the repository
        max_iterations: Maximum number of agentic loop iterations (default: 20)
        max_workers: Maximum number of parallel tool calls (default: 15)
        token: API token for authentication and private repo access
               If not provided, will use GITHUB_TOKEN or GITLAB_TOKEN environment variable
        github_token: (Deprecated) Use 'token' parameter instead. Kept for backwards compatibility.
        **litellm_config: Additional configuration for litellm.completion()
                         (e.g., model, temperature, max_tokens, etc.)

    Returns:
        Text response to the question
    """
    # Detect platform from URL
    platform = detect_platform(repo_url)
    logger.debug(f"[ask] Detected platform: {platform}")

    # Parse repository URL using platform-specific parser
    module = _get_module(platform)
    owner, repo, ref = module.parse_repo_url(repo_url)

    # Get authentication token
    auth_token = _get_auth_token(platform, token, github_token)

    # Resolve git reference (branch/tag/commit)
    ref = _get_ref(module, owner, repo, ref, auth_token)

    # Set default litellm config values
    llm_params = {
        "model": "gpt-5",
        "tools": TOOLS,
        "parallel_tool_calls": True,
    }
    # Override with user-provided config
    llm_params.update(litellm_config)

    # Initialize conversation with system message and user prompt
    platform_name = "GitHub" if platform == "github" else "GitLab"
    messages = [
        {
            "role": "system",
            "content": f"Use {platform_name} API tools to answer the given questions by exploring and analyzing the repository {owner}/{repo} (branch: {ref}). Use the API tools like you would use filesystem tools to list and read files. You can execute up to {max_workers} tool calls in parallel - use this to your advantage by batching file reads and directory listings. When calling tools that accept a 'ref' parameter, you can omit it to use the default branch '{ref}', or specify a different branch/commit if needed. Call list_tree and get_repo_info first in parallel, and then use the list of files and directories to issue many read_file calls in parallel."
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
                result = execute_tool(tool_call.function.name, arguments, platform, auth_token, default_ref=ref)
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
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tool calls
            futures = {executor.submit(execute_single_tool, tc): tc for tc in message.tool_calls}

            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                messages.append(result)

    return "Maximum iterations reached. Unable to provide a complete answer."


def list_tree(repo_url: str, recursive: bool = True, token: str | None = None) -> list[dict[str, Any]]:
    """
    Get the file tree of a repository directly without using LLM.

    Args:
        repo_url: URL of the GitHub or GitLab repository (can include branch, e.g., /tree/branch-name)
        recursive: Get full recursive tree (default: True)
        token: API token for authentication and private repo access
               If not provided, will use GITHUB_TOKEN or GITLAB_TOKEN environment variable

    Returns:
        List of dictionaries with 'path' and 'type' keys for each file/directory
    """
    # Detect platform from URL
    platform = detect_platform(repo_url)
    logger.debug(f"[list_tree] Detected platform: {platform}")

    # Parse repository URL using platform-specific parser
    module = _get_module(platform)
    owner, repo, ref = module.parse_repo_url(repo_url)

    # Get authentication token
    auth_token = _get_auth_token(platform, token)

    # Resolve git reference (branch/tag/commit)
    ref = _get_ref(module, owner, repo, ref, auth_token)

    # Call tool directly
    return module.list_tree(owner, repo, ref, recursive, github_token=auth_token)
