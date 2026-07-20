"""
GitLab Pipeline 分支自动化脚本
功能：创建新分支并修改 Jenkinsfile pipeline 配置
"""
import requests
import base64
import json
from urllib.parse import quote
from typing import Optional
from project_searcher import GitLabProjectSearcher


class GitLabPipelineManager:
    def __init__(self, gitlab_token: str, project_id: str = None, gitlab_url: str = "https://gitlab.com"):
        """
        初始化 GitLab API 客户端

        Args:
            gitlab_token: GitLab Personal Access Token (需要 api 权限)
            project_id: 项目 ID、项目编号或 URL 编码的命名空间/项目名
            gitlab_url: GitLab 实例 URL，默认使用 gitlab.com
        """
        self.gitlab_url = gitlab_url.rstrip("/")
        self.token = gitlab_token
        self.headers = {
            "Content-Type": "application/json",
            "PRIVATE-TOKEN": self.token,
        }
        self.project_id = project_id
        self.encoded_project_id = quote(self.project_id, safe='')
        self.api_url = f"{self.gitlab_url}/api/v4/projects/{self.encoded_project_id}"

    def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> Optional[dict]:
        """发送 HTTP 请求并处理响应"""
        url = f"{self.api_url}/{endpoint}"
        response = requests.request(method=method, url=url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def create_branch(self, branch_name: str, base_branch: str = "main") -> Optional[dict]:
        """
        创建新分支

        Args:
             branch_name: 新分支名称
             base_branch: 源分支名称

         Returns:
             dict: 创建的分支信息
        """
        data = {
            "branch": branch_name,
            "ref": base_branch
        }
        return self._request("POST", "repository/branches", data)

    def get_file(self, file_path: str, ref: str = "main") -> Optional[dict]:
        """
        获取文件内容和元数据

        Args:
             file_path: 文件路径 (如：Jenkinsfile)
             ref: 分支名或 commit SHA

         Returns:
             dict: 包含 file_path, content, encoding, blob_id 等信息，失败返回 None
        """
        try:
            encoded_file_path = quote(file_path, safe='')
            params = {"ref": ref}
            url = f"{self.api_url}/repository/files/{encoded_file_path}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_file_content(self, file_path: str, ref: str = "main") -> Optional[str]:
        """
        获取文件解码后的内容

        Args:
            file_path: 文件路径
            ref: 分支名或 commit SHA

        Returns:
            str: 文件内容，失败返回 None
        """
        file_info = self.get_file(file_path, ref)
        if file_info:
            content_bytes = base64.b64decode(file_info["content"])
            return content_bytes.decode("utf-8")
        return None

    def update_pipeline(self, branch_name: str, jenkins_file_content: str,
                        file_path: str = "Jenkinsfile",
                        commit_message: str = "Update Jenkinsfile") -> Optional[dict]:
        """
        更新 pipeline 文件并提交

        Args:
            branch_name: 目标分支名称
            jenkins_file_content: 新的文件内容
            file_path: 文件路径，默认为Jenkinsfile
            commit_message: 提交信息

        Returns:
            dict: 提交信息
        """
        # 先检查文件是否存在
        file_info = self.get_file(file_path, ref=branch_name)

        data = {
            "branch": branch_name,
            "commit_message": commit_message,
            "actions": []
        }

        if file_info:
            # 更新现有文件
            data["actions"].append({
                "action": "update",
                "file_path": file_path,
                "content": jenkins_file_content
            })
        else:
            data["actions"].append({
                "action": "create",
                "file_path": file_path,
                "content": jenkins_file_content
            })

        return self._request("POST", "repository/commits", data)

    def create_branch_and_update(self, branch_name: str, jenkins_file_content: str,
                                 base_branch: str = "main",
                                 file_path: str = "Jenkinsfile",
                                 commit_message: str = "Update Jenkinsfile") -> Optional[dict]:
        """
        一键操作：创建分支并更新 pipeline

        Args:
            branch_name: 新分支名称
            jenkins_file_content: 新的 Jenkinsfile 内容
            base_branch: 源分支名称
            file_path: 文件路径
            commit_message: 提交信息

        Returns:
            dict: 包含分支和提交信息
        """
        result = {
            "branch_created": False,
            "pipeline_updated": False,
            "branch_info": None,
            "commit_info": None,
            "error": None
        }

        try:
            # 1. 创建分支
            print(f"正在创建分支: {branch_name} (基于 {base_branch})")
            branch_info = self.create_branch(branch_name, base_branch)
            result["branch_created"] = True
            result["branch_info"] = branch_info

            # 2. 更新 pipeline
            commit_info = self.update_pipeline(
                branch_name=branch_name,
                jenkins_file_content=jenkins_file_content,
                file_path=file_path,
                commit_message=commit_message
            )
            result["pipeline_updated"] = True
            result["commit_info"] = commit_info

        except requests.exceptions.HTTPError as e:
            result["error"] = f"API 请求失败: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            result["error"] = str(e)

        return result

    def create_merge_request(self, source_branch: str, target_branch: str,
                             title: str = None, description: str = None,
                             remove_source_branch: bool = True) -> Optional[dict]:
        """
        创建合并请求 (Merge Request)

        Args:
            source_branch: 源分支
            target_branch: 目标分支
            title: MR 标题
            description: MR 描述
            remove_source_branch: 合并后是否删除源分支

        Returns:
            dict: MR 信息
        """
        if title is None:
            title = f"Merge {source_branch} into {target_branch}"

        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
            "remove_source_branch": remove_source_branch
        }

        return self._request("POST", "merge_requests", data)

    def get_branch(self, branch_name: str) -> Optional[dict]:
        """
        获取分支

        Args:
            branch_name: 要获取的分支名称

        Returns:
            dict: 分支信息
        """
        try:
            encoded_branch = quote(branch_name, safe='/')
            return self._request("GET", f"repository/branches/{encoded_branch}")
        except requests.exceptions.HTTPError as e:
            print(f"获取分支失败: {e}")
            return None

    def delete_branch(self, branch_name: str) -> Optional[bool]:
        """
        删除分支

        Args:
            branch_name: 要删除的分支名称

        Returns:
            bool: 是否成功删除
        """
        try:
            encoded_branch = quote(branch_name, safe='/')
            self._request("DELETE", f"repository/branches/{encoded_branch}")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"删除分支失败：{e}")
            return False

    def list_branch(self) -> Optional[list]:
        """
        列出所有分支

        Returns:
            list: 分支列表
        """
        return self._request("GET", "repository/branches")

    def get_project_info(self) -> dict:
        """
        获取项目信息（用于调试连接）

        Returns:
            dict: 项目信息
        """
        print(self.api_url)
        print(self.project_id)
        print(self.encoded_project_id)
        return self._request("GET", "")

    def verify_connection(self) -> bool:
        """
        验证 API 连接是否正常

        Returns:
            bool: 连接是否成功
        """
        try:
            project_info = self.get_project_info()
            print(f"连接成功！")
            print(f"  项目名称：{project_info.get('name', 'N/A')}")
            print(f"  项目路径：{project_info.get('path_with_namespace', 'N/A')}")
            print(f"  API URL: {self.api_url}")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"连接失败！")
            print(f"  状态码：{e.response.status_code}")
            print(f"  响应：{e.response.text}")
            print(f"  API URL: {self.api_url}")
            print(f"  编码后的 project_id: {self.encoded_project_id}")
            return False


if __name__ == "__main__":
    import os
    # 配置：从环境变量读取
    GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")
    GITLAB_URL = os.environ.get("GITLAB_URL", "https://gitlab.com")
    if not GITLAB_TOKEN:
        print("错误: 请设置环境变量 GITLAB_TOKEN")
        exit(1)

    # ==========================================
    # 方式一：传统方式 - 直接传入项目路径
    # ==========================================
    # PROJECT_ID = "ops/pipeline/api/game"
    PROJECT_ID = "ops/test-project"

    # 初始化管理器
    manager = GitLabPipelineManager(
        gitlab_token=GITLAB_TOKEN,
        project_id=PROJECT_ID,
        gitlab_url=GITLAB_URL
    )

    # ==========================================
    # 方式二：自动搜索方式 - 传入项目编号，自动搜索项目
    # ==========================================
    # PROJECT_NUMBER = "5500"  # 传入项目编号
    # manager = GitLabPipelineManager(
    #     gitlab_token=GITLAB_TOKEN,
    #     project_id=PROJECT_NUMBER,
    #     gitlab_url=GITLAB_URL,
    #     search_project=True  # 启用自动搜索
    # )


    # 新的 Jenkinsfile 内容
    new_jenkinsfile = """
@Library('global-share-library@main') _

apiGamePipelineByAgent {
    gitLabRepo = "git@gitlab.fun1888.com:server/api/game/multi/2000.git"
    gitlabDefaultBranch = "dev"

    registryAddr = "registry-intl.ap-southeast-1.aliyuncs.com"
    registryNamespace = "relax_many_game"  // 不传默认值为：relax_many_game
    registryImage = "2000"

    resourceType = "statefulset"    // 不传默认值为：statefulset
    resourceName = "2000" 
    deployNamespace = "api-games"   // 不传默认值为：api-games
    dockerfilePath = "./_build/Dockerfile" // 不传默认值为：./_build/Dockerfile 
    jenkinsAgentLabel = "agent01"  // 指定用agent01节点构建
}
"""

    # 一键创建分支并更新 pipeline
    result = manager.create_branch_and_update(
        branch_name="2000",
        base_branch="main",
        jenkins_file_content=new_jenkinsfile,
        file_path="Jenkinsfile",
        commit_message="新增子游戏2000"
    )
    if result["pipeline_updated"]:
        print("操作成功完成!")


    # # 获取分支
    # result = manager.get_branch(
    #     branch_name="5139", )
    # print(result)
    #
    # # 获取游戏分支
    # result = manager.list_branch()
    # print(result)
