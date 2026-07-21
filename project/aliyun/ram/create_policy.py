# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys
import json

from typing import List

from alibabacloud_ram20150501.client import Client as Ram20150501Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ram20150501 import models as ram_20150501_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Ram20150501Client:
        """
        Initialize the Client with the credentials
        @return: Client
        @throws Exception
        """
        # It is recommended to use the default credential. For more credentials, please refer to: https://www.alibabacloud.com/help/en/alibaba-cloud-sdk-262060/latest/configure-credentials-378659.
        credential = CredentialClient()
        config = open_api_models.Config(
            credential=credential
        )
        # See https://api.alibabacloud.com/product/Ram.
        config.endpoint = f'ram.aliyuncs.com'
        return Ram20150501Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> str:
        client = Sample.create_client()
        create_policy_version_request = ram_20150501_models.CreatePolicyVersionRequest(
            policy_name='sre-opshub-base-policy',
            policy_document='''{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "log:CreateProject",
        "log:CreateLogStore",
        "log:CreateIndex",
        "log:CreateLogtailPipelineConfig",
        "log:GetLogStore",
        "log:CreateMachineGroup",
        "log:ListConfig",
        "log:ListProject",
        "log:ListLogStores",
        "log:ListDashboard",
        "log:ListMachineGroup",
        "log:GetProject",
        "log:GetConfig",
        "log:GetLogtailPipelineConfig",
        "log:GetIndex",
        "log:GetDashboard",
        "log:GetMachineGroup",
        "log:GetAppliedMachineGroups",
        "log:GetLogStoreMeteringMode",
        "log:ListLogtailPipelineConfig",
        "log:UpdateProject",
        "log:UpdateConfig",
        "log:UpdateIndex",
        "log:UpdateLogtailPipelineConfig",
        "log:UpdateLogStore",
        "log:UpdateLogStoreMeteringMode",
        "log:DeleteProject",
        "log:DeleteIndex",
        "log:DeleteLogtailPipelineConfig",
        "log:DeleteMachineGroup",
        "log:DeleteLogStore",
        "log:ApplyConfigToGroup",
        "log:RemoveConfigFromGroup",
        "log:SplitShard",
        "log:MergeShard",
        "log:ListShards",
        "dcdn:DescribeDcdnUserDomains",
        "dcdn:DescribeDcdnDomainDetail",
        "dcdn:BatchSetDcdnDomainConfigs",
        "dcdn:DescribeDcdnDomainConfigs",
        "dcdn:DeleteDcdnSpecificConfig",
        "dcdn:StopDcdnDomain",
        "dcdn:StartDcdnDomain",
        "dcdn:AddDcdnDomain",
        "dcdn:BatchAddDcdnDomain",
        "dcdn:UpdateDcdnDomain",
        "dcdn:DeleteDcdnDomain",
        "dcdn:ModifyDCdnDomainSchdmByProperty",
        "dcdn:RefreshDcdnObjectCaches",
        "dcdn:PreloadDcdnObjectCaches",
        "dcdn:DescribeDcdnRefreshTasks",
        "dcdn:DescribeDcdnRefreshQuota",
        "dcdn:DescribeDcdnRefreshTaskById",
        "dcdn:DescribeDcdnDomainUsageData",
        "dcdn:DescribeDcdnUserResourcePackage",
        
        "vpc:DescribeVpcs",
        "vpc:CreateVpc",
        "vpc:DescribeVSwitches",
        "vpc:CreateVSwitch",
        "vpc:DescribeVpcAttribute",
        "vpc:DescribeVSwitchAttributes",
        
        "cs:CreateCluster",
        
        "domain:QueryCommonInfo",
        
        "alidns:DescribeDomainRecords",
        "alidns:UpdateDomainRecord",
        "alidns:SetDomainRecordStatus",
        "alidns:DescribeDomainRecordInfo",
        "alidns:AddDomainRecord",
        "alidns:DeleteDomainRecord",
        "alidns:UpdateDomainRecordRemark",
        
        "yundun-cert:ListCertificates",
        "yundun-cert:ListUserCertificateOrder",
        "yundun-cert:ListCert",
        "yundun-cert:DescribeCertificateState",
        "yundun-cert:GetUserCertificateDetail",
        "yundun-cert:GetInstanceDetail",
        
        "ecs:DescribeInstances",
        "ecs:RunCommand",
        "ecs:DescribeInvocationResults"
        
        
      ],
      "Resource": "*"
    }
  ]
}''',
            rotate_strategy='DeleteOldestNonDefaultVersionWhenLimitExceeded'
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.create_policy_version_with_options(create_policy_version_request, runtime)
            # print(json.dumps(resp, default=str, indent=2))
            return resp.body.policy_version.version_id
        except Exception as error:
            # Only a printing example. Please be careful about exception handling and do not ignore exceptions directly in engineering projects.
            # print error message
            print(error.message)
            # Please click on the link below for diagnosis.
            print(error.data.get("Recommend"))

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        client = Sample.create_client()
        create_policy_version_request = ram_20150501_models.CreatePolicyVersionRequest(
            policy_name='opshub',
            policy_document='''{
    "Version": "1",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "log:CreateTicket",
            "Resource": "acs:log:*:*:ticket/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "log:GetConfig",
                "log:GetCursorOrData",
                "log:GetDashboard",
                "log:GetIndex",
                "log:GetLogging",
                "log:GetLogStoreLogs",
                "log:GetLogStoreMeteringMode",
                "log:GetLogtailPipelineConfig",
                "log:GetMachineGroup",
                "log:GetProductDataCollection",
                "log:GetProject",
                "log:GetProjectPolicy",
                "log:GetSqlInstance",
                "log:GetStoreView",
                "log:GetStoreViewIndex",
                "log:ListLogStores",
                "log:ListProject"
            ],
            "Resource": "*"
        }
    ]
}''',
            rotate_strategy='DeleteOldestNonDefaultVersionWhenLimitExceeded'
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await client.create_policy_version_with_options_async(create_policy_version_request, runtime)
            print(json.dumps(resp, default=str, indent=2))
        except Exception as error:
            # Only a printing example. Please be careful about exception handling and do not ignore exceptions directly in engineering projects.
            # print error message
            print(error.message)
            # Please click on the link below for diagnosis.
            print(error.data.get("Recommend"))

    @staticmethod
    def set_default_policy_version(policy_name: str, policy_version: str) -> None:
        client = Sample.create_client()
        set_default_policy_version_request = ram_20150501_models.SetDefaultPolicyVersionRequest(
            policy_name=policy_name,
            version_id=policy_version,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.set_default_policy_version_with_options(set_default_policy_version_request, runtime)
            print(json.dumps(resp, default=str, indent=2))
        except Exception as error:
            # Only a printing example. Please be careful about exception handling and do not ignore exceptions directly in engineering projects.
            # print error message
            print(error.message)
            # Please click on the link below for diagnosis.
            print(error.data.get("Recommend"))

if __name__ == '__main__':
    policy_version = Sample.main(sys.argv[1:])
    print(policy_version)
    Sample.set_default_policy_version('sre-opshub-base-policy', policy_version)
