# OpenVPN Access Server MAC/UUID post_auth script.
# Version: 2.1
# Contributions by:
# Johan Draaisma
# Brandon Giron
#
# This script can be used with LOCAL, PAM, LDAP, RADIUS and SAML authentication.
# It adds an additional check when authentication is done through the VPN connection.
# It applies to all 3 connection profiles types (server-locked, user-locked, auto-login).
#
# Windows, macOS, Android, and iOS will be reporting MAC addresses and UUID (Device ID from
# OpenVPN Connect v3)
# Linux running OpenVPN2 will be reporting MAC addresses
# Linux running OpenVPN3 will be reporting Machine ID
#
#
# Full documentation and explanation can be found here:
# https://openvpn.net/as-docs/tutorials/tutorial--hardware-address-post-auth.html
#
# Script last updated in July 2025
#!/usr/bin/python3
import ipaddress
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import re
import sys
from typing import Dict

# 配置常量
MAC_WHITELIST_FILE = '/etc/openvpn/scripts/macaddr'
ACCESS_WHITELIST_FILE = '/etc/openvpn/scripts/access'
LOG_FILE = '/var/log/openvpn/hw_auth.log'

reference_var = {
    'IV_HWADDR': '客户端物理地址',
    'IV_GUI_VER': '客户端GUI版本',
    'IV_SSL': '客户端SSL版本',
    'IV_CIPHERS': '客户端cipherSuite',
    'ifconfig_pool_netmask': '掩码地址',
    'ifconfig_pool_remote_ip': '客户端地址',
    'trusted_port': '客户端连接端口',
    'trusted_ip': '客户端公网地址',
    'untrusted_ip': '客户端公网地址',
    'common_name': '客户端证书名称',
    'username': '认证用户名'
}

def setup_logging():
    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",       # Day
        interval=1,     # 间隔1天
        backupCount=30, # 保留30个文件
        encoding='utf-8'
    )

    handler.namer = lambda name: name + ".gz"
    handler.compressor = lambda data: __import__('gzip').compress(data)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
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

class IpWhiteList:
    def __init__(self, access: str, seprator: list):
        self.networks = []
        self.allow_all = False
        self._load(access, seprator)

    def _load(self, file_path, separators):
        raw_data = load_simple_kv(file_path, separators)
        if not raw_data:
            raw_data = {'0.0.0.0': 'allow_all'}
        for key in raw_data.keys():
            if key == '0.0.0.0':
                self.allow_all = True
                return
            try:
                # 支持 1.2.3.4 或 1.2.3.0/24
                self.networks.append(ipaddress.ip_network(key, strict=False))
            except ValueError:
                logging.error(f"Invalid IP/Network format: {key}")

    def contain(self, ipaddr: str) -> bool:
        if self.allow_all:
            return True
        if not ipaddr:
            return False
        try:
            addr = ipaddress.ip_address(ipaddr)
            return any(addr in net for net in self.networks)
        except ValueError:
            return False

def load_simple_kv(file_path: str, separators: list) -> Dict[str, str]:
    """
    通用加载配置函数
    separators: 支持的分隔符列表，如 [':', '=', '|']
    """
    kv_dict = {}
    if not os.path.exists(file_path):
        return kv_dict

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                content = line.strip()
                if not content or content.startswith('#'):
                    continue

                for s in separators:
                    content = content.replace(s, '|')

                parts = content.split('|')
                if len(parts) >= 2:
                    # key: parts[0], value: parts[1]
                    kv_dict[parts[0].strip().lower()] = parts[1].strip().lower()
                elif len(parts) == 1:
                    # only key exist.
                    kv_dict[parts[0].strip()] = 'placeholder'
    except Exception as e:
        logging.error(f"Error reading {file_path}: {str(e)}")

    return kv_dict

def main():
    # 1. 预检查配置文件
    if not os.path.exists(MAC_WHITELIST_FILE) or not os.path.exists(ACCESS_WHITELIST_FILE):
        logging.critical("Critical: Whitelist files missing.")
        sys.exit(1)

    # 2. 从环境变量获取客户端信息 (统一入口)
    # 注意：使用 opt-verify 后，IV_HWADDR 才会出现在 os.environ
    client_data = {
        'common_name': os.environ.get('common_name'),
        'username': os.environ.get('username'),
        'access_ip': os.environ.get('trusted_ip') or os.environ.get('untrusted_ip'),
        'hw_addr': os.environ.get('IV_HWADDR'),
        'fingerprint': os.environ.get('UV_UUID'),
        'assigned_ip': os.environ.get('ifconfig_pool_remote_ip'),
        'gui_ver': os.environ.get('IV_GUI_VER', 'Unknown'),
        'cn': os.environ.get('X509_0_CN')
    }

    for k0, v0 in os.environ.items():
        logging.info(f"Debug [ClientSide] variables, key: {k0}, value: {v0}")

    # 3. 加载白名单
    allowed_device = load_simple_kv(MAC_WHITELIST_FILE, ['='])
    allowed_access = IpWhiteList(ACCESS_WHITELIST_FILE, ['=', '|'])

    # 校验 A: 来源 IP 是否在允许范围内
    if not allowed_access.contain(client_data['access_ip']):
        logging.error(f"Rejected [IP]: {client_data['access_ip']} User: {client_data['username']}")
        sys.exit(1)

    # 校验 B: 证书名与登录名一致性校验 (安全增强)
    if client_data['username'] and client_data['cn']:
        u_name = client_data['username'].partition('@')[0].lower()
        c_name = client_data['cn'].partition('@')[0].lower()
        if u_name != c_name:
            logging.error(f"Rejected [Mismatch]: User({u_name}) != Cert({c_name})")
            sys.exit(1)

    # 校验 C: MAC 地址绑定校验
    user_key = client_data['username'] or client_data['cn']

    user_key = user_key.partition('@')[0]

    if user_key in allowed_device:
        target_mac = allowed_device[user_key]

        current_mac = client_data['hw_addr'].lower()

        current_fingerprint = client_data['fingerprint'].lower()

        allowed_mac_set = {m.strip().lower() for m in re.split(r'[;,]', target_mac) if m.strip()}

        if current_mac in allowed_mac_set:
            logging.info(
                f"Passed: User {user_key} MAC {current_mac} from {client_data['access_ip']}, assigned: {client_data['assigned_ip']}")
            sys.exit(0)
        elif current_fingerprint in allowed_mac_set:
            logging.info(
                f"Passed: User {user_key} Fingerprint {current_fingerprint} from {client_data['access_ip']}, assigned: {client_data['assigned_ip']}")
            sys.exit(0)
        else:
            logging.error(f"Rejected [MAC|Fingerprint]: User {user_key} expected {target_mac}, got {current_mac}")
            sys.exit(1)
    else:
        # 用户不在白名单中，默认拒绝
        logging.error(f"Rejected [Unknown User]: {user_key} not in whitelist")
        sys.exit(1)

if __name__ == '__main__':
    setup_logging()
    main()