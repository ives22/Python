import argparse

import jenkins
import xml.etree.ElementTree as ET
import logging
import os
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JenkinsGameJobUpdater:
    """Jenkins 游戏 Job 配置更新器"""

    def __init__(
            self,
            server_url: Optional[str] = None,
            user: Optional[str] = None,
            token: Optional[str] = None,
            job_path: Optional[str] = None
    ):
        """
        初始化更新器

        Args:
            server_url: Jenkins 服务器地址
            user: 用户名
            token: API Token
            job_path: Job 完整路径
        """
        # 优先使用传入参数，否则从环境变量读取
        self.server_url = server_url or os.getenv("JENKINS_URL")
        self.user = user or os.getenv("JENKINS_USER")
        self.token = token or os.getenv("JENKINS_TOKEN")
        self.job_path = job_path or os.getenv("JENKINS_JOB_PATH", "server/api/game")
        if not self.server_url or not self.user or not self.token:
            raise ValueError("请设置环境变量 JENKINS_URL、JENKINS_USER 和 JENKINS_TOKEN")
        self.server = None

    def connect(self) -> bool:
        """连接到 Jenkins 服务器"""
        try:
            self.server = jenkins.Jenkins(self.server_url, self.user, self.token)
            logger.info(f"成功连接到 Jenkins: {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"连接 Jenkins 失败：{e}")
            return False

    def validate_game_id(self, game_id: str) -> bool:
        """验证游戏 ID 是否为有效的数字"""
        try:
            int(game_id)
            return True
        except (ValueError, TypeError):
            logger.error(f"无效的游戏 ID: {game_id}")
            return False

    def parse_existing_games(self, regex_str: str) -> set:
        """从正则表达式字符串中解析已有的游戏 ID 集合"""
        if not regex_str:
            return set()
        game_ids = set()
        # 分割正则表达式，提取游戏 ID
        for pattern in regex_str.split('|'):
            pattern = pattern.strip()
            if pattern.startswith('^') and pattern.endswith('$'):
                game_id = pattern[1:-1]
                game_ids.add(game_id)
        return game_ids

    def update_game_job(self, game_id: str) -> bool:
        """
        更新单个游戏 Job 配置

        Args:
            game_id: 游戏 ID

        Returns:
            bool: 更新是否成功
        """
        if not self.validate_game_id(game_id):
            return False

        if self.server is None and not self.connect():
            return False

        try:
            config_xml = self.server.get_job_config(self.job_path)
            root = ET.fromstring(config_xml)

            xpath_query = ".//jenkins.scm.impl.trait.RegexSCMHeadFilterTrait/regex"
            regex_node = root.find(xpath_query)

            if regex_node is None:
                logger.error("未能在 XML 中找到 RegexSCMHeadFilterTrait 节点，请检查路径。")
                return False

            old_regex = regex_node.text or ""
            existing_games = self.parse_existing_games(old_regex)

            if game_id in existing_games:
                logger.info(f"游戏 ID {game_id} 已存在于正则中，无需更新")
                return True

            # 添加新的游戏 ID
            new_pattern = f"^{game_id}$"
            new_regex = f"{old_regex}|{new_pattern}" if old_regex else new_pattern
            regex_node.text = new_regex

            logger.info(f"检测到旧正则：{old_regex}")
            logger.info(f"准备更新为：{new_regex}")

            updated_xml = ET.tostring(root, encoding='unicode')
            self.server.reconfig_job(self.job_path, updated_xml)
            logger.info(f"游戏 ID {game_id} 添加成功！")
            return True

        except Exception as e:
            logger.error(f"更新 Job 配置失败：{e}")
            return False

    def update_batch(self, game_ids: list) -> dict:
        """
        批量更新游戏 Job 配置

        Args:
            game_ids: 游戏 ID 列表

        Returns:
            dict: 包含成功和失败统计的结果
        """
        results = {"success": [], "failed": [], "skipped": []}

        if self.server is None and not self.connect():
            return results

        for game_id in game_ids:
            game_id = str(game_id).strip()
            if not game_id:
                continue

            if not self.validate_game_id(game_id):
                results["failed"].append(game_id)
                continue

            if self.server is None and not self.connect():
                results["failed"].append(game_id)
                continue

            try:
                config_xml = self.server.get_job_config(self.job_path)
                root = ET.fromstring(config_xml)

                xpath_query = ".//jenkins.scm.impl.trait.RegexSCMHeadFilterTrait/regex"
                regex_node = root.find(xpath_query)

                if regex_node is None:
                    logger.error("未能在 XML 中找到 RegexSCMHeadFilterTrait 节点")
                    results["failed"].append(game_id)
                    continue

                old_regex = regex_node.text or ""
                existing_games = self.parse_existing_games(old_regex)

                if game_id in existing_games:
                    logger.info(f"游戏 ID {game_id} 已存在，跳过")
                    results["skipped"].append(game_id)
                    continue

                # 添加新的游戏 ID
                new_pattern = f"^{game_id}$"
                new_regex = f"{old_regex}|{new_pattern}" if old_regex else new_pattern
                regex_node.text = new_regex

                updated_xml = ET.tostring(root, encoding='unicode')
                self.server.reconfig_job(self.job_path, updated_xml)
                logger.info(f"游戏 ID {game_id} 添加成功！")
                results["success"].append(game_id)

            except Exception as e:
                logger.error(f"更新游戏 ID {game_id} 失败：{e}")
                results["failed"].append(game_id)

        logger.info(
            f"批量更新完成 - 成功：{len(results['success'])}, "
            f"跳过：{len(results['skipped'])}, 失败：{len(results['failed'])}"
        )
        return results

    def close(self):
        """关闭连接（清理资源）"""
        self.server = None
        logger.info("已关闭 Jenkins 连接")




def test():
    # 创建更新器实例
    updater = JenkinsGameJobUpdater()

    # 单个更新
    # updater.update_game_job("9900")
    updater.update_game_job("2000")

    # 批量更新示例
    game_list = ["2001", "2002", "2003"]
    results = updater.update_batch(game_list)
    print(f"结果：{results}")

    updater.close()

def main():
    # 解析命令参数
    parser = argparse.ArgumentParser(
        description="Jenkins 多分支Job 自动化工具 - 正对 api-games模块 修改配置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    示例:
      python 02_api_games_job.py -g 5500
      python run_pipeline_update.py -p 5500 -t ops/pipeline/api/game
      python run_pipeline_update.py -p 6600 -t ops/pipeline/api/game -m "发布 6600 版本"
            """
    )

    parser.add_argument(
        "-g",
        "--game",
        required=True,
        help="游戏编号（如 5117）即分支名字，将基于此添加到Job的正则匹配列表"
    )

    args = parser.parse_args()


    # 创建更新器实例
    updater = JenkinsGameJobUpdater()
    updater.update_game_job(args.game)

    updater.close()

# 使用示例
if __name__ == "__main__":
    main()

