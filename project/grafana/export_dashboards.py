"""
通过 Grafana API 导出 Dashboard 到本地 JSON 文件
"""

import argparse
import json
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


def list_dashboards(base_url: str, headers: dict) -> list[dict]:
    """获取所有 Dashboard 列表"""
    resp = requests.get(
        f"{base_url}/api/search?type=dash-db",
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        print(f"获取 Dashboard 列表失败: HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)
    return resp.json()


def list_folders(base_url: str, headers: dict) -> dict[int, str]:
    """获取所有文件夹，返回 {folder_id: folder_title} 映射"""
    resp = requests.get(
        f"{base_url}/api/search?type=dash-folder",
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        print(f"警告: 获取文件夹列表失败: HTTP {resp.status_code}")
        return {}
    return {f["id"]: f["title"] for f in resp.json()}


def _safe_filename(name: str) -> str:
    """将字符串转换为安全的文件名"""
    return "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name).strip()


def export_dashboard(
    base_url: str,
    headers: dict,
    dashboard_uid: str,
    output_dir: str,
    folder_name: str = "",
) -> str:
    """导出单个 Dashboard 到本地 JSON 文件，返回相对路径"""
    resp = requests.get(
        f"{base_url}/api/dashboards/uid/{dashboard_uid}",
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        print(f"  失败: HTTP {resp.status_code}: {resp.text}")
        return ""

    data = resp.json()
    dashboard = data["dashboard"]

    # 移除 Grafana 自动生成的元数据，导入时不需要
    dashboard.pop("id", None)
    dashboard.pop("uid", None)
    dashboard.pop("version", None)

    # 写入文件夹元数据，方便后续按目录结构还原
    if folder_name:
        dashboard["_folder"] = folder_name

    # 使用 dashboard title 作为文件名
    title = dashboard.get("title", dashboard_uid)
    safe_title = _safe_filename(title)
    filename = f"{safe_title}.json"

    # 按文件夹创建子目录
    if folder_name:
        target_dir = os.path.join(output_dir, _safe_filename(folder_name))
    else:
        target_dir = output_dir
    os.makedirs(target_dir, exist_ok=True)

    filepath = os.path.join(target_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)

    return os.path.relpath(filepath, output_dir)


def main():
    parser = argparse.ArgumentParser(description="通过 Grafana API 导出 Dashboard 到本地")
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "-o", "--output", default="./dashboards", help="导出目录 (默认: ./dashboards)"
    )
    parser.add_argument(
        "--uid", help="仅导出指定 UID 的 Dashboard"
    )
    parser.add_argument(
        "--title", help="仅导出指定标题的 Dashboard（模糊匹配）"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    base_url, api_key = get_api_client(cfg["grafana"])
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)

    if args.uid:
        # 导出指定 UID 的 Dashboard
        filename = export_dashboard(base_url, headers, args.uid, args.output)
        if filename:
            print(f"已导出: {filename}")
        return

    # 获取所有文件夹和 Dashboard 列表
    folders = list_folders(base_url, headers)
    dashboards = list_dashboards(base_url, headers)
    if not dashboards:
        print("未找到任何 Dashboard")
        return

    # 按标题过滤
    if args.title:
        dashboards = [d for d in dashboards if args.title.lower() in d.get("title", "").lower()]
        if not dashboards:
            print(f"未找到标题包含 '{args.title}' 的 Dashboard")
            return

    # 按文件夹分组展示
    by_folder: dict[str, list] = {}
    for dash in dashboards:
        folder_id = dash.get("folderId", 0)
        folder_name = folders.get(folder_id, "")
        by_folder.setdefault(folder_name, []).append(dash)

    print(f"共 {len(dashboards)} 个 Dashboard，{len(folders)} 个文件夹")
    for folder_name, dashes in by_folder.items():
        label = folder_name or "(无文件夹)"
        print(f"  [{label}] {len(dashes)} 个")

    print()
    for folder_name, dashes in by_folder.items():
        label = folder_name or "(无文件夹)"
        print(f"[{label}]")
        for dash in dashes:
            uid = dash["uid"]
            title = dash.get("title", uid)
            print(f"  导出: {title} (uid: {uid})", end=" ... ")
            rel_path = export_dashboard(base_url, headers, uid, args.output, folder_name)
            if rel_path:
                print(rel_path)
            else:
                print("失败")
        print()


if __name__ == "__main__":
    main()
