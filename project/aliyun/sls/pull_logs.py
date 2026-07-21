# -*- coding: utf-8 -*-
import sys
import json
from datetime import datetime
from typing import List

from alibabacloud_sls20201230.client import Client as Sls20201230Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_sls20201230 import models as sls_20201230_models
from alibabacloud_tea_util import models as util_models


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Sls20201230Client:
        credential = CredentialClient()
        config = open_api_models.Config(
            credential=credential
        )
        config.endpoint = 'ap-southeast-1.log.aliyuncs.com'
        return Sls20201230Client(config)

    @staticmethod
    def parse_time(time_str: str) -> int:
        """Parse formatted time string to Unix timestamp.

        Supported formats:
            - 'YYYY-MM-DD HH:MM:SS'
            - 'YYYY-MM-DD'
            - Unix timestamp (integer string)
        """
        try:
            return int(time_str)
        except ValueError:
            pass

        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(time_str, fmt)
                return int(dt.timestamp())
            except ValueError:
                continue

        raise ValueError(f"Unsupported time format: {time_str}")

    @staticmethod
    def main(args: List[str]) -> None:
        if len(args) < 4:
            print("Usage: python pull_logs.py <project> <logstore> <start_time> <end_time> [query] [count]")
            print("  start_time: 'YYYY-MM-DD HH:MM:SS' | 'YYYY-MM-DD' | unix timestamp")
            print("  end_time:   'YYYY-MM-DD HH:MM:SS' | 'YYYY-MM-DD' | unix timestamp")
            print("  query:      SLS query string (default: '*')")
            print("  count:      number of logs to return (default: 100)")
            return

        project = args[0]
        logstore = args[1]
        start_time_str = args[2]
        end_time_str = args[3]
        query = args[4] if len(args) > 4 else '*'
        count = int(args[5]) if len(args) > 5 else 100

        start_timestamp = Sample.parse_time(start_time_str)
        end_timestamp = Sample.parse_time(end_time_str)

        client = Sample.create_client()
        runtime = util_models.RuntimeOptions()
        headers = {}

        request = sls_20201230_models.GetLogsRequest(
            from_=start_timestamp,
            to=end_timestamp,
            query=query,
            line=count,
            reverse=True
        )

        try:
            resp = client.get_logs_with_options(project, logstore, request, headers, runtime)
            if resp.body:
                print(f"Total logs returned: {len(resp.body)}")
                for log in resp.body:
                    print(json.dumps(log, default=str, indent=2))
            else:
                print("No logs returned")
        except Exception as error:
            print(f"Error: {error}")

if __name__ == '__main__':
    Sample.main(sys.argv[1:])
