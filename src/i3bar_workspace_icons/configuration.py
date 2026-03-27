"""Tools for generating, updating, and determining the program's configuration."""

import logging
import sys
from configparser import ConfigParser
from importlib.resources import as_file, files
from os import PathLike
from pathlib import Path

from platformdirs import PlatformDirs

logger = logging.getLogger(__name__)

dirs = PlatformDirs(appname="i3bar-workspace-icons", appauthor="vm70")
"""Class containing platform-specific directories for the program."""

CONFIG_FILE_NAME = "config.ini"
"""Name of the default configuration file in the user & site config directories."""

DEFAULT_CONFIG_INI = files("i3bar_workspace_icons").joinpath("default_config.ini")
"""Path to the default configuration file in the package."""


def generate_config(
    configfiles: list[PathLike | str] | PathLike | str | None = None,
) -> tuple[ConfigParser, list[str]]:
    """Generate the configuration for this application.

    If no configuration files are provided, the default configuration files
    will be loaded from:

    - `default_config.ini` in the package
    - `config.ini` in the site config directory
    - `config.ini` in the user config directory

    Args:
        configfiles: The list of configuration files to load, or `None`.

    Returns:
        config: the configuration.
        read_files: the files that were read.
    """
    config = ConfigParser()

    # Coerce into a list of Paths
    if isinstance(configfiles, (Path, str)):
        configfiles = [configfiles]
    elif isinstance(configfiles, list):
        configfiles = [Path(f) for f in configfiles]
    else:
        configfiles = []

    if len(configfiles) == 0:
        with as_file(DEFAULT_CONFIG_INI) as config_path:
            read_files = config.read(
                filenames=[
                    config_path,
                    str(dirs.site_config_path / CONFIG_FILE_NAME),
                    str(dirs.user_config_path / CONFIG_FILE_NAME),
                ],
                encoding="utf-8",
            )
    else:
        read_files = config.read(filenames=configfiles, encoding="utf-8")

    return config, read_files


def dump_config(config: ConfigParser) -> None:
    """Dump the ConfigParser's configuration to `stdout`."""
    config.write(sys.stdout)
