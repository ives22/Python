# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys
import json

from typing import List

from alibabacloud_sls20201230.client import Client as Sls20201230Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_sls20201230 import models as sls_20201230_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Sls20201230Client:
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
        # See https://api.alibabacloud.com/product/Sls.
        config.endpoint = f'ap-southeast-1.log.aliyuncs.com'
        return Sls20201230Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        client = Sample.create_client()
        create_ticket_request = sls_20201230_models.CreateTicketRequest(
            expiration_time=86400,
            access_token_expiration_time=86400
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            resp = client.create_ticket_with_options(create_ticket_request, headers, runtime)
            print(json.dumps(resp, default=str, indent=2))
            print(resp.body.ticket)
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
        create_ticket_request = sls_20201230_models.CreateTicketRequest(
            expiration_time=86400,
            access_token_expiration_time=86400
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            resp = await client.create_ticket_with_options_async(create_ticket_request, headers, runtime)
            print(json.dumps(resp, default=str, indent=2))


        except Exception as error:
            # Only a printing example. Please be careful about exception handling and do not ignore exceptions directly in engineering projects.
            # print error message
            print(error.message)
            # Please click on the link below for diagnosis.
            print(error.data.get("Recommend"))


if __name__ == '__main__':
    Sample.main(sys.argv[1:])
