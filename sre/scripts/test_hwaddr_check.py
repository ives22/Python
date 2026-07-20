#!/usr/bin/env python3
"""
OpenVPN 硬件地址校验脚本 - 测试驱动
用于模拟 OpenVPN 环境变量，测试 post_auth 脚本的各种场景

用法:
    python test_hwaddr_check.py           # 运行所有测试
    python test_hwaddr_check.py pass_mac  # 运行指定测试
"""

import os
import sys
import subprocess
import tempfile
import shutil

# 测试场景配置
TEST_CASES = {
    'pass_mac': {
        'desc': 'MAC 地址匹配 - 应通过',
        'env': {
            'username': 'testuser',
            'trusted_ip': '192.168.1.100',
            'IV_HWADDR': 'aa:bb:cc:dd:ee:ff',
        },
        'expected': 0,
    },
    'pass_fingerprint': {
        'desc': '设备指纹匹配 - 应通过',
        'env': {
            'username': 'user2',
            'trusted_ip': '10.0.0.50',
            'IV_HWADDR': 'IV_UUID:550e8400-e29b-41d4-a716-446655440000',
        },
        'expected': 0,
    },
    'pass_multiple_mac': {
        'desc': '多 MAC 绑定 (分号分隔) - 应通过',
        'env': {
            'username': 'user3',
            'trusted_ip': '192.168.1.105',
            'IV_HWADDR': '11:22:33:44:55:66',
        },
        'expected': 0,
    },
    'reject_ip': {
        'desc': 'IP 不在白名单 - 应拒绝',
        'env': {
            'username': 'testuser',
            'trusted_ip': '8.8.8.8',
            'IV_HWADDR': 'aa:bb:cc:dd:ee:ff',
        },
        'expected': 1,
    },
    'reject_mac': {
        'desc': 'MAC 地址不匹配 - 应拒绝',
        'env': {
            'username': 'testuser',
            'trusted_ip': '192.168.1.100',
            'IV_HWADDR': '00:11:22:33:44:55',
        },
        'expected': 1,
    },
    'reject_user_mismatch': {
        'desc': '用户名与证书 CN 不匹配 - 应拒绝',
        'env': {
            'username': 'alice',
            'cn': 'bob',
            'trusted_ip': '192.168.1.100',
            'IV_HWADDR': 'aa:bb:cc:dd:ee:ff',
        },
        'expected': 1,
    },
    'reject_unknown_user': {
        'desc': '用户不在白名单 - 应拒绝',
        'env': {
            'username': 'unknown_user',
            'trusted_ip': '192.168.1.100',
            'IV_HWADDR': 'aa:bb:cc:dd:ee:ff',
        },
        'expected': 1,
    },
    'pass_allow_all_ip': {
        'desc': 'IP 白名单 0.0.0.0 全允许 - 应通过',
        'env': {
            'username': 'testuser',
            'trusted_ip': '203.0.113.50',
            'IV_HWADDR': 'aa:bb:cc:dd:ee:ff',
        },
        'access_content': '0.0.0.0\n',
        'expected': 0,
    },
    'pass_cidr_range': {
        'desc': 'IP 在 CIDR 范围内 - 应通过',
        'env': {
            'username': 'testuser',
            'trusted_ip': '172.16.5.100',
            'IV_HWADDR': 'aa:bb:cc:dd:ee:ff',
        },
        'expected': 0,
    },
    'reject_outside_cidr': {
        'desc': 'IP 超出 CIDR 范围 - 应拒绝',
        'env': {
            'username': 'testuser',
            'trusted_ip': '172.17.0.1',
            'IV_HWADDR': 'aa:bb:cc:dd:ee:ff',
        },
        'expected': 1,
    },
}

# 默认配置文件内容
DEFAULT_MAC_WHITELIST = """# OpenVPN MAC 地址白名单配置文件
# 格式：用户名=MAC 地址 (支持多个 MAC，用;或，分隔)
testuser=aa:bb:cc:dd:ee:ff
user2=550e8400-e29b-41d4-a716-446655440000
user3=11:22:33:44:55:66;66:55:44:33:22:11
alice=aa:bb:cc:dd:ee:ff
"""

DEFAULT_ACCESS_WHITELIST = """# OpenVPN 访问 IP 白名单配置文件
# 格式：IP 或 CIDR=allow (或仅写 IP/CIDR)
192.168.1.0/24=allow
10.0.0.0/8=allow
172.16.0.0/12=allow
"""


class TestRunner:
    def __init__(self):
        self.test_dir = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.target_script = os.path.join(self.script_dir, 'openvpn_hwaddr_check.py')
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def setup(self):
        """创建临时测试环境"""
        self.test_dir = tempfile.mkdtemp(prefix='openvpn_test_')

        # 创建 MAC 白名单文件
        mac_file = os.path.join(self.test_dir, 'macaddr')
        with open(mac_file, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_MAC_WHITELIST)

        # 创建 IP 访问白名单文件
        access_file = os.path.join(self.test_dir, 'access')
        with open(access_file, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_ACCESS_WHITELIST)

        # 创建日志目录
        log_dir = os.path.join(self.test_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        print(f"测试目录：{self.test_dir}")
        print(f"MAC 白名单：{mac_file}")
        print(f"IP 白名单：{access_file}")
        print()

        return mac_file, access_file, log_dir

    def cleanup(self):
        """清理临时测试环境"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print(f"\n已清理测试目录：{self.test_dir}")

    def modify_script_paths(self, mac_file, access_file, log_dir):
        """创建修改后的测试脚本副本"""
        test_script = os.path.join(self.test_dir, 'openvpn_hwaddr_check_test.py')

        with open(self.target_script, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换配置路径
        content = content.replace(
            "MAC_WHITELIST_FILE = '/etc/openvpn/scripts/macaddr'",
            f"MAC_WHITELIST_FILE = '{mac_file}'"
        )
        content = content.replace(
            "ACCESS_WHITELIST_FILE = '/etc/openvpn/scripts/access'",
            f"ACCESS_WHITELIST_FILE = '{access_file}'"
        )
        content = content.replace(
            "LOG_FILE = '/var/log/openvpn/hw_auth.log'",
            f"LOG_FILE = '{os.path.join(log_dir, 'hw_auth.log')}'"
        )

        with open(test_script, 'w', encoding='utf-8') as f:
            f.write(content)

        return test_script

    def run_test(self, case_name, case_config, test_script, log_dir, mac_file, access_file):
        """运行单个测试用例"""
        print(f"\n{'='*60}")
        print(f"测试：{case_config['desc']}")
        print(f"{'='*60}")

        # 准备模拟环境 - 创建最小化环境
        env = {
            'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
            'PYTHONPATH': self.test_dir,
        }

        # 注入测试环境变量
        for k, v in case_config['env'].items():
            env[k] = v

        # 如果有自定义 access 文件内容，覆盖默认文件
        if 'access_content' in case_config:
            with open(access_file, 'w', encoding='utf-8') as f:
                f.write(case_config['access_content'])
        else:
            # 恢复默认 access 文件
            with open(access_file, 'w', encoding='utf-8') as f:
                f.write(DEFAULT_ACCESS_WHITELIST)

        # 清空日志文件
        log_file = os.path.join(log_dir, 'hw_auth.log')
        if os.path.exists(log_file):
            open(log_file, 'w').close()

        # 执行测试
        result = subprocess.run(
            ['python3', test_script],
            env=env,
            capture_output=True,
            text=True,
            cwd=self.test_dir
        )

        # 验证结果
        passed = result.returncode == case_config['expected']
        status = '✓' if passed else '✗'

        print(f"预期退出码：{case_config['expected']}")
        print(f"实际退出码：{result.returncode}")
        print(f"测试结果：{status} {'通过' if passed else '失败'}")

        # 显示错误输出（如果有）
        if result.returncode != case_config['expected']:
            if result.stderr:
                # 只显示关键错误信息
                error_lines = [l for l in result.stderr.split('\n') if 'Error' in l or 'Rejected' in l or 'Critical' in l or 'AttributeError' in l]
                if error_lines:
                    print(f"错误信息：{error_lines[0]}")
                else:
                    print(f"错误输出：{result.stderr[:100]}")

        # 读取日志文件内容
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read().strip()
                if log_content:
                    # 只显示最后一行相关日志
                    log_lines = log_content.split('\n')
                    relevant = [l for l in log_lines if 'Passed' in l or 'Rejected' in l or 'Critical' in l or 'Error' in l]
                    if relevant:
                        print(f"关键日志：{relevant[-1]}")

        return passed

    def run_all(self, filter_name=None):
        """运行所有或指定的测试用例"""
        mac_file, access_file, log_dir = self.setup()
        test_script = self.modify_script_paths(mac_file, access_file, log_dir)

        print(f"\n开始执行测试...\n")

        for name, config in TEST_CASES.items():
            if filter_name and name != filter_name:
                continue

            try:
                if self.run_test(name, config, test_script, log_dir, mac_file, access_file):
                    self.passed += 1
                else:
                    self.failed += 1
            except Exception as e:
                print(f"测试异常：{e}")
                self.failed += 1
                self.skipped += 1

        # 汇总结果
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"测试汇总")
        print(f"{'='*60}")
        print(f"总计：{total} 个测试")
        print(f"通过：{self.passed} ✓")
        print(f"失败：{self.failed} ✗")

        if self.failed == 0:
            print("\n所有测试通过!")
            return 0
        else:
            print(f"\n有 {self.failed} 个测试失败，请检查!")
            return 1


def main():
    filter_name = sys.argv[1] if len(sys.argv) > 1 else None

    runner = TestRunner()

    try:
        exit_code = runner.run_all(filter_name)
        sys.exit(exit_code)
    finally:
        runner.cleanup()


if __name__ == '__main__':
    main()
