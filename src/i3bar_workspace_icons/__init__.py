"""Main entry point for `i3bar-workspace-icons`."""

import argparse
import logging
from importlib.metadata import metadata

import i3ipc

from i3bar_workspace_icons.configuration import dirs, dump_config, generate_config
from i3bar_workspace_icons.icon_updater import IconUpdater

__version__ = metadata("i3bar-workspace-icons")["Version"]
"""Version number of the program (stored in `pyproject.toml`)."""

# Ensure that user directories exist
dirs.user_config_path.mkdir(parents=True, exist_ok=True)
dirs.user_log_path.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename=dirs.user_log_path / "debug.log",
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
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Run the program without connecting to i3 and exit",
        default=False,
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point to the program."""
    args = read_argv()

    # Enable debug logging
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Print debug information
    logger.debug("Starting i3bar-workspace-icons with args: %s", args)

    # Print version number and exit
    if args.version:
        logger.debug("Printing version number")
        print(__version__)
        return

    # Load the configuration
    config, read_files = generate_config(args.configfiles)
    logger.debug("Read files: %s", read_files)

    # Dump the configuration and exit
    if args.dump_config:
        logger.debug("Dumping config")
        dump_config(config)
        return

    # Stop here if doing a dry run
    if args.dry_run:
        logger.debug("Dry run complete")
        return

    logger.debug("Connecting to i3")
    i3 = i3ipc.Connection()

    logger.debug("Initializing Icon Updater, registering callbacks")
    icon_updater = IconUpdater(config)
    icon_updater.update_workspace_icons(i3, None)
    i3.on(i3ipc.Event.WINDOW, icon_updater.update_workspace_icons)
    i3.on(i3ipc.Event.WORKSPACE, icon_updater.update_workspace_icons)
    i3.on(i3ipc.Event.OUTPUT, icon_updater.update_workspace_icons)

    logger.debug("Initialization complete")
    i3.main()


if __name__ == "__main__":
    main()
