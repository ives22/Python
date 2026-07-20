"""
通过 Grafana API 从本地 JSON 文件导入 Dashboard
"""

import argparse
import glob
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


def get_or_create_folder(base_url: str, headers: dict, folder_name: str) -> int:
    """查找或创建文件夹，返回 folder_id"""
    # 先查找已有的文件夹
    resp = requests.get(
        f"{base_url}/api/search?type=dash-folder",
        headers=headers,
        timeout=10,
    )
    if resp.ok:
        for f in resp.json():
            if f["title"] == folder_name:
                return f["id"]

    # 不存在则创建
    resp = requests.post(
        f"{base_url}/api/folders",
        headers=headers,
        json={"title": folder_name},
        timeout=10,
    )
    if resp.ok:
        folder_id = resp.json()["id"]
        print(f"  已创建文件夹: {folder_name} (id: {folder_id})")
        return folder_id

    print(f"  警告: 无法创建文件夹 '{folder_name}': HTTP {resp.status_code}: {resp.text}")
    return 0


def import_dashboard(
    base_url: str,
    headers: dict,
    filepath: str,
    overwrite: bool,
    root_dir: str = "",
) -> bool:
    """导入单个 Dashboard JSON 文件，按文件夹结构还原"""
    with open(filepath, "r", encoding="utf-8") as f:
        dashboard = json.load(f)

    body = {
        "dashboard": dashboard,
        "overwrite": overwrite,
    }

    # 确定目标文件夹：优先使用 JSON 中的 _folder 元数据，回退到目录名
    folder_name = dashboard.pop("_folder", None)
    if not folder_name and root_dir:
        # 从文件所在子目录推断文件夹名（相对于 root_dir 的第一层目录）
        rel_path = os.path.relpath(filepath, root_dir)
        parts = os.path.normpath(rel_path).split(os.sep)
        if len(parts) > 1:
            folder_name = parts[0]

    if folder_name:
        folder_id = get_or_create_folder(base_url, headers, folder_name)
        if folder_id:
            body["folderId"] = folder_id

    resp = requests.post(
        f"{base_url}/api/dashboards/db",
        headers=headers,
        json=body,
        timeout=10,
    )

    if resp.ok:
        data = resp.json()
        title = data.get("meta", {}).get("title", os.path.basename(filepath))
        location = folder_name or "General"
        print(f"  成功: {title} → [{location}]")
        return True
    else:
        if resp.status_code == 409 and not overwrite:
            print(f"  跳过: 已存在 (使用 --overwrite 覆盖)")
        else:
            print(f"  失败: HTTP {resp.status_code}: {resp.text}")
        return False


def main():
    parser = argparse.ArgumentParser(description="通过 Grafana API 从本地导入 Dashboard")
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "-d", "--directory", default="./dashboards", help="Dashboard JSON 文件目录 (默认: ./dashboards)"
    )
    parser.add_argument(
        "--file", help="仅导入指定文件（支持通配符，如 'Prom-*.json'）"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="覆盖已存在的同名 Dashboard"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="仅打印待导入的文件，不实际执行"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    base_url, api_key = get_api_client(cfg["grafana"])
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 递归收集待导入的 JSON 文件
    if args.file:
        pattern = os.path.join(args.directory, "**", args.file)
    else:
        pattern = os.path.join(args.directory, "**", "*.json")

    files = sorted(glob.glob(pattern, recursive=True))
    if not files:
        print(f"在 '{args.directory}' 中未找到匹配的 JSON 文件")
        return

    # 按文件夹分组展示
    by_folder: dict[str, list[str]] = {}
    for filepath in files:
        rel = os.path.relpath(filepath, args.directory)
        parts = os.path.normpath(rel).split(os.sep)
        folder = parts[0] if len(parts) > 1 else "(根目录)"
        by_folder.setdefault(folder, []).append(filepath)

    print(f"共 {len(files)} 个文件待导入")
    for folder_name, folder_files in by_folder.items():
        print(f"  [{folder_name}] {len(folder_files)} 个")

    if args.dry_run:
        print()
        for filepath in files:
            rel = os.path.relpath(filepath, args.directory)
            print(f"  [dry-run] {rel}")
        return

    print()
    success_count = 0
    for folder_name, folder_files in by_folder.items():
        print(f"[{folder_name}]")
        for filepath in folder_files:
            print(f"  导入: {os.path.relpath(filepath, args.directory)}", end=" ... ")
            if import_dashboard(base_url, headers, filepath, args.overwrite, args.directory):
                success_count += 1
        print()

    print(f"完成: {success_count}/{len(files)} 成功")


if __name__ == "__main__":
    main()
