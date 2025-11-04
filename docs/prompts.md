Here is the GitLab equivalent of your GitHub read-only tool set, using **GitLab REST API v4**.
All endpoints are public in their [official docs](https://docs.gitlab.com/ee/api/).

```markdown
## 1. Repo & Branch Info

**`get_repo_info`**

* **Args:** `{project_id_or_path}`
* **API:** `GET /projects/{id}`
* **Docs:** [Get single project](https://docs.gitlab.com/ee/api/projects.html#get-single-project)
* **Returns:** default branch, visibility, metadata.
* **Example:**
```

curl "[https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central](https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central)"

```

**`list_branches`**

* **Args:** `{project_id_or_path}`
* **API:** `GET /projects/{id}/repository/branches`
* **Docs:** [List repository branches](https://docs.gitlab.com/ee/api/branches.html#list-repository-branches)
* **Example:**
```

curl "[https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/repository/branches](https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/repository/branches)"

```

---

## 2. File & Directory Access

**`read_file`**

* **Args:** `{project_id_or_path, file_path, ref}`
* **API:** `GET /projects/{id}/repository/files/{file_path}?ref={ref}`
* **Docs:** [Get file from repository](https://docs.gitlab.com/ee/api/repository_files.html#get-file-from-repository)
* **Returns:** base64-encoded file content, metadata.
* **Example:**
```

curl "[https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/repository/files/README.md?ref=main](https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/repository/files/README.md?ref=main)"

```

**`list_directory`**

* **Args:** `{project_id_or_path, path?, ref?}`
* **API:** `GET /projects/{id}/repository/tree?path={path}&ref={ref}`
* **Docs:** [List repository tree](https://docs.gitlab.com/ee/api/repositories.html#list-repository-tree)
* **Example:**
```

curl "[https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/repository/tree?path=app&ref=main](https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/repository/tree?path=app&ref=main)"

```

**`list_tree`**

* **Args:** `{project_id_or_path, ref, recursive?}`
* **API:** `GET /projects/{id}/repository/tree?ref={ref}&recursive=true`
* **Docs:** [List repository tree](https://docs.gitlab.com/ee/api/repositories.html#list-repository-tree)
* **Returns:** full file list. Enables glob-style filtering client-side.
* **Example:**
```

curl "[https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/repository/tree?ref=main&recursive=true](https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/repository/tree?ref=main&recursive=true)"

```

---

## 3. Code Search

**`search_code`**

* **Args:** `{project_id_or_path, scope, search}`
* **API:** `GET /projects/{id}/search?scope=blobs&search={term}`
* **Docs:** [Project search](https://docs.gitlab.com/ee/api/search.html#scope-blobs)
* **Returns:** list of matching files and line excerpts.
* **Example:**
```

curl "[https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/search?scope=blobs&search=package.json](https://gitlab.com/api/v4/projects/nilenso%2Fgrand-central/search?scope=blobs&search=package.json)"

```
```
