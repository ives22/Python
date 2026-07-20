#!/usr/bin/python3
"""
OpenVPN 硬件设备地址校验脚本（简化版）

功能：仅校验客户端的硬件设备地址是否在白名单中
- 白名单文件格式：一行一个硬件地址，前面的名字只作为备注（用于维护使用，不进行校验）
  例如：client1=550e8400-e29b-41d4-a716-446655440000

适用场景：只基于硬件设备地址控制访问权限
"""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

# 配置常量
HWADDR_WHITELIST_FILE = '/etc/openvpn/scripts/hwaddr_whitelist'
LOG_FILE = '/var/log/openvpn/hwaddr_check.log'


def setup_logging():
    """初始化日志处理器"""
    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )

    handler.namer = lambda name: name + ".gz"
    handler.compressor = lambda data: __import__('gzip').compress(data)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


def write_log(message: str):
    """统一日志写入"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(message + '\n')
    except Exception as err:
        print(str(err))
        pass


def load_hwaddr_whitelist(file_path: str, separators: list) -> set:
    """
    加载硬件地址白名单

    文件格式：一行一个硬件地址
    支持格式：
    - MAC 地址：client=00:11:22:33:44:55
    - UUID/Machine ID: client1=550e8400-e29b-41d4-a716-446655440000
    separators: 支持的分隔符列表，如：[':', '=', '|']

    返回：硬件地址集合（小写）
    """
    hwaddr_set = set()

    if not os.path.exists(file_path):
        logging.error(f"Whitelist file not found: {file_path}")
        return hwaddr_set

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                content = line.strip()
                # 跳过空行和注释
                if not content or content.startswith('#'):
                    continue

                for s in separators:
                    content = content.replace(s, '|')

                parts = content.split('|')
                if len(parts) >= 2:
                    hwaddr_set.add(parts[1].strip().lower())

                # 转为小写存入集合
                hwaddr_set.add(content.lower())
    except Exception as e:
        logging.error(f"Error reading {file_path}: {str(e)}")

    return hwaddr_set


def main():
    """主函数：执行硬件地址校验"""

    # 1. 预检查配置文件是否存在
    if not os.path.exists(HWADDR_WHITELIST_FILE):
        logging.critical(f"Critical: Whitelist file missing: {HWADDR_WHITELIST_FILE}")
        sys.exit(1)

    # 2. 从环境变量获取客户端硬件地址
    # IV_HWADDR: 客户端物理地址（Windows/macOS/Android/iOS）
    # UV_UUID: OpenVPN Connect v3 的设备 ID
    # Linux OpenVPN3 使用 Machine ID
    hw_addr = os.environ.get('IV_HWADDR', '').lower()
    fingerprint = os.environ.get('UV_UUID', '').lower()

    # 记录客户端信息（调试用）
    client_ip = os.environ.get('trusted_ip') or os.environ.get('untrusted_ip', 'Unknown')
    for k0, v0 in os.environ.items():
        logging.info(f"Debug [ClientSide] variables, key: {k0}, value: {v0}")

    # 3. 加载白名单
    allowed_hwaddr_set = load_hwaddr_whitelist(HWADDR_WHITELIST_FILE, ["="])

    if not allowed_hwaddr_set:
        logging.critical("Critical: Whitelist is empty.")
        sys.exit(1)

    # 4. 执行硬件地址校验
    # 只要客户端的硬件地址或设备 ID 在白名单中，就允许访问
    if hw_addr and hw_addr in allowed_hwaddr_set:
        logging.info(f"PASSED: HWADDR {hw_addr} from {client_ip}")
        sys.exit(0)
    elif fingerprint and fingerprint in allowed_hwaddr_set:
        logging.info(f"PASSED: UUID {fingerprint} from {client_ip}")
        sys.exit(0)

    # 5. 校验失败，拒绝访问
    logging.error(f"REJECTED: HWADDR={hw_addr}, UUID={fingerprint} from {client_ip}")
    sys.exit(1)


if __name__ == '__main__':
    setup_logging()
    main()
