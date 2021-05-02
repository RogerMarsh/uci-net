# tcp_server.py
# Copyright 2017 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

# The start point for this module is the sample code in Python 3.6.1 module
# documentation for asyncio at 18.5.5.7.2. TCP echo server using streams.

"""Run a chess engine for a remote client.

The chess engine must support the Universal Chess Interface (UCI).

This server is intended for analysing positions rather than playing games.

"""

import sys
import asyncio
import multiprocessing
import os
from ast import literal_eval

from .uci_driver import UCIDriver
from .engine import (
    CommandsToEngine,
    ReservedOptionNames,
    GoSubCommands,
    PositionSubCommands,
    CommandsFromEngine,
    SetoptionSubCommands,
    )

UCI_ENGINE_LISTEN_HOSTNAME = '0.0.0.0'


# This side of "if __name__ == '__main__'" so multiprocessing.Process() target
# reference works on Microsoft Windows.
def run_driver(to_driver_queue, to_ui_queue, path, args, ui_name):
    """Start UCI chess engine and enter loop sending queued resuests to engine.
    """
    driver = UCIDriver(to_ui_queue, ui_name)
    try:
        driver.start_engine(path, args)
        to_driver_queue.put(CommandsToEngine.uci)
    except:
        to_ui_queue.put(('start failed', (ui_name,)))
        return

    # On FreeBSD, etc?, KeyboardInterrupts do not interrupt the <queue>.get()
    # after a connection has been made and terminated.  On Microsoft Windows
    # the get() is always interrupted.  Slightly annoying and confusing when
    # run from command lines in different environments.
    # Add try clause to stop the meaningless exception trace on Windows.
    try:
        while True:
            command = to_driver_queue.get()
            if command == CommandsToEngine.quit_:
                break
            driver.send_to_engine(command)
    except KeyboardInterrupt:
        pass

    driver.quit_engine()


if __name__ == '__main__':


    @asyncio.coroutine
    def handle_client_uci_commands(reader, writer):
        data = yield from reader.read()
        message = data.decode()

        commands = literal_eval(message)
        if commands[-1] == CommandsToEngine.uci:

            # Normal action is start engine and issue 'uci' command.
            # Server does this at startup so check that client is asking for
            # started engine and return the 'uciok' block sent by the engine
            # at startup.
            if commands[0].endswith(engine_name):
                writer.write(repr(uciok_item).encode())

        elif commands[-1] == CommandsToEngine.isready:

            # Normal action is prepare for 'setoption'(MultiPV) 'position' and
            # 'go' commands with 'ucinewgame' and 'clear hash'.
            # Postpone the 'isready' block until the 'go' block arrives.
            writer.write(
                repr((engine_name, [CommandsFromEngine.readyok])).encode())

        elif commands[-1].split(maxsplit=1)[0] == CommandsToEngine.go:

            # Do postponned 'ucinewgame' and 'clear hash' commands followed by
            # 'go' block; waiting for 'readyok' and 'bestmove' commands from
            # engine after 'ucinewgame' and 'go' commands to engine.
            to_driver_queue.put(CommandsToEngine.ucinewgame)
            to_driver_queue.put(CommandsToEngine.isready)
            while True:
                n, c = uci_drivers_reply.get()
                if c[-1].split(maxsplit=1)[0] == CommandsFromEngine.readyok:
                    break
            to_driver_queue.put(
                ' '.join(
                    (CommandsToEngine.setoption,
                     SetoptionSubCommands.name,
                     ReservedOptionNames.clear_hash)))
            for c in commands:
                to_driver_queue.put(c)
            reply = []
            while True:
                n, c = uci_drivers_reply.get()
                reply.extend(c)
                if c[-1].split(maxsplit=1)[0] == CommandsFromEngine.bestmove:
                    break
            reply = repr((engine_name, reply))
            writer.write(reply.encode())

        yield from writer.drain()

        writer.close()


    class UCIServer:
        """Capture server process parameters from command line.

        The process running the second and subsequent chess engines will have
        to override the default listen port.

        The remote hosts allowed to use this server can be restricted by giving
        a list of hostnames in allowed_callers.  By default any host may use
        the server.

        """
        listen_port = 11111
        allowed_callers = ()

        def __init__(self, listen_port=None, allowed_callers=None):
            if listen_port is not None:
                self.listen_port = listen_port
            if isinstance(allowed_callers, str):
                self.allowed_callers = allowed_callers,
            elif allowed_callers is not None:
                self.allowed_callers = tuple(allowed_callers)


    if len(sys.argv) > 4:
        uciserver = UCIServer(listen_port=sys.argv[1],
                              allowed_callers=sys.argv[2])
        program_file_name = sys.argv[3]
        args = sys.argv[4:]
    elif len(sys.argv) > 3:
        uciserver = UCIServer(listen_port=sys.argv[1],
                              allowed_callers=sys.argv[2])
        program_file_name = sys.argv[3]
        args = None
    elif len(sys.argv) > 2:
        uciserver = UCIServer(listen_port=sys.argv[1])
        program_file_name = sys.argv[2]
        args = None
    elif len(sys.argv) > 1:
        uciserver = UCIServer()
        program_file_name = sys.argv[1]
        args = None
    else:
        sys.stdout.write(''.join(
            ('A path to an UCI chess engine must be given.\n',
             'Usage:\n\n',
             'python[version] -m uci.tcp_driver ',
             '[port] [allowed callers] ',
             'path [options]\n\n',
             "See chess engine documentation for 'options'.\n",
             "'allowed callers' is comma separated hostname list.\n",
             )))
        sys.exit()

    # Avoid "OSError: [WinError 535] Pipe connected"  at Python3.3 running
    # under Wine on FreeBSD 10.1 by disabling the UCI functions.
    # Assume all later Pythons are affected because they do not install
    # under Wine at time of writing.
    # The OSError stopped happening by wine-2.0_3,1 on FreeBSD 10.1 but
    # get_nowait() fails to 'not wait', so ChessTab never gets going under
    # wine at present.  Leave alone because it looks like the problem is
    # being shifted constructively.
    # At Python3.5 running under Wine on FreeBSD 10.1, get() does not wait
    # when the queue is empty either, and ChessTab does not run under
    # Python3.3 because it uses asyncio: so no point in disabling.
    #try:
    #    uci_drivers_reply = multiprocessing.Queue()
    #except OSError:
    #    uci_drivers_reply = None
    uci_drivers_reply = multiprocessing.Queue()

    to_driver_queue = multiprocessing.Queue()
    driver = multiprocessing.Process(
        target=run_driver,
        args=(to_driver_queue,
              uci_drivers_reply,
              program_file_name,
              args,
              os.path.splitext(os.path.basename(program_file_name))[0]),
        )
    driver.start()

    # If this done here rather than in run_driver() Contol-c is ignored later.
    #to_driver_queue.put(CommandsToEngine.uci)
    
    uciok_item = uci_drivers_reply.get()
    if uciok_item[0] == 'start failed':
        sys.stdout.write('Unable to start chess engine.\n')
        sys.exit()
    engine_name = ' '.join((CommandsFromEngine.id_,
                            SetoptionSubCommands.name,
                            '',
                            ))
    for i in uciok_item[1]:
        if i.startswith(engine_name):
            engine_name = i.split(None, 2)
            if len(engine_name) == 3:
                engine_name = engine_name[2].strip()
                if uciok_item[1][-1] == CommandsFromEngine.uciok:
                    break
    else:
        sys.stdout.write('Unexpected start-up response from chess engine.\n')
        to_driver_queue.put(CommandsToEngine.quit_)
        sys.exit()

    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle_client_uci_commands,
                                UCI_ENGINE_LISTEN_HOSTNAME,
                                uciserver.listen_port,
                                loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed or termination
    sys.stdout.write(
        'Serving {} on {}\n'.format(engine_name,
                                    server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
    sys.stdout.write('\nClosed\n')

    # Terminate the driver
    driver.terminate()
    driver.join(10)
