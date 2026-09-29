import contextlib
import io
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import DescribeMetricList as metric_list


class DescribeMetricListArgumentsTest(unittest.TestCase):
    def test_defaults_to_last_hour_with_empty_dimensions_and_period_60(self):
        args = metric_list.parse_args(
            ["--namespace", "acs_dcdn", "--metric-name", "dcdn_qps"]
        )
        now = datetime(2026, 9, 4, 2, 30, 45, tzinfo=timezone.utc)

        parameters = metric_list.build_request_parameters(args, now=now)

        self.assertEqual(parameters["namespace"], "acs_dcdn")
        self.assertEqual(parameters["metric_name"], "dcdn_qps")
        self.assertEqual(parameters["start_time"], "2026-09-04T01:30:45Z")
        self.assertEqual(parameters["end_time"], "2026-09-04T02:30:45Z")
        self.assertEqual(parameters["period"], "60")
        self.assertNotIn("dimensions", parameters)

    def test_passes_explicit_parameters_to_request(self):
        args = metric_list.parse_args(
            [
                "--namespace",
                "acs_dcdn",
                "--metric-name",
                "dcdn_qps",
                "--start-time",
                "2026-09-03T18:15:32+08:00",
                "--end-time",
                "2026-09-03T18:45:32+08:00",
                "--dimensions",
                '[{"instanceId": "res3.joyaras.com"}]',
                "--period",
                "300",
            ]
        )

        parameters = metric_list.build_request_parameters(args)

        self.assertEqual(parameters["start_time"], "2026-09-03T10:15:32Z")
        self.assertEqual(parameters["end_time"], "2026-09-03T10:45:32Z")
        self.assertEqual(
            parameters["dimensions"],
            '[{"instanceId":"res3.joyaras.com"}]',
        )
        self.assertEqual(parameters["period"], "300")

    def test_treats_datetime_without_timezone_as_utc_plus_8(self):
        args = metric_list.parse_args(
            [
                "--namespace",
                "acs_dcdn",
                "--metric-name",
                "dcdn_qps",
                "--start-time",
                "2026-09-03 16:15:32",
                "--end-time",
                "2026-09-03 16:45:32",
            ]
        )

        parameters = metric_list.build_request_parameters(args)

        self.assertEqual(parameters["start_time"], "2026-09-03T08:15:32Z")
        self.assertEqual(parameters["end_time"], "2026-09-03T08:45:32Z")

    def test_derives_start_time_from_explicit_end_time(self):
        args = metric_list.parse_args(
            [
                "--namespace",
                "acs_dcdn",
                "--metric-name",
                "dcdn_qps",
                "--end-time",
                "2026-09-03T10:45:32Z",
            ]
        )

        parameters = metric_list.build_request_parameters(args)

        self.assertEqual(parameters["start_time"], "2026-09-03T09:45:32Z")
        self.assertEqual(parameters["end_time"], "2026-09-03T10:45:32Z")

    def test_rejects_non_array_dimensions(self):
        args = metric_list.parse_args(
            [
                "--namespace",
                "acs_dcdn",
                "--metric-name",
                "dcdn_qps",
                "--dimensions",
                '{"instanceId":"res3.joyaras.com"}',
            ]
        )

        with self.assertRaisesRegex(ValueError, "JSON 数组"):
            metric_list.build_request_parameters(args)

    def test_rejects_non_positive_period(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                metric_list.parse_args(
                    [
                        "--namespace",
                        "acs_dcdn",
                        "--metric-name",
                        "dcdn_qps",
                        "--period",
                        "0",
                    ]
                )

        self.assertEqual(error.exception.code, 2)


class DescribeMetricListCredentialsTest(unittest.TestCase):
    def test_reads_access_key_from_environment(self):
        environment = {
            "ALIBABA_CLOUD_ACCESS_KEY_ID": "test-access-key-id",
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "test-access-key-secret",
        }

        with patch.dict(os.environ, environment, clear=True):
            credentials = metric_list.load_credentials()

        self.assertEqual(
            credentials,
            ("test-access-key-id", "test-access-key-secret"),
        )

    def test_reports_missing_environment_variables(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "ALIBABA_CLOUD_ACCESS_KEY_ID.*ALIBABA_CLOUD_ACCESS_KEY_SECRET",
            ):
                metric_list.load_credentials()


if __name__ == "__main__":
    unittest.main()
