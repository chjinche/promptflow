# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
# pylint: disable=wrong-import-position
import json
import time

from promptflow._cli._utils import _get_cli_activity_name
from promptflow._sdk._telemetry import ActivityType, get_telemetry_logger, log_activity
from promptflow._sdk._telemetry.activity import update_activity_name

# Log the start time
start_time = time.perf_counter()

# E402 module level import not at top of file
import argparse  # noqa: E402
import logging  # noqa: E402
import sys  # noqa: E402

from promptflow._cli._pf._config import add_config_parser, dispatch_config_commands  # noqa: E402
from promptflow._cli._pf._connection import add_connection_parser, dispatch_connection_commands  # noqa: E402
from promptflow._cli._pf._flow import add_flow_parser, dispatch_flow_commands  # noqa: E402
from promptflow._cli._pf._run import add_run_parser, dispatch_run_commands  # noqa: E402
from promptflow._cli._pf._tool import add_tool_parser, dispatch_tool_commands  # noqa: E402
from promptflow._cli._pf.help import show_privacy_statement, show_welcome_message  # noqa: E402
from promptflow._cli._user_agent import USER_AGENT  # noqa: E402
from promptflow._sdk._utils import (  # noqa: E402
    get_promptflow_sdk_version,
    print_pf_version,
    setup_user_agent_to_operation_context,
)
from promptflow._utils.logger_utils import get_cli_sdk_logger  # noqa: E402

# get logger for CLI
logger = get_cli_sdk_logger()


def run_command(args):
    # Log the init finish time
    init_finish_time = time.perf_counter()
    try:
        # --verbose, enable info logging
        if hasattr(args, "verbose") and args.verbose:
            for handler in logger.handlers:
                handler.setLevel(logging.INFO)
        # --debug, enable debug logging
        if hasattr(args, "debug") and args.debug:
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)

        if args.version:
            print_pf_version()
        elif args.action == "flow":
            dispatch_flow_commands(args)
        elif args.action == "connection":
            dispatch_connection_commands(args)
        elif args.action == "run":
            dispatch_run_commands(args)
        elif args.action == "config":
            dispatch_config_commands(args)
        elif args.action == "tool":
            dispatch_tool_commands(args)
    except KeyboardInterrupt as ex:
        logger.debug("Keyboard interrupt is captured.")
        raise ex
    except SystemExit as ex:  # some code directly call sys.exit, this is to make sure command metadata is logged
        exit_code = ex.code if ex.code is not None else 1
        logger.debug(f"Code directly call sys.exit with code {exit_code}")
        raise ex
    except Exception as ex:
        logger.debug(f"Command {args} execute failed. {str(ex)}")
        raise ex
    finally:
        # Log the invoke finish time
        invoke_finish_time = time.perf_counter()
        logger.info(
            "Command ran in %.3f seconds (init: %.3f, invoke: %.3f)",
            invoke_finish_time - start_time,
            init_finish_time - start_time,
            invoke_finish_time - init_finish_time,
        )


def get_parser_args(argv):
    parser = argparse.ArgumentParser(
        prog="pf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="pf: manage prompt flow assets. Learn more: https://microsoft.github.io/promptflow.",
    )
    parser.add_argument(
        "-v", "--version", dest="version", action="store_true", help="show current CLI version and exit"
    )

    subparsers = parser.add_subparsers()
    add_flow_parser(subparsers)
    add_connection_parser(subparsers)
    add_run_parser(subparsers)
    add_config_parser(subparsers)
    add_tool_parser(subparsers)

    return parser.prog, parser.parse_args(argv)


def entry(argv):
    """
    Control plane CLI tools for promptflow.
    """
    prog, args = get_parser_args(argv)
    if hasattr(args, "user_agent"):
        setup_user_agent_to_operation_context(args.user_agent)
    logger = get_telemetry_logger()
    activity_name = _get_cli_activity_name(cli=prog, args=args)
    activity_name = update_activity_name(activity_name, args=args)
    with log_activity(logger, activity_name, activity_type=ActivityType.PUBLICAPI):
        run_command(args)


def main():
    """Entrance of pf CLI."""
    command_args = sys.argv[1:]
    if len(command_args) == 1 and command_args[0] == "version":
        version_dict = {"promptflow": get_promptflow_sdk_version()}
        return json.dumps(version_dict, ensure_ascii=False, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"
    if len(command_args) == 0:
        # print privacy statement & welcome message like azure-cli
        show_privacy_statement()
        show_welcome_message()
        command_args.append("-h")
    elif len(command_args) == 1:
        # pf only has "pf --version" with 1 layer
        if command_args[0] not in ["--version", "-v"]:
            command_args.append("-h")
    setup_user_agent_to_operation_context(USER_AGENT)
    entry(command_args)


if __name__ == "__main__":
    main()
