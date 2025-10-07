import base64
import json
import logging
import os
from typing import Any
from urllib.parse import urlparse, quote

import requests

# Configure logging
logger = logging.getLogger(__name__)


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Parse GitLab URL to extract owner and repo name."""
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitLab URL: {repo_url}")
    return path_parts[0], path_parts[1]


def _get_project_path(owner: str, repo: str) -> str:
    """Get URL-encoded project path for GitLab API."""
    return quote(f"{owner}/{repo}", safe='')


def get_repo_info(owner: str, repo: str, github_token: str | None = None) -> dict[str, Any]:
    """
    Get repository information including default branch.

    Note: Parameter name is github_token for API compatibility, but accepts GitLab tokens.
    """
    project_path = _get_project_path(owner, repo)
    url = f"https://gitlab.com/api/v4/projects/{project_path}"
    logger.info(f"[get_repo_info] GET {url}")

    headers = {}
    token = github_token or os.getenv("GITLAB_TOKEN")
    if token:
        headers["PRIVATE-TOKEN"] = token
        logger.info(f"[get_repo_info] Using GitLab token: {token[:20]}...")
    else:
        logger.warning(f"[get_repo_info] No GitLab token provided!")

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    logger.info(f"[get_repo_info] Response: {json.dumps(data, indent=2)}")
    return data


def read_file(owner: str, repo: str, path: str, ref: str | None = None, github_token: str | None = None) -> str:
    """
    Read a file from the repository.

    Note: Parameter name is github_token for API compatibility, but accepts GitLab tokens.
    """
    project_path = _get_project_path(owner, repo)
    # URL-encode the file path
    encoded_path = quote(path, safe='')
    url = f"https://gitlab.com/api/v4/projects/{project_path}/repository/files/{encoded_path}"

    params = {}
    if ref:
        params["ref"] = ref
    else:
        # GitLab requires ref parameter, default to main
        params["ref"] = "main"

    logger.info(f"[read_file] GET {url} with params {params}")

    headers = {}
    token = github_token or os.getenv("GITLAB_TOKEN")
    if token:
        headers["PRIVATE-TOKEN"] = token

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    if "content" in data:
        # GitLab returns base64-encoded content
        content = base64.b64decode(data["content"]).decode("utf-8")
        logger.info(f"[read_file] Successfully read file (length: {len(content)} chars)")
        return content
    raise ValueError(f"Path {path} is not a file")


def list_directory(owner: str, repo: str, path: str, ref: str | None = None, github_token: str | None = None) -> list[dict[str, Any]]:
    """
    List contents of a directory.

    Note: Parameter name is github_token for API compatibility, but accepts GitLab tokens.
    """
    project_path = _get_project_path(owner, repo)
    url = f"https://gitlab.com/api/v4/projects/{project_path}/repository/tree"

    params = {}
    if path and path != ".":
        params["path"] = path
    if ref:
        params["ref"] = ref
    else:
        params["ref"] = "main"

    logger.info(f"[list_directory] GET {url} with params {params}")

    headers = {}
    token = github_token or os.getenv("GITLAB_TOKEN")
    if token:
        headers["PRIVATE-TOKEN"] = token

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list):
        result = [{"name": item["name"], "type": item["type"], "path": item["path"]} for item in data]
        logger.info(f"[list_directory] Found {len(result)} items: {json.dumps(result, indent=2)}")
        return result
    raise ValueError(f"Path {path} is not a directory")


def list_tree(owner: str, repo: str, ref: str, recursive: bool = True, github_token: str | None = None) -> list[dict[str, Any]]:
    """
    Get the full file tree of the repository.

    Note: Parameter name is github_token for API compatibility, but accepts GitLab tokens.
    """
    project_path = _get_project_path(owner, repo)
    url = f"https://gitlab.com/api/v4/projects/{project_path}/repository/tree"

    params = {"ref": ref}
    if recursive:
        params["recursive"] = "true"
        # GitLab limits recursive queries, use pagination
        params["per_page"] = "100"

    logger.info(f"[list_tree] GET {url} with params {params}")

    headers = {}
    token = github_token or os.getenv("GITLAB_TOKEN")
    if token:
        headers["PRIVATE-TOKEN"] = token

    all_items = []
    page = 1

    while True:
        params["page"] = str(page)
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            break

        all_items.extend(data)

        # Check if there are more pages
        if "x-next-page" not in response.headers or not response.headers["x-next-page"]:
            break

        page += 1

    result = [{"path": item["path"], "type": item["type"]} for item in all_items]
    logger.info(f"[list_tree] Found {len(result)} items in tree")
    return result


def search_code(owner: str, repo: str, query: str, per_page: int = 30, page: int = 1, github_token: str | None = None) -> dict[str, Any]:
    """
    Search for code in the repository.

    Note: Parameter name is github_token for API compatibility, but accepts GitLab tokens.
    """
    project_path = _get_project_path(owner, repo)
    url = f"https://gitlab.com/api/v4/projects/{project_path}/search"

    params = {
        "scope": "blobs",
        "search": query,
        "per_page": str(per_page),
        "page": str(page)
    }

    logger.info(f"[search_code] GET {url} with params {params}")

    headers = {}
    token = github_token or os.getenv("GITLAB_TOKEN")
    if token:
        headers["PRIVATE-TOKEN"] = token

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    if isinstance(data, list):
        for item in data:
            results.append({
                "path": item.get("path", ""),
                "name": item.get("filename", ""),
                "url": item.get("project_id", "")  # GitLab doesn't return direct HTML URL in search
            })

    # GitLab doesn't return total_count in search API, estimate from results
    result = {"total_count": len(results), "items": results}
    logger.info(f"[search_code] Response: {json.dumps(result, indent=2)}")
    return result
