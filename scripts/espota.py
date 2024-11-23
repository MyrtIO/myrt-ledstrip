#!/usr/bin/env python3
#
# Original espota.py by Ivan Grokhotkov:
# https://gist.github.com/igrr/d35ab8446922179dc58c
#
# Modified since 2015-09-18 from Pascal Gollor (https://github.com/pgollor)
# Modified since 2015-11-09 from Hristo Gochkov (https://github.com/me-no-dev)
# Modified since 2016-01-03 from Matthew O'Gorman (https://githumb.com/mogorman)
# Modified since 2024-10-23 from Mikhael Khrustik (https://github.com/mishamyrt)
#
# This script will push an OTA update to the ESP
# use it like: python3 espota.py -i <ESP_IP_address> -I <Host_IP_address> -p <ESP_port> -P <Host_port> [-a password] -f <sketch.bin>
# Or to upload SPIFFS image:
# python3 espota.py -i <ESP_IP_address> -I <Host_IP_address> -p <ESP_port> -P <HOST_port> [-a password] -s -f <spiffs.bin>
#
# Changes
# 2015-09-18:
# - Add option parser.
# - Add logging.
# - Send command to controller to differ between flashing and transmitting SPIFFS image.
#
# Changes
# 2015-11-09:
# - Added digest authentication
# - Enhanced error tracking and reporting
#
# Changes
# 2016-01-03:
# - Added more options to parser.
#
# Changes
# 2024-10-23:
# - Added progress bar
# - Improved UX
# - Updated to Python 3

from __future__ import print_function, annotations
import socket
import sys
import os
import secrets
import asyncio
import hashlib
from typing import Callable
from enum import Enum
import argparse
import logging
import hashlib
import random
import time

# Commands
COMMAND_FLASH = 0
COMMAND_SPIFFS = 100
COMMAND_AUTH = 200

PACKET_SIZE = 512

Address = tuple[str, int]

class Progress:
    """Progress bar printer"""
    _value: float
    _title: str
    _bar_width: int
    _fill_char: str
    _empty_char: str

    def __init__(self,
                operation: str,
                fill_char: str = "█",
                empty_char: str = "░",
                bar_width: int = 60):
        self._title = operation
        self._fill_char = fill_char
        self._empty_char = empty_char
        self._bar_width = bar_width

    def start(self):
        """Starts the progress bar"""
        self.update(0)

    def update(self, value: float):
        """Updates the progress bar value"""
        self._value = value
        self._print_progress(self._value)

    def finish(self, message: str):
        """Finishes the progress bar, prints the final message"""
        self._print_progress(1)
        padding = os.get_terminal_size().columns - len(message) - 1
        message = f"{message}{' ' * padding}"
        print(message)

    def _print_progress(self, value: float):
        if value < 0:
            value = 0
        if value >= 1:
            value = 1
        fill_width = int(round(self._bar_width * value))
        padding_width = self._bar_width - fill_width

        progress_bar = f"{self._fill_char * fill_width}{self._empty_char * padding_width}"
        print(f"{self._title}: {progress_bar} {value*100:.1f}%", end="\r", flush=True)

class ImageType(Enum):
    """Supported image types"""
    FLASH = COMMAND_FLASH
    SPIFFS = COMMAND_SPIFFS

class ImageFile:
    """Splits file into chunks"""
    _file: bytes
    _chunk_size: int
    _offset: int
    _md5: str
    _type: ImageType

    def __init__(self, image_type: ImageType, file: bytes, chunk_size: int = PACKET_SIZE):
        self._file = file
        self._chunk_size = chunk_size
        self._type = image_type
        self._offset = 0
        self._md5 = hashlib.md5(file).hexdigest()

    @property
    def end_of_file(self) -> bool:
        """Returns true if end of file reached"""
        return self._offset >= self.size

    @property
    def offset(self) -> int:
        """Returns current offset"""
        return self._offset

    @property
    def size(self) -> int:
        """Returns file size"""
        return len(self._file)

    @property
    def md5(self) -> str:
        """Returns file md5"""
        return self._md5

    @property
    def type(self) -> ImageType:
        """Returns image type"""
        return self._type

    def next_chunk(self) -> bytes:
        """Retrieves next chunk"""
        chunk_end = 0
        if self._offset + self._chunk_size <= len(self._file):
            chunk_end = self._offset + self._chunk_size
        elif self._offset < len(self._file):
            chunk_end = len(self._file)
        else:
            raise ValueError("end of file reached")
        chunk = self._file[self._offset:chunk_end]
        self._offset += len(chunk)
        return chunk

class OTAError(Exception):
    """Returns when there is a problem during the OTA process"""

def _to_md5(message: str) -> str:
    return hashlib.md5(message.encode()).hexdigest()

def _calculate_auth_challenge(password: str, nonce: str) -> tuple[str, str]:
    cnonce = _to_md5(secrets.token_hex(32))
    challenge = _to_md5(f"{_to_md5(password)}:{nonce}:{cnonce}")
    return (challenge, cnonce)

def _format_invitation(image: ImageFile, port: int) -> str:
    return f"{image.type.value} {port} {image.size} {image.md5}\n"

def _format_authentication(password: str, nonce: str) -> str:
    challenge, cnonce = _calculate_auth_challenge(password, nonce)
    return f"{COMMAND_AUTH} {challenge} {cnonce}\n"

def _try_invite(
        remote: Address,
        local_port: int,
        file: ImageFile,
        password: str = None) -> None:
    """Invite ArduinoOTA client"""
    invitation = _format_invitation(file, local_port)
    stream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    stream.sendto(invitation.encode(), remote)
    stream.settimeout(1.5)
    try:
        data = stream.recv(128).decode()
    except socket.timeout as exc:
        stream.close()
        raise OTAError('invitation timeout') from exc
    if data.find("OK") >= 0:
        stream.close()
        return
    # Authentication
    if data.startswith('AUTH'):
        if password is None:
            raise OTAError('no password provided, but board requires it')
        nonce = data.split()[1]
        authentication = _format_authentication(password, nonce)
        stream.sendto(authentication.encode(), remote)
        stream.settimeout(5)
        try:
            data = stream.recv(32).decode()
        except socket.timeout as exc:
            stream.close()
            raise OTAError('authentication timeout') from exc
        if data != "OK":
            stream.close()
            raise OTAError('authentication failed')
    else:
        stream.close()
        raise OTAError(f'bad answer: {data}')

async def invite(
        remote: Address,
        local_port: int,
        file: ImageFile,
        password: str = None,
        attempts: int = 5,
        loop: asyncio.AbstractEventLoop = None) -> None:
    """Invites ArduinoOTA client to port"""
    if loop is None:
        loop = asyncio.get_event_loop()
    for i in range(attempts):
        try:
            await loop.run_in_executor(None, _try_invite, remote, local_port, file, password)
            return
        except OTAError as exc:
            if i == attempts - 1:
                raise exc
    raise OTAError("failed to invite")

def _random_port() -> int:
    return random.randint(500, 32766)

async def update_ota(
        remote: Address,
        server: Address,
        file: ImageFile,
        report: Callable[[float], None],
        password: str = None,
        client_timeout: float = 3) -> None:
    """Updates ArduinoOTA client firmware"""
    update_done = asyncio.Event()
    client_connected = asyncio.Event()
    async def handle_connection(reader, writer):
        report(0)
        client_connected.set()
        while not file.end_of_file:
            chunk = file.next_chunk()
            writer.write(chunk)
            try:
                async with asyncio.timeout(5):
                    resp = await reader.read(32)
            except asyncio.TimeoutError as exc:

                raise OTAError("timeout on chunk write") from exc
            if len(resp) == 0:
                raise OTAError("no response on chunk write")
            written = int(resp.decode("utf-8"))
            if written < len(chunk):
                raise OTAError(f"chunk write failed. Length mismatch: {written} < {len(chunk)}")
            report(file.offset / file.size)

        try:
            async with asyncio.timeout(5):
                resp = await reader.read(32)
        except asyncio.TimeoutError as exc:
            raise OTAError("final status is not received") from exc
        status = resp.decode("utf-8")
        if status.find("E") >= 0:
            raise OTAError("board failed to update firmware")
        elif status.find("O") >= 0:
            update_done.set()

    server_host, server_port = server
    server = await asyncio.start_server(handle_connection, server_host, server_port)
    # await invite(remote, server_port, file, password)
    try:
        async with asyncio.timeout(client_timeout):
            await client_connected.wait()
    except asyncio.TimeoutError as exc:
        raise OTAError("client connection timeout") from exc
    await update_done.wait()
    server.close()

def _parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    # Connection
    parser.add_argument("-i", "--ip",
        help="ArduinoOTA client IP address",
        type=str,
        dest="client_ip",
        metavar="",
        required=True)
    parser.add_argument("-p", "--port",
        help="ArduinoOTA client port. Default: 2040",
        type=int,
        dest="client_port",
        metavar="",
        default=2040)
    parser.add_argument("-I", "--host_ip",
        help="Host IP address",
        type=str,
        metavar="",
        default="0.0.0.0")
    parser.add_argument("-P", "--host_port",
        help="Host port. Default: random",
        metavar="",
        type=int,
        default=None)
    # Authentication
    parser.add_argument("-a", "--auth",
        help="Authentication password",
        metavar="",
        type=str,
        default=None)
    # Image
    parser.add_argument("-f", "--file",
        help="Image file",
        type=str,
        metavar="",
        default=None
    )
    parser.add_argument("-s", "--spiffs",
        help="Update only SPIFFS image and do not flash the module",
        type=str,
        metavar="",
        default=None
    )

    return parser.parse_args(args)

def _die(message: str) -> None:
    sys.stderr.write(message + "\n")
    sys.exit(1)

async def main(argv: list[str]) -> None:
    """Entrypoint"""
    if len(argv) < 2:
        _die("Not enough arguments. Try --help")
    args = _parse_args(argv[1:])
    if args.host_port is None:
        args.host_port = _random_port()
    client = (args.client_ip, args.client_port)
    host = (args.host_ip, args.host_port)

    if args.spiffs is None and args.file is None:
        _die("Please specify either --spiffs or --file")
    if args.spiffs is not None:
        file_path = args.spiffs
        image_type = ImageType.SPIFFS
    else:
        file_path = args.file
        image_type = ImageType.FLASH

    try:
        with open(file_path, 'rb') as file:
            image = ImageFile(image_type, file.read())
    except OSError as exc:
        _die(f"Failed to open file {file_path}: {exc}")

    progress_bar = Progress("Uploading", bar_width=60)
    def report(progress: float) -> None:
        if progress == 1.0:
            progress_bar.finish("Upload completed")
            print("Waiting for board to confirm...")
        else:
            progress_bar.update(progress)
    
    print("Inviting board...")
    try:
        await invite(client, host[1], image, args.auth)
    except OTAError as exc:
        _die(f"Failed to invite board: {exc}")
    print("Updating image...")
    progress_bar.start()
    try:
        await update_ota(client, host, image, report)
    except OTAError as exc:
        _die(f"Failed to update image: {exc}")
    print("Success!")


if __name__ == '__main__':
    try:
        asyncio.run(main(sys.argv))
    except KeyboardInterrupt:
        pass
    except OTAError as exc:
        print(exc)
# end if
