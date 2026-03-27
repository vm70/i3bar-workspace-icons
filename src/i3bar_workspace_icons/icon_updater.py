"""The icon updater class that handles fetching and setting the workspace icons."""

import json
import logging
import sys
from configparser import ConfigParser

import i3ipc

logger = logging.getLogger(__name__)


NO_ICON = ""
"""Signal value for unmatched windows."""


def remaining_key(num_remaining_windows: int) -> str:
    """Get the icon key showing the number of remaining (unmatched) windows.

    Args:
        num_remaining_windows: The number of remaining windows

    Returns:
        The icon key, a string number or "9+"
    """
    if num_remaining_windows < 9:  # noqa: PLR2004
        return str(num_remaining_windows)

    return "9+"


class IconUpdater:
    """The icon updater class that handles fetching and setting the workspace icons."""

    config: ConfigParser
    """The configuration for this icon updater."""
    override_windows: dict[str, bool]
    """Which windows to override the icon for."""
    override_patterns: dict[str, str]
    """What patterns to search for when overriding windows."""
    remaining_icons: dict[str, str]
    """Icons for the number of remaining windows."""
    window_classes: dict[str, str]
    """Mapping from window classes to icons."""
    spacer: str
    """The spacer string."""
    default_unmatched_icon: str = NO_ICON
    """The default icon for unmatched windows."""

    def __init__(self, config: ConfigParser) -> None:
        """Initialize the icon updater.

        Args:
            config: The configuration.
        """
        self.config = config
        self.override_windows = {
            option: config.getboolean("override_windows", option)
            for option in config["override_windows"]
        }
        self.override_patterns = {
            value: key for key, value in config["override_patterns"].items()
        }
        self.remaining_icons = {
            key: value for key, value in config["remaining"].items()
        }
        self.remaining_icons.pop("show")

        self.window_classes = {
            key: value for key, value in config["window_classes"].items()
        }
        self.spacer = " " * config.getint("options", "spacing")

        if self.config.getboolean("unmatched", "show"):
            self.default_unmatched_icon = self.config.get("unmatched", "default")

    def override_window_class(self, window_class: str, window_title: str) -> str:
        """Override the window class if it is a terminal running a terminal application.

        Args:
            window_class: The window class.
            window_title: The window title.

        Returns:
            The new window class
        """
        if not self.override_windows.get(window_class.lower(), False):
            return window_class

        for pattern in self.override_patterns:
            if pattern in window_title:
                return self.override_patterns[pattern]

        return window_class

    def list_windows(self, con: i3ipc.Con) -> list[str]:
        """Recursively list all the windows in a workspace.

        Args:
            con: An i3 container, typically a workspace or window

        Returns:
            The list of window classes
        """
        result = []
        # pyrefly: ignore
        if con.type == "con" and con.window is not None:
            logger.debug("class %s, %s", con.window_class, con.window_title)
            result.append(
                # pyrefly: ignore
                self.override_window_class(con.window_class, con.window_title)
            )

        for node in con.nodes:
            result += self.list_windows(node)

        for floating_node in con.floating_nodes:
            result += self.list_windows(floating_node)

        return result

    def build_icons_string(self, window_classes: list[str]) -> str:
        """Build the string of icons for the given window classes.

        Args:
            window_classes: The list of window classes.

        Returns:
            The string of icons
        """
        if len(window_classes) == 0:
            # No windows means no icons
            return ""

        icons_string = " "  # start with a space
        icon_count = 0
        remaining = 0

        # Populate with N-1 matched icons
        for window_class in window_classes:
            if icon_count >= self.config.getint("options", "max_icons"):
                remaining += 1
                continue

            this_window_icon = self.window_classes.get(
                window_class.lower(), self.default_unmatched_icon
            )
            if this_window_icon != NO_ICON:
                icons_string += this_window_icon + self.spacer
                icon_count += 1
            else:
                remaining += 1

        # Populate with Nth icon (showing how many remaining windows)
        if remaining >= 1 and self.config.getboolean("remaining", "show"):
            icons_string += (
                self.remaining_icons.get(remaining_key(remaining), "") + self.spacer
            )
        return icons_string

    def update_workspace_icons(
        self,
        i3: i3ipc.connection.Connection,
        _e: i3ipc.events.IpcBaseEvent | None = None,
    ) -> None:
        """Update the icons for each workspace.

        This callback function draws the icons in the workspace status bar,
        interacting via the `i3bar workspace protocol`_. It modifies the names
        of the i3bar workspace objects to add icons corresponding to the
        windows in each workspace.

        .. _i3bar workspace protocol: https://i3wm.org/docs/i3bar-workspace-protocol.html

        Args:
            i3: The i3 connection.
            _e: The event, not used.

        """
        # This is the list of currently active workspaces.
        workspace_list = i3.get_tree().workspaces()
        window_classes = {}
        for workspace in workspace_list:
            # pyrefly: ignore
            window_classes[workspace.num] = self.list_windows(workspace)
        logger.debug(window_classes)

        # This is the workspace JSON that we're modifying.
        workspaces = i3.get_workspaces()
        logger.debug(workspaces)

        workspace_ipc_data = [ws.ipc_data for ws in workspaces]
        for ws_ipc in workspace_ipc_data:
            ws_ipc["name"] += self.build_icons_string(window_classes[ws_ipc["num"]])

        workspaces_string = json.dumps(workspace_ipc_data)
        logger.debug(workspaces_string)

        # Flushing the output is needed to update the workspace objects each time
        sys.stdout.write(workspaces_string + "\n")
        sys.stdout.flush()
