"""Test the icon updater."""

import unittest
from configparser import ConfigParser
from typing import get_args
from unittest.mock import Mock

import i3ipc

from i3bar_workspace_icons.configuration import DEFAULT_CONFIG_INI, generate_config
from i3bar_workspace_icons.icon_updater import (
    IconUpdater,
    RemainingIconKey,
    remaining_key,
)


class TestIconUpdater(unittest.TestCase):
    """Test the icon updater."""

    config: ConfigParser
    icon_updater: IconUpdater

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test class."""
        cls.config, _ = generate_config([str(DEFAULT_CONFIG_INI)])
        cls.icon_updater = IconUpdater(cls.config)

    def test_init_config(self) -> None:
        """Test that the `IconUpdater` class initializes the configuration correctly."""
        # Test override windows
        for option in self.config["override_windows"]:
            with self.subTest(option=option):
                self.assertEqual(
                    self.icon_updater.override_windows[option],
                    self.config["override_windows"].getboolean(option),
                )

        # Test override patterns
        for window_class, pattern in self.config["override_patterns"].items():
            with self.subTest(window_class=window_class, pattern=pattern):
                self.assertEqual(
                    self.icon_updater.override_patterns[pattern],
                    window_class,
                )

        # Test remaining window icons
        for icon_key in get_args(RemainingIconKey):
            with self.subTest(icon_key=icon_key):
                if icon_key == "show":
                    continue
                self.assertEqual(
                    self.icon_updater.remaining_icons.get(icon_key),
                    self.config["remaining"].get(icon_key),
                )

    def test_fetch_window_icon(self) -> None:
        """Test the `override_window_class` method."""
        self.assertEqual(
            self.icon_updater.fetch_window_icon("alacritty", "File - Nvim"),
            self.icon_updater.window_classes.get("neovim"),
        )
        self.assertEqual(
            self.icon_updater.fetch_window_icon("alacritty", "File - VIM"),
            self.icon_updater.window_classes.get("vim"),
        )
        self.assertEqual(
            self.icon_updater.fetch_window_icon("alacritty", "Window Title"),
            self.icon_updater.window_classes.get("alacritty"),
        )
        self.assertEqual(
            self.icon_updater.fetch_window_icon("firefox", "File - Nvim"),
            self.icon_updater.window_classes.get("firefox"),
        )
        self.assertEqual(
            self.icon_updater.fetch_window_icon("firefox", "File - VIM"),
            self.icon_updater.window_classes.get("firefox"),
        )
        self.assertEqual(
            self.icon_updater.fetch_window_icon("firefox", "Window Title"),
            self.icon_updater.window_classes.get("firefox"),
        )

    def test_recursive_config(self) -> None:
        """Test if having recursive overriding patterns will throw an error."""
        self.icon_updater.override_patterns["pattern1"] = "pattern2"
        self.icon_updater.override_patterns["pattern2"] = "pattern1"
        self.icon_updater.override_windows["pattern1"] = True
        self.icon_updater.override_windows["pattern2"] = True
        self.assertRaises(
            RuntimeError,
            self.icon_updater.fetch_window_icon,
            window_class="alacritty",
            window_title="pattern1",
        )

    def test_build_icons_string(self) -> None:
        """Test the `build_icons_string` method."""
        alacritty = Mock(spec=i3ipc.Con)
        alacritty.window_class = "Alacritty"
        alacritty.window_title = "Alacritty"

        # Test for 0 icons

        self.assertEqual(
            self.icon_updater.build_icons_string([]),
            "",
        )

        # Test for 1 to N-1 icons

        for i in range(1, self.icon_updater.max_icons - 1):
            with self.subTest(i=i):
                self.assertEqual(
                    self.icon_updater.build_icons_string([alacritty] * i),
                    " " + f"{self.config.get('window_classes', 'alacritty')} " * i,
                )

        # Test for N icons to N + 10 icons (and more)

        for i in range(self.icon_updater.max_icons, self.icon_updater.max_icons + 20):
            num_rendered_icons = self.icon_updater.max_icons - 1

            remaining_icon = self.config.get(
                "remaining", remaining_key(i - self.icon_updater.max_icons + 1)
            )

            with self.subTest(i=i):
                self.assertEqual(
                    self.icon_updater.build_icons_string([alacritty] * i),
                    " "
                    + f"{self.config.get('window_classes', 'alacritty')} "
                    * num_rendered_icons
                    + remaining_icon
                    + " ",
                )
        pass


if __name__ == "__main__":
    unittest.main()
