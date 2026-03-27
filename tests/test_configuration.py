"""Test configuration for the application."""

import unittest
from importlib.resources import as_file
from pathlib import Path
from tempfile import TemporaryFile

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

    def test_generate_config(self) -> None:
        """Test that the `generate_config` function works."""
        with as_file(DEFAULT_CONFIG_INI) as default_config_path:
            config, read_files = generate_config(default_config_path)
            self.assertEqual(len(read_files), 1)
            self.assertEqual(Path(read_files[0]), default_config_path)

        with TemporaryFile("w+") as fp:
            # Write to the temporary file
            config.write(fp)
            fp.seek(0)
            # Compare the contents of the temporary file with the default config
            self.assertEqual(fp.read(), DEFAULT_CONFIG_INI.read_text())

    def test_dump_config(self) -> None:
        """Test that the `dump_config` function doesn't raise an exception."""
        with as_file(DEFAULT_CONFIG_INI) as default_config_path:
            config, _ = generate_config(default_config_path)
            dump_config(config)


if __name__ == "__main__":
    unittest.main()
