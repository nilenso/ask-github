import base64
import json
import logging
import os
from typing import Any
from urllib.parse import urlparse

import requests

# Configure logging
logger = logging.getLogger(__name__)


def parse_repo_url(repo_url: str) -> tuple[str, str, str | None]:
    """
    Parse GitHub URL to extract owner, repo name, and optional ref.

    Supports:
    - https://github.com/owner/repo -> (owner, repo, None)
    - https://github.com/owner/repo/tree/branch -> (owner, repo, branch)
    - https://github.com/owner/repo/blob/branch/path -> (owner, repo, branch)
    - https://github.com/owner/repo/commit/sha -> (owner, repo, sha)
    """
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip("/").split("/")

    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")

    owner = path_parts[0]
    repo = path_parts[1]
    ref = None

    # Extract ref from tree/blob/commit URLs
    if len(path_parts) >= 4 and path_parts[2] in ["tree", "blob", "commit"]:
        ref = path_parts[3]

    return owner, repo, ref


def get_repo_info(owner: str, repo: str, github_token: str | None = None) -> dict[str, Any]:
    """Get repository information including default branch."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    logger.debug(f"[get_repo_info] GET {url}")

    headers = {}
    token = github_token or os.getenv("GITHUB_TOKEN")
    if token:
        # Use Bearer for fine-grained tokens (github_pat_*), token for classic tokens (ghp_*)
        prefix = "Bearer" if token.startswith("github_pat_") else "token"
        headers["Authorization"] = f"{prefix} {token}"
        logger.debug(f"[get_repo_info] Using {prefix} auth")

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    logger.debug(f"[get_repo_info] Got default_branch: {data.get('default_branch')}")
    return data


def read_file(owner: str, repo: str, path: str, ref: str | None = None, github_token: str | None = None) -> str:
    """Read a file from the repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    if ref:
        url += f"?ref={ref}"
    logger.debug(f"[read_file] GET {url}")

    headers = {}
    token = github_token or os.getenv("GITHUB_TOKEN")
    if token:
        # Use Bearer for fine-grained tokens (github_pat_*), token for classic tokens (ghp_*)
        prefix = "Bearer" if token.startswith("github_pat_") else "token"
        headers["Authorization"] = f"{prefix} {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict) and "content" in data:
        content = base64.b64decode(data["content"]).decode("utf-8")
        logger.debug(f"[read_file] Read {len(content)} chars")
        return content
    raise ValueError(f"Path {path} is not a file")


def list_directory(owner: str, repo: str, path: str, ref: str | None = None, github_token: str | None = None) -> list[dict[str, Any]]:
    """List contents of a directory."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    if ref:
        url += f"?ref={ref}"
    logger.debug(f"[list_directory] GET {url}")

    headers = {}
    token = github_token or os.getenv("GITHUB_TOKEN")
    if token:
        # Use Bearer for fine-grained tokens (github_pat_*), token for classic tokens (ghp_*)
        prefix = "Bearer" if token.startswith("github_pat_") else "token"
        headers["Authorization"] = f"{prefix} {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list):
        result = [{"name": item["name"], "type": item["type"], "path": item["path"]} for item in data]
        logger.debug(f"[list_directory] Found {len(result)} items")
        return result
    raise ValueError(f"Path {path} is not a directory")


def list_tree(owner: str, repo: str, ref: str, recursive: bool = True, github_token: str | None = None) -> list[dict[str, Any]]:
    """Get the full file tree of the repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}"
    if recursive:
        url += "?recursive=1"
    logger.debug(f"[list_tree] GET {url}")

    headers = {}
    token = github_token or os.getenv("GITHUB_TOKEN")
    if token:
        # Use Bearer for fine-grained tokens (github_pat_*), token for classic tokens (ghp_*)
        prefix = "Bearer" if token.startswith("github_pat_") else "token"
        headers["Authorization"] = f"{prefix} {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    if "tree" in data:
        result = [{"path": item["path"], "type": item["type"]} for item in data["tree"]]
        logger.debug(f"[list_tree] Found {len(result)} items")
        return result
    return []


def search_code(owner: str, repo: str, query: str, per_page: int = 30, page: int = 1, github_token: str | None = None) -> dict[str, Any]:
    """Search for code in the repository."""
    search_query = f"{query}+repo:{owner}/{repo}"
    url = f"https://api.github.com/search/code?q={search_query}&per_page={per_page}&page={page}"
    logger.debug(f"[search_code] GET {url}")

    headers = {}
    token = github_token or os.getenv("GITHUB_TOKEN")
    if token:
        # Use Bearer for fine-grained tokens (github_pat_*), token for classic tokens (ghp_*)
        prefix = "Bearer" if token.startswith("github_pat_") else "token"
        headers["Authorization"] = f"{prefix} {token}"

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
    logger.debug(f"[search_code] Found {result['total_count']} results")
    return result
