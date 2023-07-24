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
INVALID_PAYLOAD = 4000


class PresenceError(Exception):
    """
    An error emitted from Discord. See the [docs](https://discord.com/developers/docs/topics/opcodes-and-status-codes#rpc) for more details.
    """

    def __init__(self, message: object, code: int) -> None:
        super().__init__(message)
        self.code = code


class ClientIDError(PresenceError):
    """
    Invalid client ID.
    """

    def __init__(self) -> None:
        super().__init__("Client ID is invalid", INVALID_PAYLOAD)


class ActivityError(PresenceError):
    """
    Discord rejected the payload because the activity was not in the [correct format](https://discord.com/developers/docs/topics/gateway-events#activity-object).
    """

    def __init__(self, message: object) -> None:
        super().__init__(message, INVALID_PAYLOAD)


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
        Sets the current activity using a dictionary representing a [Discord activity object](https://discord.com/developers/docs/topics/gateway-events#activity-object).

        Raises a `PresenceError` if Discord rejected the payload.
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

        # Check for errors
        reply = self._read()
        if reply.get("evt") != "ERROR":
            return

        message: str = reply["data"]["message"]
        code: int = reply["data"]["code"]

        if code == INVALID_PAYLOAD:
            # Improve readability of the error message if the dictionary is invalid
            prefix = 'child "activity" fails because ['
            if message.startswith(prefix):
                message = message[len(prefix) : -1]
            raise ActivityError(message)

        raise PresenceError(message, code)

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
        try:
            self._send({}, _OpCode.CLOSE)
        finally:
            self._socket._close()

    def _handshake(self) -> None:
        self._send({"v": 1, "client_id": self.client_id}, _OpCode.HANDSHAKE)
        payload = self._read()

        if payload.get("evt") != "READY":
            if payload["code"] == INVALID_PAYLOAD:
                raise ClientIDError()
            raise PresenceError(payload["message"], payload["code"])

    def _read(self) -> dict[str, Any]:
        op, length = self._read_header()
        decoded = self._read_bytes(length).decode("utf-8")
        data = json.loads(decoded)
        return cast(dict[str, Any], data)

    def _read_header(self) -> tuple[int, int]:
        return cast(tuple[int, int], struct.unpack("<ii", self._read_bytes(8)))

    def _read_bytes(self, size: int) -> bytes:
        data = b""
        while size > 0:
            chunk = self._socket._read(size)
            if not chunk:
                raise ConnectionAbortedError(
                    "Connection closed before all bytes were read"
                )
            data += chunk
            size -= len(chunk)
        return data

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
            raise FileNotFoundError("Cannot find a Unix socket to connect to Discord")

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
            raise FileNotFoundError(
                "Cannot find a Windows socket to connect to Discord"
            )

    def _read(self, size: int) -> bytes:
        return self._buffer.read(size)

    def _write(self, data: bytes) -> None:
        self._buffer.write(data)
        self._buffer.flush()

    def _close(self) -> None:
        self._buffer.close()
