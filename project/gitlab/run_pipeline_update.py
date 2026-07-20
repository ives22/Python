"""
GitLab Pipeline 自动化工具 - 入口脚本

功能：
1. 接收命令行参数（项目名称、分支名等）
2. 根据项目名称自动搜索 GitLab 仓库
3. 创建新分支并更新 pipeline 配置
"""
import argparse
import os
import sys
from pipeline_manager import GitLabPipelineManager
from project_searcher import GitLabProjectSearcher

# 配置：从环境变量读取
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")
GITLAB_URL = os.environ.get("GITLAB_URL", "https://gitlab.com")
if not GITLAB_TOKEN:
    print("错误: 请设置环境变量 GITLAB_TOKEN")
    sys.exit(1)


def build_jenkinsfile_content(project_name: str, git_repo_path: str) -> str:
    """
    生成 Jenkinsfile 内容

    Args:
        project_name: 项目名称（如 5500）
        git_repo_path: Git 仓库路径（用于生成 registryImage 等）

    Returns:
        str: Jenkinsfile 内容

    """

    return f"""@Library('global-share-library@main') _

apiGamePipelineByAgent {{
    gitLabRepo = "{git_repo_path}"
    gitlabDefaultBranch = "dev"

    registryAddr = "registry-intl.ap-southeast-1.aliyuncs.com"
    registryNamespace = "relax_many_game"
    registryImage = "{project_name}"

    resourceType = "statefulset"
    resourceName = "{project_name}"
    deployNamespace = "api-games"
    dockerfilePath = "./_build/Dockerfile"
    jenkinsAgentLabel = "agent01"
}}
"""


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="GitLab Pipeline 自动化工具 - 创建分支并更新 pipeline 配置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_pipeline_update.py -p 5500
  python run_pipeline_update.py -p 5500 -t ops/pipeline/api/game
  python run_pipeline_update.py -p 6600 -t ops/pipeline/api/game -m "发布 6600 版本"
        """
    )

    parser.add_argument(
        "-p", "--project",
        required=True,
        help="项目名称/编号（如 5500），将基于此搜索 GitLab 仓库"
    )

    parser.add_argument(
        "-t", "--target-project",
        default="ops/pipeline/api/game",
        # default="ops/test-project",
        help="目标项目路径（pipeline 所在项目），默认为 ops/pipeline/api/game"
    )

    parser.add_argument(
        "-m", "--message",
        default="Update Jenkinsfile",
        help="提交信息，默认为 'Update Jenkinsfile'"
    )

    parser.add_argument(
        "--base-branch",
        default="main",
        help="基础分支名称，默认为 main"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示将要执行的操作，不实际执行"
    )

    args = parser.parse_args()

    print(f"=" * 60)
    print(f"GitLab Pipeline 自动化工具")
    print(f"=" * 60)
    print(f"api项目名称：{args.project}")
    print(f"pipeline项目：{args.target_project}")
    print(f"pipeline分支：{args.project}")
    print(f"pipeline基础分支：{args.base_branch}")
    print(f"pipeline提交信息：{args.message}")
    print(f"=" * 60)

    if args.dry_run:
        print(f"[DRY RUN] 模式：仅显示操作，不实际执行")
        print(f"[DRY RUN] 将搜索项目：{args.project}")
        print(f"[DRY RUN] 将在项目 {args.target_project} 的分支 {args.project} 中更新 Jenkinsfile")
        return 0

    try:
        # 步骤 1：搜索项目，获取仓库信息
        print(f"\n[步骤 1/3] 正在搜索项目：{args.project} ...")
        searcher = GitLabProjectSearcher(
            gitlab_token=GITLAB_TOKEN,
            gitlab_url=GITLAB_URL
        )

        project_info = searcher.find_project_repo_url(args.project)
        if project_info is None:
            print(f"项目【{args.project} 】不存在，请检查项目是否正确")
            return 1
        else:
            project_ssh_rul = project_info["ssh_url"]
            print(project_ssh_rul)

            # 步骤 2: 生成 Jenkinsfile 内容
            print(f"\n[步骤 2/3] 正在生成 Jenkinsfile 内容...")
            # 这里的仓库地址为 pipeline 中需要替换的内容
            jenkinsfile_content = build_jenkinsfile_content(
                project_name=args.project,
                git_repo_path=project_ssh_rul
            )
            print(jenkinsfile_content)

            # 步骤 3: 创建pipeline项目分支，并更新pipeline
            print(f"\n[步骤 3/3] 正在创建分支并更新 pipeline...")
            manager = GitLabPipelineManager(
                gitlab_token=GITLAB_TOKEN,
                project_id=args.target_project,
                gitlab_url=GITLAB_URL
            )
            result = manager.create_branch_and_update(
                branch_name=args.project,
                base_branch=args.base_branch,
                jenkins_file_content=jenkinsfile_content,
                commit_message=args.message
            )

            if result.get("error"):
                print(f"\n执行失败： {result['error']}")
                return 1

            if result["branch_created"] and result["pipeline_updated"]:
                print(f"\n{'=' * 60}")
                print(f"添加多分支流水线，操作成功完成！")
                print(f"  - 新增项目: {args.project} --> {project_ssh_rul} ")
                print(f"  - 分支已创建：{args.target_project} --> {args.project}")
                if result.get("branch_info"):
                    print(f"  - 分支 Commit: {result['branch_info'].get('commit', {}).get('id', 'N/A')[:8]}")
                if result.get("commit_info"):
                    print(f"  - 提交 ID: {result['commit_info'].get('id', 'N/A')[:8]}")
                print(f"{'=' * 60}")
                return 0
            else:
                print(f"\n操作未完全成功，请检查日志")
                return 1
    except KeyboardInterrupt:
        print(f"\n\n用户中断操作")
        return 1
    except Exception as e:
        print(f"\n发生错误：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
