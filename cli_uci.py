# cli_uci.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Universal Chess Interface (UCI) commands in cmd module style."""

from .engine import Engine


class CLIUCI(object):
    """Command Line Interface for chess engines using UCI.

    """

    def __init__(self, cli, **k):
        """Instantiate a command line interface."""
        super().__init__(cli, **k)
        self._engine = Engine()

    def help_uci(self):
        hs = (
            'uci',
            'Tell engine to use UCI.',
            'The engine responds with command sequence (ignoring arguments):',
            'id [ option ... ] uciok',
            'The engine expects to be killed if uciok response takes too long.',
            )
        self.write_cmd_response(hs)

    def help_debug(self):
        hs = (
            'debug [ on | off ]',
            'Turn engine debug mode on and off.',
            'The engine responds with additional info commands when debug',
            'mode is on.',
            'Debug mode is expected to be off by default.',
            )
        self.write_cmd_response(hs)

    def help_isready(self):
        hs = (
            'isready',
            'Synchronize with the engine.',
            'The engine responds with command sequence:',
            'readyok',
            'The engine should respond when ready to accept further commands.',
            'This command is required once after start-up commands to ensure',
            'completion before doing searches.  If the command is used while',
            'the engine is searching the readyok response should be immediate',
            'without stopping the search.',
            'The engine expects this command to be used as a ping to find out',
            'if it is still alive.',
            )
        self.write_cmd_response(hs)

    def help_setoption(self):
        hs = (
            'setoption name <id> [ value <x> ]',
            'Tell engine to set value of option <id> to value <x>.',
            '<id> and <x> should not be case sensitive and can include spaces.',
            'Engines should have sent option commands when responding to the',
            'uci command to specify the acceptable <id> and <x> values.',
            'Engines should avoid substrings "name" and "value" in <id> and',
            '<x> to avoid ambiguity.',
            )
        self.write_cmd_response(hs)

    def help_register(self):
        hs = (
            'register { later | name <x> | code <y> }',
            'Tell engine registration will be done later or to attempt it now.',
            'The engine responds with command sequence:',
            'registration checking',
            'registration { ok | error }',
            'This command should always be used if "registration error" was',
            'sent at engine start-up.',
            )
        self.write_cmd_response(hs)

    def help_ucinewgame(self):
        hs = (
            'ucinewgame',
            'Tell engine the next search will be from a different game.',
            'The isready command should be the next command, and the position',
            'and go commands to start the search should be delayed until the',
            'readyok response has been received.',
            )
        self.write_cmd_response(hs)

    def help_position(self):
        hs = (
            'position { fen <fenstring> | startpos } moves <move1> ... <movei>',
            'Tell engine to setup position and play moves on internal board.',
            'This command should be part of the sequence (engine responses in',
            ' UPPER case), omitting arguments:',
            'ucinewgame isready READYOK position go [ INFO ... ]'
            'When the search, started by go, is finished for any reason, the',
            'engine sends the bestmove command.',
            )
        self.write_cmd_response(hs)

    def help_go(self):
        hs = (
            'go <subcommand> [ <x> ... ] [ <subcommand> [ <x> ... ] ... ]',
            'Tell engine to start search on current position.',
            'This command should be part of the sequence, omitting arguments:',
            'ucinewgame isready READYOK position go [ INFO ... ]',
            '(engine responses in UPPER case)',
            'Engine sends bestmove command when the search is finished.',
            'The subcommands which have no <x> argument are:',
            'ponder infinite',
            'The subcommands which have a single <x> argument are:',
            'wtime btime winc binc movestogo depth nodes mate movetime',
            'The subcommands which have a repeatable <x> argument are:',
            'searchmoves',
            'The ponder subcommand tells the engine that the last move in the',
            'the position command is the ponder move.',
            )
        self.write_cmd_response(hs)

    def help_stop(self):
        hs = (
            'stop',
            'Tell engine to stop search as soon as possible.',
            'The engine responds with command sequence (ignoring arguments):',
            'bestmove',
            'Engine sends bestmove command whenever a search is finished,',
            'not just when engine is told to stop.',
            )
        self.write_cmd_response(hs)

    def help_ponderhit(self):
        hs = (
            'ponderhit',
            'Tell engine the ponder move has been played.',
            'The engine switches to normal mode and continues the search.',
            )
        self.write_cmd_response(hs)

    def help_quit(self):
        hs = (
            'quit',
            'Kill the engine as soon as possible.',
            )
        self.write_cmd_response(hs)

    def do_uci(self, arg):
        """UCI uci."""
        if self.not_connected():
            return False
        self.client.add_command(('uci', dict()))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        self._engine.process_engine_response(self.client.response)
        return False

    def do_debug(self, arg):
        """UCI debug."""
        if self.not_connected():
            return False
        self.client.add_command(('debug', dict(string=arg)))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        return False

    def do_isready(self, arg):
        """UCI isready."""
        if self.not_connected():
            return False
        self.client.add_command(('isready', dict()))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        self._engine.process_engine_response(self.client.response)
        return False

    def do_setoption(self, arg):
        """UCI setoption."""
        if self.not_connected():
            return False
        self.client.add_command(('setoption', dict(string=arg)))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        return False

    def do_register(self, arg):
        """UCI register."""
        if self.not_connected():
            return False
        self.client.add_command(('register', dict(string=arg)))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        return False

    def do_ucinewgame(self, arg):
        """UCI ucinewgame."""
        if self.not_connected():
            return False
        self.client.add_command(('ucinewgame', dict()))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        return False

    def do_position(self, arg):
        """UCI position."""
        if self.not_connected():
            return False
        self.client.add_command(('position', dict(string=arg)))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        return False

    def do_go(self, arg):
        """UCI go."""
        if self.not_connected():
            return False
        self.client.add_command(('go', dict(string=arg)))

        # Clear the old engine snapshot as late as possible.
        # Hook in do_request() which follows?
        self._engine.initialize_info_snapshot()
        
        self.client.do_request()
        #self.write_client_response(self.client.response)
        self._engine.process_engine_response(self.client.response)
        pvg = self._engine.snapshot.pv_group
        r = []
        for k in sorted(pvg):
            score = ''.join((pvg[k].get('score', {}).get('cp', ''), '\t'))
            pv = pvg[k].get('pv', [''])[0]
            r.append(''.join((score, pv)))
        self.write_cmd_response(r)
            
        return False

    def do_stop(self, arg):
        """UCI stop."""
        if self.not_connected():
            return False
        self.client.add_command(('stop', dict()))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        return False

    def do_ponderhit(self, arg):
        """UCI ponderhit."""
        if self.not_connected():
            return False
        self.client.add_command(('ponderhit', dict()))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        return False

    def do_quit(self, arg):
        """UCI quit."""
        if self.not_connected():
            return False
        self.client.add_command(('quit', dict()))
        self.client.do_request()
        #self.write_client_response(self.client.response)
        return False

    def write_client_response(self, response):
        """Format and write the response to the client."""
        self.write_cmd_response(('BEGIN response block',))
        for r in response:
            self.write_cmd_response((' '.join(('***', r[0], repr(r[1]))),))
            if len(r[2]):
                self.write_cmd_response(r[2])
        self.write_cmd_response(('END response block',))
