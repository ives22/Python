# 阿里云 CMS 指标查询脚本

`DescribeMetricList.py` 用于临时查询阿里云云监控 `DescribeMetricList` 接口，方便获取指标数据进行对比。

接口文档：[DescribeMetricList](https://api.alibabacloud.com/api/Cms/2019-01-01/DescribeMetricList)

## 环境准备

项目使用 uv 管理依赖，虚拟环境中可能没有 `pip`。请在仓库根目录安装依赖：

```bash
cd /Users/liyj/Documents/Code/Github/Python
uv sync --default-index https://pypi.org/simple
```

`--default-index` 会覆盖当前 shell 中可能存在的 `UV_DEFAULT_INDEX`，确保本次安装使用官方 PyPI。

通过环境变量设置阿里云 AccessKey ID 和 AccessKey Secret：

```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID='your-access-key-id'
export ALIBABA_CLOUD_ACCESS_KEY_SECRET='your-access-key-secret'
```

不要将真实凭据写入脚本或提交到 Git。

## 参数说明

| 参数 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--namespace` | 是 | 无 | 云产品的数据命名空间，例如 `acs_dcdn` |
| `--metric-name` | 是 | 无 | 监控项名称，例如 `dcdn_qps`；也支持 `--metric_name` |
| `--start-time` | 否 | 结束时间前 1 小时 | 开始时间；也支持 `--start_time` |
| `--end-time` | 否 | 当前时间 | 结束时间；也支持 `--end_time` |
| `--dimensions` | 否 | 空 | 由对象组成的 JSON 数组；为空时不向 API 传递该字段 |
| `--period` | 否 | `60` | 数据采样周期，单位为秒，必须大于 `0` |

## 时间格式

脚本支持以下时间格式：

```text
2026-09-03 16:15:32        # 未携带时区，按 UTC+8 处理
2026-09-03T16:15:32+08:00  # 显式 UTC+8
2026-09-03T08:15:32Z       # UTC
```

时间在发送给阿里云 API 前统一转换成 UTC `Z` 格式。例如，`2026-09-03 16:15:32` 会转换为 `2026-09-03T08:15:32Z`。

开始时间和结束时间均未传递时，默认查询最近 1 小时的数据。只传结束时间时，开始时间取结束时间前 1 小时；只传开始时间时，结束时间取当前时间。

## 使用示例

查询最近 1 小时的数据，采样周期使用默认值 `60` 秒：

```bash
python3 DescribeMetricList.py \
  --namespace acs_dcdn \
  --metric-name dcdn_qps
```

使用 UTC+8 时间和指定维度查询：

```bash
python3 DescribeMetricList.py \
  --namespace acs_dcdn \
  --metric-name dcdn_qps \
  --start-time '2026-09-03 16:15:32' \
  --end-time '2026-09-03 16:45:32' \
  --dimensions '[{"instanceId":"res3.joyaras.com"}]' \
  --period 60
```

使用 UTC 时间查询：

```bash
python3 DescribeMetricList.py \
  --namespace acs_dcdn \
  --metric-name dcdn_qps \
  --start-time '2026-09-03T08:15:32Z' \
  --end-time '2026-09-03T08:45:32Z'
```

查看完整命令行帮助：

```bash
python3 DescribeMetricList.py --help
```

请求成功后，脚本会将 SDK 响应格式化为 JSON 输出。参数或凭据错误写入标准错误，并返回非零退出码。
