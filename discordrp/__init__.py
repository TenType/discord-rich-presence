"""
A lightweight and safe module for creating custom rich presences on Discord.
"""

from .presence import ActivityError, ClientIDError, Presence, PresenceError

__title__ = "discord-rich-presence"
__author__ = "TenType"
__copyright__ = "Copyright 2022-2023 TenType"
__license__ = "MIT"
__version__ = "1.1.0"
__all__ = ("ActivityError", "ClientIDError", "Presence", "PresenceError")
