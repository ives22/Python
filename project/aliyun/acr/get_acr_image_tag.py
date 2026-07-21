# -*- coding: utf-8 -*-
import json
import os
from alibabacloud_cr20160607.client import Client as cr_client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_openapi_util.client import Client as OpenApiUtilClient


def get_acr_personal_tags():
    # 1. 获取凭证 (请确保已在系统中设置了这两个环境变量)
    access_key_id = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET')

    # 2. 配置参数 (请根据实际情况修改)
    region_id = 'ap-southeast-1'  # 替换为你的 ACR 所在地域
    namespace = 'relax_many_game'  # 替换为你的命名空间
    repo_name = '5117'  # 替换为你的镜像仓库名称

    # 3. 初始化 Config
    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        # 个人版 Endpoint 格式通常为 cr.<region_id>.aliyuncs.com
        endpoint=f'cr.{region_id}.aliyuncs.com'
    )

    # 4. 实例化客户端 (个人版专属客户端)
    client = cr_client(config)

    try:
        # 5. 直接调用底层 call_api 获取原始响应
        #    (SDK 的 GetRepoTagsResponse 模型缺少 body 字段，无法直接使用高层方法)
        print(f"正在查询 {namespace}/{repo_name} 的镜像 Tags...")
        runtime = util_models.RuntimeOptions()
        req = open_api_models.OpenApiRequest(
            headers={},
            query=OpenApiUtilClient.query({})
        )
        params = open_api_models.Params(
            action='GetRepoTags',
            version='2016-06-07',
            protocol='HTTPS',
            pathname=f'/repos/{namespace}/{repo_name}/tags',
            method='GET',
            auth_type='AK',
            style='ROA',
            req_body_type='json',
            body_type='none'
        )
        raw_response = client.call_api(params, req, runtime)

        # 6. 解析返回的 JSON body
        body = json.loads(raw_response['body'])
        data = body.get('data', {})
        tags = data.get('tags', [])
        total = data.get('total', 0)

        # 7. 输出结果
        if tags:
            print(f"查询成功，共找到 {total} 个 Tag:")
            print("-" * 40)
            for tag_info in tags:
                print(f"Tag 名称: {tag_info['tag']}")
                print(f"镜像 ID:  {tag_info['imageId']}")
                print(f"镜像大小: {tag_info['imageSize']} Bytes")
                print(f"更新时间: {tag_info['imageUpdate']}")
                print("-" * 40)
        else:
            print("该镜像仓库下目前没有任何 Tag。")

    except Exception as e:
        print(f"获取镜像 Tag 失败: {e}")


if __name__ == '__main__':
    get_acr_personal_tags()
