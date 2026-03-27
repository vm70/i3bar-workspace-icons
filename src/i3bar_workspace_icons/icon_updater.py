"""The icon updater class that handles fetching and setting the workspace icons."""

import json
import logging
import sys
from configparser import ConfigParser
from typing import Literal

import i3ipc

logger = logging.getLogger(__name__)

NO_ICON = ""
"""Signal value for unmatched windows."""

RemainingIconKey = Literal["0", "1", "2", "3", "4", "5", "6", "7", "8", "9+"]
"""Valid keys in the `[remaining]` section of the config file."""


def remaining_key(num_remaining_windows: int) -> RemainingIconKey:
    """Get the icon key showing the number of remaining (unmatched) windows.

    Args:
        num_remaining_windows: The number of remaining windows

    Returns:
        The icon key, a string number or "9+"

    Raises:
        ValueError: If the number of remaining windows is negative
    """
    # Invalid window count
    if num_remaining_windows < 0:
        raise ValueError("Remaining window count must not be negative")

    # Returning "0"-"8"
    if 0 <= num_remaining_windows < 9:  # noqa: PLR2004
        # pyrefly: ignore
        return str(num_remaining_windows)

    # Returning "9+"
    return "9+"


class IconUpdater:
    """The icon updater class that handles fetching and setting the workspace icons."""

    # [options]

    spacing: int
    """The number of spaces between icons."""
    max_icons: int
    """The maximum number of icons to show per workspace."""
    spacer: str
    """The spacer string, placed between icons."""

    # [override_windows]

    override_windows: dict[str, bool]
    """Dictionary detailing which windows to override the icon for."""

    # [override_patterns]

    override_patterns: dict[str, str]
    """What patterns to search for when overriding windows."""

    # [unmatched]

    show_unmatched: bool
    """Whether to show unmatched windows."""
    unmatched_default_icon: str = NO_ICON
    """The icon (or lack thereof) to show for unmatched windows."""

    # [remaining]

    show_remaining: bool
    """Whether to show the remaining number of windows."""
    remaining_icons: dict[RemainingIconKey, str]
    """Dictionary mapping keys ("1"-"9+") to the number of remaining windows."""

    # [window_classes]

    window_classes: dict[str, str]
    """Mapping from window classes to icons."""

    def __init__(self, config: ConfigParser) -> None:
        """Initialize the icon updater.

        Args:
            config: The configuration.
        """
        # [options]

        self.spacing = config.getint("options", "spacing")
        self.max_icons = config.getint("options", "max_icons")
        self.spacer = " " * self.spacing

        # [override_windows]

        self.override_windows = {
            option: config.getboolean("override_windows", option)
            for option in config["override_windows"]
        }

        # [override_patterns]

        self.override_patterns = {
            value: key for key, value in config["override_patterns"].items()
        }

        # [unmatched]

        self.show_unmatched = config.getboolean("unmatched", "show")
        if self.show_unmatched:
            self.default_unmatched_icon = config.get("unmatched", "default")
        else:
            self.default_unmatched_icon = NO_ICON

        # [remaining]

        self.show_remaining = config.getboolean("remaining", "show")

        # pyrefly: ignore
        self.remaining_icons = {
            key: value for key, value in config["remaining"].items()
        }
        self.remaining_icons.pop("show")  # pyrefly: ignore
        self.window_classes = {
            key: value for key, value in config["window_classes"].items()
        }

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
            if icon_count >= self.max_icons:
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
        if remaining >= 1 and self.show_remaining:
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
