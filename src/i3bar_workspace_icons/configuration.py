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

    Raises:
        RuntimeError: if the default configuration cannot be read.
    """
    config = ConfigParser()

    # Coerce input into a list of Paths
    if isinstance(configfiles, (Path, str)):
        configfiles = [configfiles]
    elif isinstance(configfiles, list):
        configfiles = [Path(f) for f in configfiles]
    else:
        configfiles = []

    # Read default configuration
    with as_file(DEFAULT_CONFIG_INI) as config_path:
        if not (config_path.exists() and config_path.is_file()):
            raise RuntimeError("Cannot read default config")
        config.read(config_path, encoding="utf-8")

    if len(configfiles) == 0:
        # Read default site config path & user config path
        read_files = config.read(
            filenames=[
                str(dirs.site_config_path / CONFIG_FILE_NAME),
                str(dirs.user_config_path / CONFIG_FILE_NAME),
            ],
            encoding="utf-8",
        )
    else:
        # Read provided config file(s)
        read_files = config.read(filenames=configfiles, encoding="utf-8")

    return config, read_files


def dump_config(config: ConfigParser) -> None:
    """Dump the ConfigParser's configuration to `stdout`.

    Args:
        config: the configuration to dump.

    Raises:
        RuntimeError: if the default configuration file cannot be read
    """
    # Print locations of where this file should go
    with as_file(DEFAULT_CONFIG_INI) as config_path:
        if not (config_path.exists() and config_path.is_file()):
            raise RuntimeError("Cannot read default config")
        print(
            "; For reference, the default configuration is located at `%s`"
            % config_path
        )

    print(
        "; Place this in `%s` for system-wide configuration"
        % (dirs.site_config_path / CONFIG_FILE_NAME)
    )
    print(
        "; Place this in `%s` for your personal configuration"
        % (dirs.user_config_path / CONFIG_FILE_NAME)
    )
    config.write(sys.stdout)
