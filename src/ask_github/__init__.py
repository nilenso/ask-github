import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import os
import re
from typing import Any
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
import litellm
from litellm import completion

# Load environment variables from .env file
load_dotenv()

# Enable litellm logging
os.environ['LITELLM_LOG'] = 'INFO'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Parse GitHub URL to extract owner and repo name."""
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    return path_parts[0], path_parts[1]


# GitHub API wrapper functions
def get_repo_info(owner: str, repo: str) -> dict[str, Any]:
    """Get repository information including default branch."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    logger.info(f"[get_repo_info] GET {url}")

    headers = {}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    logger.info(f"[get_repo_info] Response: {json.dumps(data, indent=2)}")
    return data


def read_file(owner: str, repo: str, path: str, ref: str | None = None) -> str:
    """Read a file from the repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    if ref:
        url += f"?ref={ref}"
    logger.info(f"[read_file] GET {url}")

    headers = {}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict) and "content" in data:
        content = base64.b64decode(data["content"]).decode("utf-8")
        logger.info(f"[read_file] Successfully read file (length: {len(content)} chars)")
        return content
    raise ValueError(f"Path {path} is not a file")


def list_directory(owner: str, repo: str, path: str, ref: str | None = None) -> list[dict[str, Any]]:
    """List contents of a directory."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    if ref:
        url += f"?ref={ref}"
    logger.info(f"[list_directory] GET {url}")

    headers = {}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list):
        result = [{"name": item["name"], "type": item["type"], "path": item["path"]} for item in data]
        logger.info(f"[list_directory] Found {len(result)} items: {json.dumps(result, indent=2)}")
        return result
    raise ValueError(f"Path {path} is not a directory")


def list_tree(owner: str, repo: str, ref: str, recursive: bool = True) -> list[dict[str, Any]]:
    """Get the full file tree of the repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}"
    if recursive:
        url += "?recursive=1"
    logger.info(f"[list_tree] GET {url}")

    headers = {}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    if "tree" in data:
        result = [{"path": item["path"], "type": item["type"]} for item in data["tree"]]
        logger.info(f"[list_tree] Found {len(result)} items in tree")
        return result
    return []


def search_code(owner: str, repo: str, query: str, per_page: int = 30, page: int = 1) -> dict[str, Any]:
    """Search for code in the repository."""
    search_query = f"{query}+repo:{owner}/{repo}"
    url = f"https://api.github.com/search/code?q={search_query}&per_page={per_page}&page={page}"
    logger.info(f"[search_code] GET {url}")

    headers = {}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "path": item["path"],
            "name": item["name"],
            "url": item["html_url"]
        })

    result = {"total_count": data.get("total_count", 0), "items": results}
    logger.info(f"[search_code] Response: {json.dumps(result, indent=2)}")
    return result


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


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
    """Execute a tool by name with given arguments."""
    logger.info(f"[execute_tool] Calling {tool_name} with args: {json.dumps(arguments, indent=2)}")

    if tool_name == "get_repo_info":
        return get_repo_info(**arguments)
    elif tool_name == "read_file":
        return read_file(**arguments)
    elif tool_name == "list_directory":
        return list_directory(**arguments)
    elif tool_name == "list_tree":
        return list_tree(**arguments)
    elif tool_name == "search_code":
        return search_code(**arguments)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def ask(repo_url: str, prompt: str, max_iterations: int = 150, **litellm_config) -> str:
    """
    Ask a question about a GitHub repository.

    Args:
        repo_url: URL of the GitHub repository
        prompt: Question or prompt about the repository
        max_iterations: Maximum number of agentic loop iterations (default: 150)
        **litellm_config: Additional configuration for litellm.completion()
                         (e.g., model, temperature, max_tokens, etc.)

    Returns:
        Text response to the question
    """
    # Parse repository URL
    owner, repo = parse_repo_url(repo_url)

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
            "content": f"You are an expert code analyst. You have access to GitHub API tools to explore and analyze the repository {owner}/{repo}. Use the tools to gather information and answer the user's question thoroughly."
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
                result = execute_tool(tool_call.function.name, arguments)
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
