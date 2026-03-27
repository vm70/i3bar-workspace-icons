"""Main entry point for `i3bar-workspace-icons`."""

import argparse
import logging
import os
import pathlib
from importlib.metadata import metadata

import i3ipc

from i3bar_workspace_icons.configuration import dirs, dump_config, generate_config
from i3bar_workspace_icons.icon_updater import IconUpdater

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename=pathlib.Path(dirs.user_log_dir, "debug.log"),
    level=logging.INFO,
    encoding="utf-8",
    format="%(asctime)s - PID %(process)d [%(levelname)s]: %(message)s",
)


def read_argv() -> argparse.Namespace:
    """Read command line arguments."""
    parser = argparse.ArgumentParser(
        prog="i3bar-workspace-icons",
        description=metadata("i3bar-workspace-icons")["Summary"],
        epilog=(
            "You shouldn't need to run this program directly in the terminal. "
            "Instead, set it as the `workspace_command` in your i3bar configurtion."
        ),
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="show the version number of this program and exit",
    )
    parser.add_argument(
        "-d",
        "--dump-config",
        action="store_true",
        help="dump the current configuration and exit",
    )
    parser.add_argument(
        "-D",
        "--debug",
        action="store_true",
        help="enable debug logging",
        default=False,
    )
    parser.add_argument(
        "-c",
        "--configfile",
        action="append",
        dest="configfiles",
        help="path to configuration files to use instead of the XDG default",
        default=[],
    )

    args = parser.parse_args()
    logger.debug("Command line arguments: %s", args)
    return args


def main() -> None:
    """Main entry point to the program."""
    os.makedirs(dirs.user_log_dir, exist_ok=True)
    args = read_argv()

    # Print version number and exit
    if args.version:
        logger.debug("printing version number")
        print(metadata("i3bar-workspace-icons")["Version"])
        return

    # Enable debug logging
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Load the configuration
    config, _ = generate_config(args.configfiles)

    # Dump the configuration and exit
    if args.dump_config:
        logger.debug("dumping config")
        dump_config(config)
        return

    # Start the icon updater
    i3 = i3ipc.Connection()
    icon_updater = IconUpdater(config)

    logger.debug("starting icon updater")
    icon_updater.update_workspace_icons(i3, None)
    i3.on(i3ipc.Event.WINDOW, icon_updater.update_workspace_icons)
    i3.on(i3ipc.Event.WORKSPACE, icon_updater.update_workspace_icons)
    i3.on(i3ipc.Event.OUTPUT, icon_updater.update_workspace_icons)
    i3.main()


if __name__ == "__main__":
    main()
