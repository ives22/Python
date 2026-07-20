"""
通过 Grafana API 创建数据源配置
支持: Prometheus, Elasticsearch (含 Basic 认证) 等类型
"""

import argparse
import os
import sys

import requests
import yaml


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_api_client(grafana_cfg: dict) -> tuple[str, str]:
    """返回 (base_url, api_key)"""
    url = grafana_cfg["url"].rstrip("/")
    api_key = grafana_cfg.get("api_key") or os.environ.get("GRAFANA_API_KEY", "")
    if not api_key:
        print("错误: 请在配置文件中设置 grafana.api_key 或设置环境变量 GRAFANA_API_KEY")
        sys.exit(1)
    return url, api_key


def build_datasource_payload(ds_cfg: dict) -> tuple[dict, dict, str]:
    """
    根据数据源类型构建 Grafana API 请求体
    返回 (json_data, secure_json_data, url_override) 三个值
    """
    ds_type = ds_cfg["type"]

    # 顶层字段，不放入 jsonData
    top_level_keys = {"name", "type", "access", "url", "database", "index",
                      "is_default", "editable",
                      "basic_auth", "basic_auth_user", "basic_auth_password",
                      # SLS 专用字段
                      "access_key_id", "access_key_secret", "logstore"}

    json_data = {}
    secure_json_data = {}
    url_override = ""

    # 基础认证
    if ds_cfg.pop("basic_auth", False):
        json_data["basicAuth"] = True
        if ds_cfg.get("basic_auth_user"):
            json_data["basicAuthUser"] = ds_cfg.pop("basic_auth_user")
        if ds_cfg.get("basic_auth_password"):
            secure_json_data["basicAuthPassword"] = ds_cfg.pop("basic_auth_password")

    # 阿里云 SLS 日志服务
    if ds_type in ("log-service-datasource", "aliyun-log-service-datasource"):
        endpoint = ds_cfg.pop("endpoint", "")
        json_data["endpoint"] = endpoint
        url_override = endpoint  # 插件后端从 settings.URL 读取 endpoint
        json_data["project"] = ds_cfg.pop("project", "")
        # 插件使用 logstore 字段 (非 default_logstore)
        if "default_logstore" in ds_cfg:
            json_data["logstore"] = ds_cfg.pop("default_logstore")
        if "logstore" in ds_cfg:
            json_data["logstore"] = ds_cfg.pop("logstore")
        if "region" in ds_cfg:
            json_data["region"] = ds_cfg.pop("region")
        if "role_arn" in ds_cfg:
            json_data["roleArn"] = ds_cfg.pop("role_arn")
        # SLS 插件的 AK 使用驼峰命名放在 secureJsonData 中
        if "access_key_id" in ds_cfg:
            secure_json_data["accessKeyId"] = ds_cfg.pop("access_key_id")
        if "access_key_secret" in ds_cfg:
            secure_json_data["accessKeySecret"] = ds_cfg.pop("access_key_secret")

    # Elasticsearch
    if ds_type == "elasticsearch":
        json_data["esVersion"] = ds_cfg.pop("es_version", "8.0.0")
        json_data["timeField"] = ds_cfg.pop("time_field", "@timestamp")
        # index 替代了废弃的 database 字段
        if "index" in ds_cfg:
            json_data["index"] = ds_cfg.pop("index")
        elif "database" in ds_cfg:
            # 兼容旧的 database 字段
            json_data["index"] = ds_cfg.pop("database")
        if "interval" in ds_cfg:
            json_data["timeInterval"] = ds_cfg.pop("interval")

    # 剩余未消耗的字段作为 jsonData 顶层键 (灵活扩展)
    for key, value in ds_cfg.items():
        if key not in top_level_keys:
            json_data[key] = value

    return json_data, secure_json_data, url_override


def datasource_exists(base_url: str, headers: dict, name: str) -> bool:
    resp = requests.get(
        f"{base_url}/api/datasources/name/{name}",
        headers=headers,
        timeout=10,
    )
    return resp.status_code == 200


def create_or_update_datasource(
    base_url: str, headers: dict, ds_cfg: dict, dry_run: bool = False
) -> None:
    name = ds_cfg["name"]
    json_data, secure_json_data, url_override = build_datasource_payload(ds_cfg.copy())

    ds_url = url_override if url_override else ds_cfg.get("url", "")

    body = {
        "name": name,
        "type": ds_cfg["type"],
        "access": ds_cfg.get("access", "proxy"),
        "url": ds_url,
        "isDefault": ds_cfg.get("is_default", False),
        "editable": ds_cfg.get("editable", True),
        "basicAuth": json_data.get("basicAuth", False),
        "basicAuthUser": json_data.get("basicAuthUser", ""),
        "jsonData": json_data,
    }
    if secure_json_data:
        body["secureJsonData"] = secure_json_data
        # 更新数据源时，必须同时设置 secureJsonFields 告知 Grafana 重置哪些 secure 字段
        body["secureJsonFields"] = {key: True for key in secure_json_data}

    if dry_run:
        print(f"[dry-run] 数据源 '{name}':")
        # 脱敏输出
        safe_body = {**body}
        if "secureJsonData" in safe_body:
            safe_body["secureJsonData"] = "***REDACTED***"
        print(yaml.dump(safe_body, allow_unicode=True, default_flow_style=False))
        return

    if datasource_exists(base_url, headers, name):
        # 非 admin 用户的 API key 可能无法 PUT 更新
        # 策略：先删除再创建（POST 和 DELETE 对非 admin 可用）
        resp = requests.delete(
            f"{base_url}/api/datasources/name/{name}",
            headers=headers,
            timeout=10,
        )
        if not resp.ok:
            print(f"失败: {name} — 删除已有数据源失败, HTTP {resp.status_code}: {resp.text}")
            sys.exit(1)
        print(f"已删除旧数据源: {name}")

    resp = requests.post(
        f"{base_url}/api/datasources",
        headers=headers,
        json=body,
        timeout=10,
    )
    action = "创建"

    if resp.ok:
        print(f"成功 {action} 数据源: {name}")
    else:
        print(f"失败: {name} — HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="通过 Grafana API 管理数据源")
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "-n", "--name", help="仅处理指定名称的数据源"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="仅打印配置，不实际执行"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    base_url, api_key = get_api_client(cfg["grafana"])
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    datasources = cfg.get("datasources", [])
    if not datasources:
        print("配置文件中未找到 datasources")
        return

    if args.name:
        datasources = [ds for ds in datasources if ds["name"] == args.name]
        if not datasources:
            print(f"未找到名称为 '{args.name}' 的数据源")
            return

    print(f"共 {len(datasources)} 个数据源待处理")
    for ds_cfg in datasources:
        create_or_update_datasource(base_url, headers, ds_cfg, args.dry_run)


if __name__ == "__main__":
    main()
