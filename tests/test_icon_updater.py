"""Test the icon updater."""

import unittest
from configparser import ConfigParser

from i3bar_workspace_icons.configuration import DEFAULT_CONFIG_INI, generate_config
from i3bar_workspace_icons.icon_updater import IconUpdater, remaining_key


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
        for icon_key in self.config["remaining"]:
            with self.subTest(icon_key=icon_key):
                if icon_key == "show":
                    continue
                self.assertEqual(
                    self.icon_updater.remaining_icons.get(icon_key),
                    self.config["remaining"].get(icon_key),
                )

    def test_override_window_class(self) -> None:
        """Test the `override_window_class` method."""
        self.assertEqual(
            self.icon_updater.override_window_class("alacritty", "File - Nvim"),
            "neovim",
        )
        self.assertEqual(
            self.icon_updater.override_window_class("alacritty", "File - VIM"),
            "vim",
        )
        self.assertEqual(
            self.icon_updater.override_window_class("alacritty", "Window Title"),
            "alacritty",
        )
        self.assertEqual(
            self.icon_updater.override_window_class("firefox", "File - Nvim"),
            "firefox",
        )
        self.assertEqual(
            self.icon_updater.override_window_class("firefox", "File - VIM"),
            "firefox",
        )
        self.assertEqual(
            self.icon_updater.override_window_class("firefox", "Window Title"),
            "firefox",
        )

    def test_build_icons_string(self) -> None:
        """Test the `build_icons_string` method."""
        max_icons = self.config.getint("options", "max_icons")

        # Test for 0 icons
        self.assertEqual(
            self.icon_updater.build_icons_string([]),
            "",
        )
        # Test for 1 to N-1 icons
        for i in range(1, max_icons - 1):
            with self.subTest(i=i):
                self.assertEqual(
                    self.icon_updater.build_icons_string(["alacritty"] * i),
                    " " + f"{self.config.get('window_classes', 'alacritty')} " * i,
                )

        # Test for N icons to N + 10 icons (and more)
        for i in range(max_icons, max_icons + 20):
            num_rendered_icons = max_icons - 1
            remaining_icon = self.config.get(
                "remaining", remaining_key(i - max_icons + 1)
            )

            with self.subTest(i=i):
                self.assertEqual(
                    self.icon_updater.build_icons_string(["alacritty"] * i),
                    " "
                    + f"{self.config.get('window_classes', 'alacritty')} "
                    * num_rendered_icons
                    + remaining_icon
                    + " ",
                )


if __name__ == "__main__":
    unittest.main()
