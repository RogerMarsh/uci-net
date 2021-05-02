# uci_mixin.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Universal Chess Interface (UCI) communication with chess engine driver.

"""
# UCIMixin was originally in UCI (uci.py), called UCIDriver, as the extension of
# Provider class for chess engines, but it should be available independently.

import subprocess
from collections import deque
import shlex

# Use the multiprocessing API for threading
from multiprocessing import dummy

# So subprocess can be told to use parent's console on Microsoft Windows.
import sys
_win32_platform = sys.platform == 'win32'
del sys


class UCIError(Exception):
    pass


class UCIMixin(object):
    """Implement communication with chess engine processes.

    """
    def init_mixin(self, to_ui_queue, ui_name):
        """Create a database state instance."""
        self.to_ui_queue = to_ui_queue
        self.ui_name = ui_name
        self.engine_process = None
        self.engine_process_responses = deque()
        self._engine_response_handler = None
        self._termination_handler = None
        self._terminators = {
            'uciok', 'bestmove', 'copyprotection', 'registration', 'readyok'}
        self._command_done = dummy.Event()
        self._responses_collected = dummy.Event()

        # Used to decide polling strategy for responses.
        self._commands_sent = deque()

    def start_engine(self, path, args):
        """Set command to start engine."""
        if self.engine_process:
            return

        if _win32_platform:
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

    def quit_engine(self):
        """Set command to quit engine."""
        try:
            outs, errs = self.engine_process.communicate('quit', timeout=15)
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
        t = self._terminators
        while e.poll() is None:
            response = e.stdout.readline().rstrip()
            if not response:
                continue
            r.append(response)
            if r[-1].split(maxsplit=1)[0] in t:
                self._command_done.set()
                self._responses_collected.wait()
                self._responses_collected.clear()

    def _process_response_terminations(self):
        """"""
        cs = self._commands_sent
        epr = self.engine_process_responses
        tuq = self.to_ui_queue
        while True:
            self.wait_for_responses()
            response = []
            while len(cs):
                command_sent = cs.popleft()
                if command_sent in ('stop', 'uci'):
                    self.collect_more_responses()
                    self.wait_for_responses_timeout(timeout=0.5)
            while len(epr):
                response.append(epr.popleft())
            self.collect_more_responses()
            tuq.put((self.ui_name, response))

    def send_to_engine(self, command):
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
