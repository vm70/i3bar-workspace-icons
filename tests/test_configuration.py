"""Test configuration for the application."""

import unittest
from importlib.resources import as_file

from i3bar_workspace_icons.configuration import (
    DEFAULT_CONFIG_INI,
    dump_config,
    generate_config,
)


class TestConfiguration(unittest.TestCase):
    """Test configuration."""

    def test_default_config_ini_readable(self) -> None:
        """Test that the `default_config.ini` file in the package is accessible."""
        with DEFAULT_CONFIG_INI.open("r") as fp:
            self.assertTrue(fp.readable())

    def test_dump_config(self) -> None:
        """Test that the `dump_config` function doesn't raise an exception."""
        with as_file(DEFAULT_CONFIG_INI) as default_config_path:
            config, _ = generate_config(default_config_path)
            dump_config(config)


if __name__ == "__main__":
    unittest.main()
