#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <https://www.gnu.org/licenses/>.

import argparse
import os
import multiprocessing
import sys
from importlib import util
from typing import Any

from fluster.fluster import Fluster, Context, SummaryFormat

TEST_SUITES_DIR = "test_suites"
TEST_SUITES_DIR_SYS = "/usr/share/fluster/test_suites"
DECODERS_DIR = "decoders"
RESOURCES_DIR = "resources"
RESULTS_DIR = "results"


def fluster_main() -> None:
    """Entrypoint for the application."""
    main = Main()
    main.run()


class Main:
    """Main class for Fluster"""

    # pylint: disable=broad-except

    def __init__(self) -> None:
        self.decoders_dir = DECODERS_DIR
        self.test_suites_dir = TEST_SUITES_DIR
        # Only use the system directory for test suites if the local directory
        # doesn't exist and the system directory does exist.
        if (
            sys.platform.startswith("linux")
            and not os.path.exists(TEST_SUITES_DIR)
            and os.path.exists(TEST_SUITES_DIR_SYS)
        ):
            self.test_suites_dir = TEST_SUITES_DIR_SYS
        self.parser = self._create_parser()

        # Prepend to the PATH the decoders_dir so that we can run them
        # without having to set the env for every single command
        os.environ["PATH"] = self.decoders_dir + os.path.pathsep + os.environ["PATH"]

    def run(self) -> None:
        """Runs Fluster"""
        args = self.parser.parse_args()
        self._validate_args(args)
        self._validate_deps(args)
        if hasattr(args, "func"):
            fluster = Fluster(
                test_suites_dir=args.test_suites_dir,
                decoders_dir=self.decoders_dir,
                resources_dir=args.resources,
                results_dir=args.output,
                use_emoji=not args.no_emoji,
            )
            args.func(args, fluster)
        else:
            self.parser.print_help()

    def _validate_args(self, args: Any) -> None:
        if hasattr(args, "format"):
            if (
                args.format in [SummaryFormat.JUNITXML.value, SummaryFormat.CSV.value]
                and not args.summary_output
            ):
                sys.exit(
                    "error: please specify XML/CSV file path with -so/--summary-output option."
                )

    def _validate_deps(self, args: Any) -> None:
        if hasattr(args, "format"):
            junit_spec = util.find_spec("junitparser")
            if args.format == SummaryFormat.JUNITXML.value and junit_spec is None:
                sys.exit(
                    "error: junitparser required to use JUnit format. Please install with pip install junitparser."
                )

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-r",
            "--resources",
            help="set the directory where resources are taken from",
            default=RESOURCES_DIR,
        )
        parser.add_argument(
            "-o",
            "--output",
            help="set the directory where test results will be stored",
            default=RESULTS_DIR,
        )
        parser.add_argument(
            "-ne",
            "--no-emoji",
            help="set to use plain text instead of emojis",
            action="store_true",
        )
        parser.add_argument(
            "-tsd",
            "--test-suites-dir",
            help="set the directory where test suite will be read from",
            default=self.test_suites_dir,
        )
        subparsers = parser.add_subparsers(title="subcommands")
        self._add_list_cmd(subparsers)
        self._add_run_cmd(subparsers)
        self._add_download_cmd(subparsers)
        self._add_reference_cmd(subparsers)
        return parser

    def _add_list_cmd(self, subparsers: Any) -> None:
        subparser = subparsers.add_parser(
            "list",
            aliases=["l"],
            help="show list of available test suites and decoders",
        )
        subparser.add_argument(
            "-ts",
            "--testsuites",
            help="show only the test suites given",
            nargs="+",
        )
        subparser.add_argument(
            "-tv",
            "--testvectors",
            help="show test vectors of test suites",
            action="store_true",
        )
        subparser.add_argument(
            "-c",
            "--check",
            help="check which decoders can be run successfully. Reports ✔️ or ❌",
            action="store_true",
        )
        subparser.add_argument(
            "-v",
            "--verbose",
            help="show stdout and stderr of commands executed",
            action="store_true",
        )
        subparser.set_defaults(func=self._list_cmd)

    def _add_run_cmd(self, subparsers: Any) -> None:
        subparser = subparsers.add_parser(
            "run", aliases=["r"], help="run test suites for decoders"
        )
        subparser.add_argument(
            "-j",
            "--jobs",
            help="number of parallel jobs to use. 1x logical cores by default."
            "0 means all logical cores",
            type=int,
            default=multiprocessing.cpu_count(),
        )
        subparser.add_argument(
            "-t",
            "--timeout",
            help="timeout in secs for each decoding. Defaults to 30 secs",
            type=int,
            default=30,
        )
        subparser.add_argument(
            "-ff",
            "--failfast",
            help="stop after first fail",
            action="store_true",
        )
        subparser.add_argument(
            "-q",
            "--quiet",
            help="don't show every test run",
            action="store_true",
        )
        subparser.add_argument(
            "-ts",
            "--testsuites",
            help="run only the specific test suites",
            nargs="+",
        )
        subparser.add_argument(
            "-tv",
            "--testvectors",
            help="run only the specific test vectors",
            nargs="+",
        )
        subparser.add_argument(
            "-d",
            "--decoders",
            help="run only the specific decoders",
            nargs="+",
        )
        subparser.add_argument(
            "-s",
            "--summary",
            help="generate a summary in Markdown format for each test suite",
            action="store_true",
        )
        subparser.add_argument(
            "-so", "--summary-output", help="dump summary output to file"
        )
        subparser.add_argument(
            "-f",
            "--format",
            help="specify the format for the summary file",
            choices=list(x.value for x in SummaryFormat),
            default=SummaryFormat.MARKDOWN.value,
        )
        subparser.add_argument(
            "-k",
            "--keep",
            help="keep output files generated during the test",
            action="store_true",
        )
        subparser.add_argument(
            "-th",
            "--threshold",
            help="set exit code to 2 if threshold tests are not success. "
            "exit code is 0 otherwise",
            type=int,
        )
        subparser.add_argument(
            "-tth",
            "--time-threshold",
            help="set exit code to 3 if test suite takes longer than threshold seconds. "
            "exit code is 0 otherwise",
            type=float,
        )
        subparser.add_argument(
            "-v",
            "--verbose",
            help="show stdout and stderr of commands executed",
            action="store_true",
        )
        subparser.set_defaults(func=self._run_cmd)

    def _add_reference_cmd(self, subparsers: Any) -> None:
        subparser = subparsers.add_parser(
            "reference",
            aliases=["f"],
            help="use a specific decoder to set its results for the test suites given",
        )
        subparser.add_argument(
            "-j",
            "--jobs",
            help="number of parallel jobs to use. 1x logical cores by default."
            "0 means all logical cores",
            type=int,
            default=multiprocessing.cpu_count(),
        )
        subparser.add_argument(
            "-t",
            "--timeout",
            help="timeout in secs for each decoding. Defaults to 30 secs",
            type=int,
            default=30,
        )
        subparser.add_argument("decoder", help="decoder to run", nargs=1)
        subparser.add_argument(
            "testsuites",
            help="list of testsuites to run the decoder with",
            nargs="+",
        )
        subparser.add_argument(
            "-q",
            "--quiet",
            help="don't show every test run",
            action="store_true",
        )
        subparser.add_argument(
            "-v",
            "--verbose",
            help="show stdout and stderr of commands executed",
            action="store_true",
        )
        subparser.set_defaults(func=self._reference_cmd)

    def _add_download_cmd(self, subparsers: Any) -> None:
        subparser = subparsers.add_parser(
            "download", aliases=["d"], help="downloads test suites resources"
        )
        subparser.add_argument(
            "-j",
            "--jobs",
            help="number of parallel jobs to use. 2x logical cores by default."
            "0 means all logical cores",
            type=int,
            default=2 * multiprocessing.cpu_count(),
        )
        subparser.add_argument(
            "-k",
            "--keep",
            help="keep original downloaded file after extracting. Only applicable to compressed "
            "files such as .zip, .tar.gz, etc",
            action="store_true",
        )
        subparser.add_argument(
            "testsuites", help="list of testsuites to download", nargs="*"
        )
        subparser.set_defaults(func=self._download_cmd)

    def _list_cmd(self, args: Any, fluster: Fluster) -> None:
        fluster.list_test_suites(
            show_test_vectors=args.testvectors, test_suites=args.testsuites
        )
        fluster.list_decoders(check=args.check, verbose=args.verbose)

    def _run_cmd(self, args: Any, fluster: Fluster) -> None:
        args.jobs = args.jobs if args.jobs > 0 else multiprocessing.cpu_count()
        context = Context(
            jobs=args.jobs,
            test_suites=args.testsuites,
            timeout=args.timeout,
            decoders=args.decoders,
            test_vectors=args.testvectors,
            failfast=args.failfast,
            quiet=args.quiet,
            summary=args.summary or args.summary_output,
            keep_files=args.keep,
            threshold=args.threshold,
            time_threshold=args.time_threshold,
            verbose=args.verbose,
            summary_output=args.summary_output,
            summary_format=args.format,
        )
        try:
            fluster.run_test_suites(context)
        except SystemExit as exception:
            sys.exit(exception.code)

    def _reference_cmd(self, args: Any, fluster: Fluster) -> None:
        context = Context(
            jobs=args.jobs,
            timeout=args.timeout,
            test_suites=args.testsuites,
            decoders=args.decoder,
            test_vectors=[],
            quiet=args.quiet,
            verbose=args.verbose,
            reference=True,
        )
        try:
            fluster.run_test_suites(context)
        except SystemExit as exception:
            sys.exit(exception.code)

    def _download_cmd(self, args: Any, fluster: Fluster) -> None:
        args.jobs = args.jobs if args.jobs > 0 else multiprocessing.cpu_count()
        fluster.download_test_suites(
            test_suites=args.testsuites, jobs=args.jobs, keep_file=args.keep
        )
