# uci_driver.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Run a chess engine and have it analyse positions from a user interface.

The chess engine must support the Universal Chess Interface (UCI).

"""

import subprocess
from collections import deque
import shlex

# Use the multiprocessing API for threading
from multiprocessing import dummy

import sys

from .engine import CommandsFromEngine, CommandsToEngine

_TERMINATE_PENDING = frozenset((CommandsToEngine.uci, CommandsToEngine.stop))


class UCIDriver(object):
    """Give commands to chess engine and collect responses using UCI protocol.

    """
    def __init__(self, to_ui_queue, ui_name):
        """Initialize with queue for responses to named user interface."""
        self.to_ui_queue = to_ui_queue
        self.ui_name = ui_name
        self.engine_process = None
        self.engine_process_responses = deque()
        self._engine_response_handler = None
        self._termination_handler = None
        self._command_done = dummy.Event()
        self._responses_collected = dummy.Event()

        # Keep a note of each command in a batch so when the engine responses
        # appear futher short waits for responses can be done for optional
        # extra responses if necessary.  This is for the uci and stop commands
        # to engines.
        self._commands_sent = deque()

    def start_engine(self, path, args):
        """Start engine specified in path passing argsto engine.

        path will be the command to run the engine directly from the current
        process, or the command to run tcp_client.py when using an engine over
        TCP.

        args will be passed to the process run using path: engine command-line
        options when run directly form the current process, or the name of the
        engine returned by the 'id name' command when the engine is accessed
        via TCP using the tcp_client and tcp_server modules.  The tcp_server
        module is obliged to ignore any arguments because the engine will
        already be running and serving more than one client.

        The format of args when passed over TCP is:

        //<host>:<port>?name=<engine name>

        """
        if self.engine_process:
            return

        # Use parent's console on Microsoft Windows
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            startupinfo = None

        self._engine_response_handler = dummy.Process(
            target=self._engine_response_catcher)
        self._engine_response_handler.daemon = True
        self._termination_handler = dummy.Process(
            target=self._process_response_terminations)
        self._termination_handler.daemon = True
        if args:
            args = shlex.split(args)
            args.insert(0, path)
        else:
            args = [path]
        self.insert_remote_hostname_port(args)
        self.engine_process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
            startupinfo=startupinfo)
        self._engine_response_handler.start()
        self._termination_handler.start()

        return True

    def insert_remote_hostname_port(self, args):
        """Assume args contains a valid command line and do nothing.

        Default action is do nothing which causes UCI chess engine specified in
        args to be run directly on localhost, not via tcp.

        See uci_driver_over_tcp for the version of this method which contacts
        the engine via TCP: in class UCIDriverOverTCP.

        """

    def quit_engine(self):
        """Send UCI quit to engine and kill engine process after 15 seconds."""
        try:
            outs, errs = self.engine_process.communicate(
                CommandsToEngine.quit_, timeout=15)
        except subprocess.TimeoutExpired:
            self.engine_process.kill()
            outs, errs = self.engine_process.communicate()
        self.engine_process = False
        return outs

    def _engine_response_catcher(self):
        """Catch chess engine responses and interrupt client on terminations.

        The termination commands from the engine are uciok, bestmove,
        copyprotection, registration, and readyok.

        This interrupt rule is not compatible with clients implicitly stopping
        one search by starting another.  However a client can interrupt another
        client's search and start their own.

        go commands are expected to use subcommands which guarantee the search
        will terminate.  In particular 'go depth <n>' is fine but 'go infinite'
        is not.

        """
        e = self.engine_process
        r = self.engine_process_responses
        t = CommandsFromEngine.terminators
        while e.poll() is None:

            # On Windows 10 Ctrl C while waiting for a response from the UCI
            # engine will often give a ValueError exception citing I/O
            # operation on closed file.  See startupinfo in start_engine().  
            response = e.stdout.readline().rstrip()

            if not response:
                continue
            r.append(response)
            if r[-1].split(maxsplit=1)[0] in t:
                self._command_done.set()
                self._responses_collected.wait()
                self._responses_collected.clear()

    def _process_response_terminations(self):
        """Process chess engine responses sent by _engine_response_catcher().
        """
        cs = self._commands_sent
        epr = self.engine_process_responses
        tuq = self.to_ui_queue
        while True:
            self.wait_for_responses()
            response = []
            while len(cs):
                command_sent = cs.popleft()
                if command_sent in _TERMINATE_PENDING:
                    self.collect_more_responses()
                    self.wait_for_responses_timeout(timeout=0.5)
            while len(epr):
                response.append(epr.popleft())
            self.collect_more_responses()
            tuq.put((self.ui_name, response))

    def send_to_engine(self, command):
        """Write command to engine's stdin and note for reply processing."""
        e = self.engine_process.stdin
        e.write(command)
        e.write('\n')
        e.flush()
        self._commands_sent.append(command.split(None, maxsplit=1)[0])

    def wait_for_responses(self):
        self._command_done.wait()
        self._command_done.clear()

    def collect_more_responses(self):
        self._responses_collected.set()

    def wait_for_responses_timeout(self, timeout=0.5):
        """Put a timeout on replies which may never be sent.

        The copy protection and registration replies in particular, which
        should be almost immediate if they happen at all.

        This method is not intended to be used to poll for replies.  Send an
        'isready' command to the engine and let the 'readyok' reply flush the
        replies of interest through the _engine_response_catcher thread.

        """
        if self._command_done.wait(timeout):
            self._command_done.clear()
            return True
