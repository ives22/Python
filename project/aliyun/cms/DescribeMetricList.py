#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence


ENDPOINT = "metrics.ap-southeast-1.aliyuncs.com"
ACCESS_KEY_ID_ENV = "ALIBABA_CLOUD_ACCESS_KEY_ID"
ACCESS_KEY_SECRET_ENV = "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
UTC_PLUS_8 = timezone(timedelta(hours=8))


def positive_integer(value: str) -> int:
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("必须是整数") from error
    if result <= 0:
        raise argparse.ArgumentTypeError("必须大于 0")
    return result


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="调用阿里云 CMS DescribeMetricList 获取监控数据。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--namespace", required=True, help="云产品的数据命名空间")
    parser.add_argument(
        "--metric-name",
        "--metric_name",
        dest="metric_name",
        required=True,
        help="监控项名称",
    )
    parser.add_argument(
        "--start-time",
        "--start_time",
        dest="start_time",
        help="开始时间；无时区格式按 UTC+8 处理，省略时取结束时间前 1 小时",
    )
    parser.add_argument(
        "--end-time",
        "--end_time",
        dest="end_time",
        help="结束时间；无时区格式按 UTC+8 处理，省略时取当前时间",
    )
    parser.add_argument(
        "--dimensions",
        default="",
        help='维度 JSON 数组，例如 [{"instanceId":"example.com"}]；默认为空',
    )
    parser.add_argument(
        "--period",
        type=positive_integer,
        default=60,
        help="监控数据的时间间隔，单位为秒",
    )
    return parser.parse_args(args)


def parse_api_time(value: str, argument_name: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith(("Z", "z")):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        result = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(
            f"{argument_name} 时间格式无效，例如 2026-09-03 16:15:32 "
            "或 2026-09-03T08:15:32Z"
        ) from error

    if result.tzinfo is None or result.utcoffset() is None:
        result = result.replace(tzinfo=UTC_PLUS_8)
    return result.astimezone(timezone.utc).replace(microsecond=0)


def format_api_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_time_range(
    start_time: str | None,
    end_time: str | None,
    now: datetime | None = None,
) -> tuple[str, str]:
    if end_time:
        resolved_end = parse_api_time(end_time, "--end-time")
    else:
        resolved_end = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        resolved_end = resolved_end.replace(microsecond=0)

    if start_time:
        resolved_start = parse_api_time(start_time, "--start-time")
    else:
        resolved_start = resolved_end - timedelta(hours=1)

    if resolved_start >= resolved_end:
        raise ValueError("--start-time 必须早于 --end-time")

    return format_api_time(resolved_start), format_api_time(resolved_end)


def normalize_dimensions(value: str) -> str | None:
    if not value.strip():
        return None

    try:
        dimensions = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"--dimensions 不是有效 JSON：{error.msg}") from error

    if not isinstance(dimensions, list) or not all(
        isinstance(item, dict) for item in dimensions
    ):
        raise ValueError("--dimensions 必须是由对象组成的 JSON 数组")

    return json.dumps(dimensions, ensure_ascii=False, separators=(",", ":"))


def build_request_parameters(
    args: argparse.Namespace,
    now: datetime | None = None,
) -> dict[str, str]:
    start_time, end_time = resolve_time_range(args.start_time, args.end_time, now)
    parameters = {
        "namespace": args.namespace,
        "metric_name": args.metric_name,
        "start_time": start_time,
        "end_time": end_time,
        "period": str(args.period),
    }
    dimensions = normalize_dimensions(args.dimensions)
    if dimensions is not None:
        parameters["dimensions"] = dimensions
    return parameters


def load_credentials() -> tuple[str, str]:
    access_key_id = os.getenv(ACCESS_KEY_ID_ENV)
    access_key_secret = os.getenv(ACCESS_KEY_SECRET_ENV)
    missing = [
        name
        for name, value in (
            (ACCESS_KEY_ID_ENV, access_key_id),
            (ACCESS_KEY_SECRET_ENV, access_key_secret),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"缺少环境变量：{', '.join(missing)}")
    return access_key_id, access_key_secret


def execute_request(parameters: dict[str, str]) -> Any:
    access_key_id, access_key_secret = load_credentials()
    try:
        from alibabacloud_cms20190101 import models as cms_models
        from alibabacloud_cms20190101.client import Client as CmsClient
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_tea_util import models as util_models
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "缺少阿里云 CMS SDK，请安装 alibabacloud-cms20190101、"
            "alibabacloud-tea-openapi 和 alibabacloud-tea-util"
        ) from error

    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
    )
    config.endpoint = ENDPOINT
    client = CmsClient(config)
    request = cms_models.DescribeMetricListRequest(**parameters)
    runtime = util_models.RuntimeOptions()
    return client.describe_metric_list_with_options(request, runtime)


def response_to_json(response: Any) -> str:
    payload = response.to_map() if hasattr(response, "to_map") else response
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


def print_api_error(error: Exception) -> None:
    message = getattr(error, "message", None) or str(error)
    print(f"请求失败：{message}", file=sys.stderr)

    data = getattr(error, "data", None)
    if isinstance(data, dict) and data.get("Recommend"):
        print(f"诊断建议：{data['Recommend']}", file=sys.stderr)


def main(args: Sequence[str] | None = None) -> int:
    try:
        parsed_args = parse_args(args)
        parameters = build_request_parameters(parsed_args)
        response = execute_request(parameters)
    except (RuntimeError, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2
    except Exception as error:
        print_api_error(error)
        return 1

    print(response_to_json(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
