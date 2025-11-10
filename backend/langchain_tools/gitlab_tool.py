"""
GitLab tool wrapper for LangChain.

Provides GitLab repository operations with:
- File reading from repositories
- Code search across projects
- Commit history viewing
- Merge request information
- Issue listing and tracking
"""

from typing import Any, Dict, List, Optional

import gitlab
from langchain_core.tools import BaseTool, tool
from loguru import logger

from .base import BaseLangChainTool


class GitLabTool(BaseLangChainTool):
    """
    GitLab repository tool wrapper.

    Configuration schema:
    {
        "gitlab_url": str,           # GitLab instance URL (default: https://gitlab.com)
        "access_token": str,         # Personal or Project Access Token (encrypted)
        "default_project": str,      # Default project (format: namespace/project)
        "rate_limit": int,           # API rate limit (default: 600 req/min)
        "timeout": int,              # Request timeout in seconds (default: 30)
    }

    Scopes required for access token:
    - read_api: Read API access
    - read_repository: Read repository contents
    """

    def get_tool_type(self) -> str:
        """
        Get the tool type identifier.

        Returns:
            str: Tool type "gitlab"
        """
        return "gitlab"

    def get_encrypted_fields(self) -> List[str]:
        """
        Get list of fields that should be encrypted in storage.

        Access tokens are automatically encrypted using Fernet
        encryption before being stored in the database.

        Returns:
            List[str]: Field names requiring encryption (["access_token"])
        """
        return ["access_token"]

    def get_required_fields(self) -> List[str]:
        """
        Get list of required configuration fields.

        These fields must be present in the configuration dict
        for the tool to function properly. Validation will fail
        if any required field is missing.

        Returns:
            List[str]: Required field names for GitLab connection
        """
        return ["access_token"]

    async def validate_config(self) -> None:
        """Validate GitLab configuration."""
        self.validate_required_fields()

        # Validate GitLab URL format
        gitlab_url = self.config.get("gitlab_url", "https://gitlab.com")
        if not gitlab_url.startswith("http"):
            raise ValueError(f"Invalid gitlab_url: {gitlab_url}. Must start with http:// or https://")

        # Validate default_project format (optional)
        default_project = self.config.get("default_project")
        if default_project and "/" not in default_project:
            raise ValueError(
                f"Invalid default_project format: {default_project}. "
                f"Must be in format 'namespace/project' (e.g., 'myorg/myapp')"
            )

        # Validate rate_limit
        rate_limit = self.config.get("rate_limit", 600)
        if not isinstance(rate_limit, int) or rate_limit < 1:
            raise ValueError(f"Invalid rate_limit: {rate_limit}. Must be positive integer")

        # Validate timeout
        timeout = self.config.get("timeout", 30)
        if not isinstance(timeout, int) or timeout < 1 or timeout > 120:
            raise ValueError(f"Invalid timeout: {timeout}. Must be between 1 and 120")

    async def create_tools(self) -> List[BaseTool]:
        """
        Create GitLab tools.

        Returns:
            List of tools:
            - gitlab_read_file: Read file from repository
            - gitlab_search_code: Search code across project
            - gitlab_list_commits: List commit history
            - gitlab_get_merge_request: Get MR details
            - gitlab_list_issues: List issues
        """
        await self.validate_config()
        decrypted_config = self.decrypt_config()

        # Create GitLab client
        gl = self._create_client(decrypted_config)

        # Create tools with config closure
        tools = [
            self._create_read_file_tool(gl, decrypted_config),
            self._create_search_code_tool(gl, decrypted_config),
            self._create_list_commits_tool(gl, decrypted_config),
            self._create_get_merge_request_tool(gl, decrypted_config),
            self._create_list_issues_tool(gl, decrypted_config),
        ]

        logger.info(f"Created {len(tools)} GitLab tools")
        return tools

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test GitLab connection.

        Returns:
            Test result dictionary with success status and details
        """
        try:
            await self.validate_config()
            decrypted_config = self.decrypt_config()

            # Create GitLab client
            gl = self._create_client(decrypted_config)

            # Test authentication
            current_user = gl.user
            user_info = {
                "username": current_user.username,
                "name": current_user.name,
                "id": current_user.id,
            }

            # Test default project access if configured
            default_project = decrypted_config.get("default_project")
            if default_project:
                try:
                    project = gl.projects.get(default_project)
                    project_info = {
                        "name": project.name,
                        "path": project.path_with_namespace,
                        "visibility": project.visibility,
                    }
                except gitlab.exceptions.GitlabGetError as e:
                    return {
                        "success": False,
                        "message": f"Authentication successful but cannot access project '{default_project}': {e}",
                        "details": {"user": user_info},
                    }

                return {
                    "success": True,
                    "message": "Connection successful",
                    "details": {
                        "user": user_info,
                        "project": project_info,
                        "gitlab_url": decrypted_config.get("gitlab_url", "https://gitlab.com"),
                    },
                }
            else:
                return {
                    "success": True,
                    "message": "Connection successful (no default project configured)",
                    "details": {
                        "user": user_info,
                        "gitlab_url": decrypted_config.get("gitlab_url", "https://gitlab.com"),
                    },
                }

        except gitlab.exceptions.GitlabAuthenticationError as e:
            logger.error(f"GitLab authentication failed: {e}")
            return {
                "success": False,
                "message": f"Authentication failed: {str(e)}. Check access token.",
            }
        except Exception as e:
            logger.error(f"GitLab connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
            }

    def _create_client(self, config: Dict[str, Any]) -> gitlab.Gitlab:
        """
        Create GitLab client from configuration.

        Args:
            config: Decrypted configuration dictionary

        Returns:
            GitLab client instance
        """
        gitlab_url = config.get("gitlab_url", "https://gitlab.com")
        access_token = config["access_token"]
        timeout = config.get("timeout", 30)

        gl = gitlab.Gitlab(
            url=gitlab_url,
            private_token=access_token,
            timeout=timeout,
        )

        # Authenticate
        gl.auth()

        return gl

    def _create_read_file_tool(self, gl: gitlab.Gitlab, config: Dict[str, Any]) -> BaseTool:
        """Create gitlab_read_file tool."""
        default_project = config.get("default_project")

        @tool
        def gitlab_read_file(
            file_path: str,
            project: Optional[str] = None,
            branch: str = "main",
        ) -> str:
            """
            Read file content from GitLab repository.

            Args:
                file_path: Path to file in repository (e.g., "src/main.py")
                project: Project path (namespace/project). Uses default if not specified.
                branch: Branch name (default: main)

            Returns:
                File content as string

            Example:
                gitlab_read_file("README.md", branch="develop")
            """
            try:
                project_path = project or default_project
                if not project_path:
                    return "Error: No project specified and no default project configured"

                # Get project
                proj = gl.projects.get(project_path)

                # Get file
                file_data = proj.files.get(file_path=file_path, ref=branch)
                content = file_data.decode().decode('utf-8')

                return f"File: {file_path}\nBranch: {branch}\nProject: {project_path}\n\n{content}"

            except gitlab.exceptions.GitlabGetError as e:
                logger.error(f"GitLab file read failed: {e}")
                return f"Error: File not found or access denied: {str(e)}"
            except Exception as e:
                logger.error(f"GitLab file read failed: {e}")
                return f"Error: {str(e)}"

        return gitlab_read_file

    def _create_search_code_tool(self, gl: gitlab.Gitlab, config: Dict[str, Any]) -> BaseTool:
        """Create gitlab_search_code tool."""
        default_project = config.get("default_project")

        @tool
        def gitlab_search_code(
            query: str,
            project: Optional[str] = None,
            scope: str = "blobs",
        ) -> str:
            """
            Search code across GitLab project.

            Args:
                query: Search query string
                project: Project path (namespace/project). Uses default if not specified.
                scope: Search scope (blobs, commits, issues, merge_requests, wiki_blobs)

            Returns:
                Search results as formatted string

            Example:
                gitlab_search_code("def calculate_total", scope="blobs")
            """
            try:
                project_path = project or default_project
                if not project_path:
                    return "Error: No project specified and no default project configured"

                # Get project
                proj = gl.projects.get(project_path)

                # Search
                results = proj.search(scope, query)

                if not results:
                    return f"No results found for query: {query}"

                # Format results
                output = [f"Search results for '{query}' in {project_path}:\n"]

                for i, result in enumerate(results[:20], 1):  # Limit to 20 results
                    if scope == "blobs":
                        output.append(f"{i}. {result['filename']} (line {result.get('startline', 'N/A')})")
                        output.append(f"   {result.get('data', '')[:200]}...")
                    elif scope == "commits":
                        output.append(f"{i}. {result['title']}")
                        output.append(f"   Author: {result.get('author_name')}")
                        output.append(f"   Date: {result.get('committed_date')}")
                    elif scope == "issues":
                        output.append(f"{i}. #{result['iid']}: {result['title']}")
                        output.append(f"   State: {result.get('state')}")
                    elif scope == "merge_requests":
                        output.append(f"{i}. !{result['iid']}: {result['title']}")
                        output.append(f"   State: {result.get('state')}")

                    output.append("")

                return "\n".join(output)

            except gitlab.exceptions.GitlabGetError as e:
                logger.error(f"GitLab search failed: {e}")
                return f"Error: Project not found or access denied: {str(e)}"
            except Exception as e:
                logger.error(f"GitLab search failed: {e}")
                return f"Error: {str(e)}"

        return gitlab_search_code

    def _create_list_commits_tool(self, gl: gitlab.Gitlab, config: Dict[str, Any]) -> BaseTool:
        """Create gitlab_list_commits tool."""
        default_project = config.get("default_project")

        @tool
        def gitlab_list_commits(
            project: Optional[str] = None,
            branch: str = "main",
            limit: int = 10,
            since: Optional[str] = None,
        ) -> str:
            """
            List commit history from GitLab repository.

            Args:
                project: Project path (namespace/project). Uses default if not specified.
                branch: Branch name (default: main)
                limit: Maximum number of commits (default: 10, max: 100)
                since: ISO 8601 date string (e.g., "2025-01-01T00:00:00Z")

            Returns:
                Commit history as formatted string

            Example:
                gitlab_list_commits(branch="develop", limit=5)
            """
            try:
                project_path = project or default_project
                if not project_path:
                    return "Error: No project specified and no default project configured"

                # Limit to 100 commits max
                limit = min(limit, 100)

                # Get project
                proj = gl.projects.get(project_path)

                # Get commits
                kwargs = {"ref_name": branch, "per_page": limit}
                if since:
                    kwargs["since"] = since

                commits = proj.commits.list(**kwargs)

                if not commits:
                    return f"No commits found in branch '{branch}'"

                # Format commits
                output = [f"Recent commits in {project_path} ({branch}):\n"]

                for i, commit in enumerate(commits, 1):
                    output.append(f"{i}. [{commit.short_id}] {commit.title}")
                    output.append(f"   Author: {commit.author_name}")
                    output.append(f"   Date: {commit.committed_date}")
                    output.append("")

                return "\n".join(output)

            except gitlab.exceptions.GitlabGetError as e:
                logger.error(f"GitLab list commits failed: {e}")
                return f"Error: Project or branch not found: {str(e)}"
            except Exception as e:
                logger.error(f"GitLab list commits failed: {e}")
                return f"Error: {str(e)}"

        return gitlab_list_commits

    def _create_get_merge_request_tool(self, gl: gitlab.Gitlab, config: Dict[str, Any]) -> BaseTool:
        """Create gitlab_get_merge_request tool."""
        default_project = config.get("default_project")

        @tool
        def gitlab_get_merge_request(
            mr_iid: int,
            project: Optional[str] = None,
        ) -> str:
            """
            Get merge request details from GitLab.

            Args:
                mr_iid: Merge request IID (internal ID, e.g., 123)
                project: Project path (namespace/project). Uses default if not specified.

            Returns:
                Merge request details as formatted string

            Example:
                gitlab_get_merge_request(42)
            """
            try:
                project_path = project or default_project
                if not project_path:
                    return "Error: No project specified and no default project configured"

                # Get project
                proj = gl.projects.get(project_path)

                # Get MR
                mr = proj.mergerequests.get(mr_iid)

                # Format MR details
                output = [
                    f"Merge Request !{mr.iid}: {mr.title}",
                    f"Project: {project_path}",
                    f"",
                    f"Author: {mr.author['name']}",
                    f"State: {mr.state}",
                    f"Source: {mr.source_branch} → Target: {mr.target_branch}",
                    f"Created: {mr.created_at}",
                    f"Updated: {mr.updated_at}",
                    f"",
                    f"Description:",
                    f"{mr.description or '(no description)'}",
                    f"",
                    f"Stats:",
                    f"  Upvotes: {mr.upvotes}",
                    f"  Downvotes: {mr.downvotes}",
                    f"  Changes: {mr.changes_count}",
                    f"",
                ]

                # Add labels if any
                if mr.labels:
                    output.append(f"Labels: {', '.join(mr.labels)}")

                return "\n".join(output)

            except gitlab.exceptions.GitlabGetError as e:
                logger.error(f"GitLab get MR failed: {e}")
                return f"Error: Merge request not found: {str(e)}"
            except Exception as e:
                logger.error(f"GitLab get MR failed: {e}")
                return f"Error: {str(e)}"

        return gitlab_get_merge_request

    def _create_list_issues_tool(self, gl: gitlab.Gitlab, config: Dict[str, Any]) -> BaseTool:
        """Create gitlab_list_issues tool."""
        default_project = config.get("default_project")

        @tool
        def gitlab_list_issues(
            project: Optional[str] = None,
            state: str = "opened",
            labels: Optional[str] = None,
            limit: int = 10,
        ) -> str:
            """
            List issues from GitLab project.

            Args:
                project: Project path (namespace/project). Uses default if not specified.
                state: Issue state (opened, closed, all) (default: opened)
                labels: Comma-separated label names to filter (e.g., "bug,urgent")
                limit: Maximum number of issues (default: 10, max: 100)

            Returns:
                Issue list as formatted string

            Example:
                gitlab_list_issues(state="opened", labels="bug")
            """
            try:
                project_path = project or default_project
                if not project_path:
                    return "Error: No project specified and no default project configured"

                # Limit to 100 issues max
                limit = min(limit, 100)

                # Get project
                proj = gl.projects.get(project_path)

                # Get issues
                kwargs = {"state": state, "per_page": limit}
                if labels:
                    kwargs["labels"] = labels.split(",")

                issues = proj.issues.list(**kwargs)

                if not issues:
                    return f"No {state} issues found"

                # Format issues
                output = [f"Issues in {project_path} (state: {state}):\n"]

                for i, issue in enumerate(issues, 1):
                    output.append(f"{i}. #{issue.iid}: {issue.title}")
                    output.append(f"   State: {issue.state}")
                    output.append(f"   Author: {issue.author['name']}")
                    output.append(f"   Created: {issue.created_at}")
                    if issue.labels:
                        output.append(f"   Labels: {', '.join(issue.labels)}")
                    output.append("")

                return "\n".join(output)

            except gitlab.exceptions.GitlabGetError as e:
                logger.error(f"GitLab list issues failed: {e}")
                return f"Error: Project not found or access denied: {str(e)}"
            except Exception as e:
                logger.error(f"GitLab list issues failed: {e}")
                return f"Error: {str(e)}"

        return gitlab_list_issues
