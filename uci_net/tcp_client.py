# tcp_client.py
# Copyright 2017 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

# The start point for this module is the sample code in Python 3.6.1 module
# documentation for asyncio at 18.5.4.3.1. TCP echo client protocol.

"""Send positions to a remote chess engine for analysis.

The chess engine must support the Universal Chess Interface (UCI).

This client is intended for analysing positions rather than playing games.

Sequences of UCI commands are sent in batches to a server running an UCI chess
engine. The final command in each batch is one which will force a response from
the chess engine and terminate any processing being done by the chess engine in
preparation for the next batch.

Two additional non-UCI commands, 'start' and 'quit', are used to control this
client and the server.

The commands are issued to the client by a chess user interface program which
can process the commands generated by the chess engine and returned via the
server.

The restrictions on the final command in each batch allow multiple clients to
use a server.

The only chess engine option which can be changed by the client is 'MultiPV'
using 'setoption name MultiPV value <n>' where <n> is an integer.

Each 'go' command must be preceded by a 'setoption' command which sets the
'MultiPV' option.

Each 'go' command must be preceded by a 'position' command.

The 'go' command must be like 'go depth <n>' where <n> is an integer.

UCI chess engines expect chess user interface programs to issue 'ucinewgame',
'isready', and 'uci' commands to control it's operation.  There are other such
commands but the restrictions on the final command in each batch allow them to
be ignored.

Chess user interface programs which drive UCI chess engines directly can safely
change the 'Hash' option using 'setoption name Hash value <n>' where <n> is an
integer.  Such commands are removed before sending the batch to a server.

Chess user interface programs may choose to not clear the hash tables before
issuing a 'go' command using 'setoption name Clear Hash'.  The server must
clear the hash tables before each 'go' command is done, so clear hash commands
are removed before sending the batch to a server.  (UCI chess engines expect to
be playing games of chess where retaining the hash tables between each move is
an advantage.  When analysing arbitrary positions it seems best to analyse each
position starting with a clean hash table.)

"""
import sys
from urllib.parse import urlsplit
import asyncio
from ast import literal_eval
import tkinter.messagebox

from .engine import (
    CommandsToEngine,
    ReservedOptionNames,
    GoSubCommands,
    PositionSubCommands,
)

DEFAULT_UCI_ENGINE_LISTEN_PORT = "11111"
DEFAULT_UCI_ENGINE_HOSTNAME = "127.0.0.1"
GO_COMMAND_SEQUENCE = [CommandsToEngine.setoption, CommandsToEngine.position]


class UCIClientProtocol(asyncio.Protocol):
    """Implement communication with chess engine processes over TCP."""

    def __init__(self, message, loop):
        """Initialize instance to send message and receive reply."""
        self.message = message
        self.loop = loop
        self.data_from_engine = []

    def connection_made(self, transport):
        """Write message on transport after connection made."""
        transport.write(self.message.encode())
        try:
            transport.write_eof()
        except ConnectionResetError:
            pass

    def data_received(self, data):
        """Collect response to message."""
        self.data_from_engine.append(data)

    def connection_lost(self, exc):
        """Write response to stdout after connection finished."""
        self.loop.stop()
        response = b"".join(self.data_from_engine).decode().strip()
        if response:
            response = literal_eval(response)
            for text in response[-1]:
                sys.stdout.write(text + "\n")
                sys.stdout.flush()


def run_connection(host, port, message):
    """Connect to UCI chess engine on host:port to commands in message."""
    try:
        loop = asyncio.get_event_loop()
        coro = loop.create_connection(
            lambda: UCIClientProtocol(message, loop), host, port
        )
        loop.run_until_complete(coro)
        loop.run_forever()
    except Exception as exc:
        rep = tkinter.Tk()
        rep.wm_title("UCI TCP Client")
        label = tkinter.Label(
            master=rep,
            wraplength="3i",
            justify=tkinter.LEFT,
            text="".join(
                (
                    "\nA problem has occurred with the UCI ",
                    "chess engine:\n\n",
                    sys.argv[1],
                    "\n\nNo more analysis will be done by ",
                    "this engine until the quit and start ",
                    "actions have been done.\n\nThe reported ",
                    "exception is:\n\n",
                    str(exc),
                    "\n",
                )
            ),
        )
        label.pack()
        rep.mainloop()
        del rep


if __name__ == "__main__":

    url = urlsplit(sys.argv[1])
    if url.port or url.hostname:
        if url.hostname:
            hostname = url.hostname
        else:
            hostname = DEFAULT_UCI_ENGINE_HOSTNAME
        if url.port:
            port = url.port
        else:
            port = DEFAULT_UCI_ENGINE_LISTEN_PORT

    commands_to_engine = [" ".join((CommandsToEngine.start, sys.argv[1]))]
    while True:
        data = sys.stdin.readline()
        if not data:
            break
        command_data = data.split(maxsplit=4)
        command = command_data[0]
        if command == CommandsToEngine.isready:
            if len(commands_to_engine) > 1:
                commands_to_engine.clear()
                continue
            if len(commands_to_engine) == 1:
                if commands_to_engine[0] != CommandsToEngine.ucinewgame:
                    commands_to_engine.clear()
                    continue
            commands_to_engine.append(data.strip())
            run_connection(hostname, port, repr(commands_to_engine))
            commands_to_engine.clear()
        elif command == CommandsToEngine.ucinewgame:
            commands_to_engine.append(data.strip())
        elif command == CommandsToEngine.setoption:
            if len(command_data) == 5:
                if command_data[2] == ReservedOptionNames.MultiPV:
                    commands_to_engine.append(data.strip())
        elif command == CommandsToEngine.go:
            if len(command_data) != 3:
                pass
            elif command_data[1] != GoSubCommands.depth:
                pass
            elif [
                c.split()[0] for c in commands_to_engine
            ] != GO_COMMAND_SEQUENCE:
                pass
            else:
                commands_to_engine.append(data.strip())
                run_connection(hostname, port, repr(commands_to_engine))
            commands_to_engine.clear()
        elif command == CommandsToEngine.position:
            if len(command_data) < 2:
                commands_to_engine.clear()
            elif command_data[1] != PositionSubCommands.fen:
                commands_to_engine.clear()
            elif PositionSubCommands.moves in command_data[-1]:
                commands_to_engine.clear()
            else:
                commands_to_engine.append(data.strip())
        elif command == CommandsToEngine.uci:
            commands_to_engine.append(data.strip())
            run_connection(hostname, port, repr(commands_to_engine))
            commands_to_engine.clear()
        else:
            commands_to_engine.clear()
