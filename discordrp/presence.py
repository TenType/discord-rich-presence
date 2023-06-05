import json
import os
import socket
import struct
import sys

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Optional, cast
from types import TracebackType
from uuid import uuid4


class _OpCode(IntEnum):
    """
    A list of valid opcodes that can be sent in packets to Discord.
    """

    HANDSHAKE = 0
    FRAME = 1
    CLOSE = 2
    PING = 3
    PONG = 4


SOCKET_NAME = "discord-ipc-{}"


class PresenceError(Exception):
    """
    Errors emitted by the Presence class.
    """


class Presence:
    """
    The main class used to connect to Discord for its rich presence API.
    """

    def __init__(self, client_id: str):
        self.client_id = client_id

        # Connect to Discord IPC
        self._socket: _Socket = (
            _WindowsSocket() if sys.platform == "win32" else _UnixSocket()
        )

        # Send a handshake request
        self._handshake()

    def set(self, activity: Optional[dict[str, Any]]) -> None:
        """
        Sends an activity payload to Discord.
        :param activity: A dictionary of this format:

        ```
        {
            'state': str,
            'details': str,
            'timestamps': {
                'start': int,
                'end': int,
            },
            'assets': {
                'large_image': str,
                'large_text': str,
                'small_image': str,
                'small_text': str,
            },
            'buttons': [
                {
                    'label': str,
                    'url': str,
                },
                {
                    'label': str,
                    'url': str,
                }
            ],
        }
        ```
        One field of either 'state', 'details', or 'timestamps.start' is required.
        """
        payload = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": activity,
            },
            "nonce": str(uuid4()),
        }
        self._send(payload, _OpCode.FRAME)

    def clear(self) -> None:
        """
        Clears the current activity.
        """
        self.set(None)

    def close(self) -> None:
        """
        Closes the current connection.
        This method is automatically called when the program exits using the 'with' statement.
        """
        self._send({}, _OpCode.CLOSE)
        self._socket._close()

    def _handshake(self) -> None:
        self._send({"v": 1, "client_id": self.client_id}, _OpCode.HANDSHAKE)
        data = self._read()

        if data.get("evt") != "READY":
            raise PresenceError(
                "Discord returned an error response after a handshake request"
            )

    def _read(self) -> dict[str, Any]:
        op, length = self._read_header()
        decoded = self._read_bytes(length).decode("utf-8")
        data = json.loads(decoded)
        return cast(dict[str, Any], data)

    def _read_header(self) -> tuple[int, int]:
        return cast(tuple[int, int], struct.unpack("<ii", self._read_bytes(8)))

    def _read_bytes(self, size: int) -> bytes:
        encoded = b""
        while size > 0:
            encoded += self._socket._read(size)
            size -= len(encoded)
        return encoded

    def _send(self, payload: dict[str, Any], op: _OpCode) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        header = struct.pack("<ii", int(op), len(encoded))
        self._socket._write(header + encoded)

    def __enter__(self) -> "Presence":
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> None:
        self.close()


class _Socket(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def _read(self, size: int) -> bytes:
        pass

    @abstractmethod
    def _write(self, data: bytes) -> None:
        pass

    @abstractmethod
    def _close(self) -> None:
        pass


class _UnixSocket(_Socket):
    def __init__(self) -> None:
        pipe = os.path.join(self._get_pipe_path(), SOCKET_NAME)

        # Try to connect to a socket, starting from 0 up to 9
        for i in range(10):
            try:
                self._sock = socket.socket(socket.AF_UNIX)  # type: ignore [attr-defined,unused-ignore]
                self._sock.connect(pipe.format(i))
                break
            except FileNotFoundError:
                pass
        else:
            raise PresenceError("Cannot find a Unix socket to connect to Discord")

    def _get_pipe_path(self) -> str:
        for env in ("XDG_RUNTIME_DIR", "TMPDIR", "TMP", "TEMP"):
            path = os.environ.get(env)
            if path is not None:
                return path

        return "/tmp/"

    def _read(self, size: int) -> bytes:
        return self._sock.recv(size)

    def _write(self, data: bytes) -> None:
        self._sock.sendall(data)

    def _close(self) -> None:
        self._sock.close()


class _WindowsSocket(_Socket):
    def __init__(self) -> None:
        pipe = R"\\.\pipe\\" + SOCKET_NAME

        # Try to connect to a socket, starting from 0 up to 9
        for i in range(10):
            try:
                self._buffer = open(pipe.format(i), "rb+")
                break
            except FileNotFoundError:
                pass
        else:
            raise PresenceError("Cannot find a Windows socket to connect to Discord")

    def _read(self, size: int) -> bytes:
        return self._buffer.read(size)

    def _write(self, data: bytes) -> None:
        self._buffer.write(data)
        self._buffer.flush()

    def _close(self) -> None:
        self._buffer.close()
