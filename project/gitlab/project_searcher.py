"""
GitLab 项目搜索工具类
功能：根据项目 ID 搜索 GitLab 仓库，获取项目信息（如 web_url、path_with_namespace 等）
"""
import requests
from typing import Optional, List, Dict


class GitLabProjectSearcher:
    """
    GitLab 项目搜索类
    用于根据项目 ID 搜索并获取 GitLab 仓库信息
    """

    def __init__(self, gitlab_token: str, gitlab_url: str = "https://gitlab.com"):
        """
        初始化 GitLab 搜索客户端

        Args:
            gitlab_token: GitLab Personal Access Token (需要 api 权限)
            gitlab_url: GitLab 实例 URL，默认使用 gitlab.com
        """
        self.gitlab_url = gitlab_url.rstrip("/")
        self.token = gitlab_token
        self.headers = {
            "Content-Type": "application/json",
            "PRIVATE-TOKEN": self.token,
        }
        self.api_base_url = f"{self.gitlab_url}/api/v4"

    def search_projects(self, search_query: str, per_page: int = 20) -> List[Dict]:
        """
        搜索 GitLab 项目

        Args:
            search_query: 搜索关键词（可以是项目 ID、项目名称、项目路径等）
            per_page: 每页返回数量，默认 20

        Returns:
            List[Dict]: 搜索结果列表，每个元素包含项目信息
        """
        url = f"{self.api_base_url}/projects"
        params = {
            "search": search_query,
            "per_page": per_page
        }

        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"搜索项目失败：{e.response.status_code} - {e.response.text}")
            return []

    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """
        根据项目 ID 精确查找项目信息

        Args:
            project_id: 项目 ID（可以是数字 ID 或 URL 编码的命名空间/项目路径）

        Returns:
            Optional[Dict]: 项目信息字典，未找到返回 None
        """
        from urllib.parse import quote
        encoded_id = quote(project_id, safe='')
        url = f"{self.api_base_url}/projects/{encoded_id}"

        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
               return None
            else:
                print(f"获取项目信息失败：{e.response.status_code} - {e.response.text}")
            return None

    def search_project_by_number(self, project_number: str) -> Optional[Dict]:
        """
        根据项目编号搜索项目（如传入 5500，则搜索包含 5500 的项目）

        Args:
            project_number: 项目编号（如 5500）

        Returns:
            Optional[Dict]: 匹配的项目信息，未找到返回 None
        """
        # 先尝试精确匹配项目路径
        result = self.get_project_by_id(project_number)
        if result:
            return result

        # 如果精确匹配失败，尝试搜索包含该编号的项目
        search_results = self.search_projects(search_query=project_number)

        if search_results:
            # 优先返回路径以该编号结尾的项目（如 ops/pipeline/api/game/5500）
            for project in search_results:
                path = project.get("path", "")
                path_with_namespace = project.get("path_with_namespace", "")
                if path == project_number or path_with_namespace.endswith(f"/{project_number}"):
                    return project
            # 如果没有精确匹配，返回第一个搜索结果
            return search_results[0]

        return None

    def get_project_git_url(self, project_info: Dict) -> Optional[str]:
        """
        从项目信息中提取 SSH Git URL

        Args:
            project_info: 项目信息字典

        Returns:
            Optional[str]: SSH Git URL，如 git@gitlab.fun1888.com:ops/pipeline/api/game.git
        """
        return project_info.get("ssh_url_to_repo")

    def get_project_http_url(self, project_info: Dict) -> str:
        """
        从项目信息中提取 HTTP Git URL

        Args:
            project_info: 项目信息字典

        Returns:
            str: HTTP Git URL
        """
        return project_info.get("http_url_to_repo", "")

    def get_project_path(self, project_info: Dict) -> str:
        """
        从项目信息中提取项目路径（命名空间/项目名）

        Args:
            project_info: 项目信息字典

        Returns:
            str: 项目路径，如 ops/pipeline/api/game
        """
        return project_info.get("path_with_namespace", "")

    def find_project_repo_url(self, project_identifier: str) -> Optional[Dict]:
        """
        根据项目标识符查找项目并返回仓库 URL 信息

        Args:
            project_identifier: 项目标识符（可以是数字 ID、项目路径、项目名称等）

        Returns:
            Optional[Dict]: 包含项目 URL 信息的字典，包含 ssh_url、http_url、path 等
        """
        project_info = self.search_project_by_number(project_identifier)

        if not project_info:
            return None

        return {
            "ssh_url": self.get_project_git_url(project_info),
            "http_url": self.get_project_http_url(project_info),
            "path": self.get_project_path(project_info),
            "web_url": project_info.get("web_url", ""),
            "id": project_info.get("id"),
            "name": project_info.get("name"),
            "full_info": project_info  # 保留完整信息
        }


if __name__ == "__main__":
    import os
    # 测试代码
    GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")
    GITLAB_URL = os.environ.get("GITLAB_URL", "https://gitlab.com")
    if not GITLAB_TOKEN:
        print("错误: 请设置环境变量 GITLAB_TOKEN")
        exit(1)

    # 创建搜索器实例
    searcher = GitLabProjectSearcher(
        gitlab_token=GITLAB_TOKEN,
        gitlab_url=GITLAB_URL
    )

    # 测试：根据项目 ID 搜索
    project_number = "9900"
    print(f"搜索项目：{project_number}")

    result = searcher.find_project_repo_url(project_number)

    if result:
        print(f"\n找到项目:")
        print(f"  项目名称：{result['name']}")
        print(f"  项目路径：{result['path']}")
        print(f"  SSH URL: {result['ssh_url']}")
        print(f"  HTTP URL: {result['http_url']}")
        print(f"  Web URL: {result['web_url']}")
    else:
        print(f"未找到项目：{project_number}")

    # 测试：搜索多个项目
    # print("\n--- 测试搜索 ops/pipeline/api/game ---")
    # result = searcher.find_project_repo_url("ops/pipeline/api/game")
    # if result:
    #     print(f"SSH URL: {result['ssh_url']}")
