# -*- coding: utf-8 -*-
# 用于测试，阿里云 通过角色扮演的方式 去获取资源
# 参考文档：
#   RAM 角色扮演：https://help.aliyun.com/zh/ram/user-guide/assume-a-ram-role#e576be99f1xdw
#   Python 凭证管理：https://help.aliyun.com/zh/sdk/developer-reference/v2-manage-python-access-credentials
#   OSS SDK：https://help.aliyun.com/zh/oss/developer-reference/2-0-manual-preview-version
from __future__ import annotations

import os
import sys

from typing import List

from alibabacloud_oss_v2 import models as oss_models
from alibabacloud_oss_v2.client import Client
from alibabacloud_oss_v2.config import Config
from alibabacloud_oss_v2.credentials import CredentialsProvider, Credentials
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.models import Config as CredentialConfig


class RamRoleArnCredentialsProvider(CredentialsProvider):
    """自定义 CredentialsProvider，将 alibabacloud_credentials 适配到 OSS v2 SDK"""

    def __init__(self, credentials_client: CredentialClient):
        self._client = credentials_client

    def get_credentials(self) -> Credentials:
        credential = self._client.get_credential()
        return Credentials(
            access_key_id=credential.access_key_id,
            access_key_secret=credential.access_key_secret,
            security_token=credential.security_token,
        )


class Sample:

    def __init__(self):
        pass

    @staticmethod
    def list_buckets() -> None:
        # 使用 RAM Role ARN 方式获取临时凭证
        # 需要设置环境变量：
        #   ALIBABA_CLOUD_ACCESS_KEY_ID     - 主账号/子账号 AccessKey ID
        #   ALIBABA_CLOUD_ACCESS_KEY_SECRET - 主账号/子账号 AccessKey Secret
        # 以下参数也可通过环境变量传入，这里写死在代码中方便调试
        credentials_config = CredentialConfig(
            type='ram_role_arn',
            access_key_id=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID'),
            access_key_secret=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
            role_arn='acs:ram::5275618694441737:role/srerole',  # 替换为目标角色 ARN
            role_session_name='oss-list-buckets-session',
            role_session_expiration=3600,
        )
        credentials_client = CredentialClient(credentials_config)
        credentials_provider = RamRoleArnCredentialsProvider(credentials_client)

        config = Config(
            credentials_provider=credentials_provider,
            region='ap-southeast-1',
        )
        client = Client(config)
        list_buckets_request = oss_models.ListBucketsRequest()
        resp = client.list_buckets(list_buckets_request)
        print(resp.buckets)
        print(vars(resp))
        for i in resp.buckets:
            print(i.name)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        Sample.list_buckets()

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        Sample.list_buckets()


if __name__ == '__main__':
    Sample.main(sys.argv[1:])
