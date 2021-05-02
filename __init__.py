# __init__.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Universal Chess Interface (UCI).
"""

'''from clientserver.provider import Provider
from clientserver.cli_admin import CLIAdmin
from clientserver.cli_user import CLIUser
from clientserver.commands import Commands
from clientserver.services import Services
from clientserver.session import Session
from clientserver.request import Request
from clientserver.respond import Respond

from .cli_uci import CLIUCI
from .uci import UCI
from .engine import CommandsToEngine, CommandsFromEngine, Engine


class Commands(Commands):
    """Extend Commands command definitions with UCI commands."""

    # UCI startup and shutdown commands.

    # engine is used to say which chess engine to start.
    engine = 'engine'

    # stop is a UCI command and it's superclass use is renamed.
    end = 'end'

    # UCI client commands
    uci = CommandsToEngine.uci
    debug = CommandsToEngine.debug
    isready = CommandsToEngine.isready
    setoption = CommandsToEngine.setoption
    register = CommandsToEngine.register
    ucinewgame = CommandsToEngine.ucinewgame
    position = CommandsToEngine.position
    go = CommandsToEngine.go
    stop = CommandsToEngine.stop
    ponderhit = CommandsToEngine.ponderhit
    quit_ = CommandsToEngine.quit_


    def __init__(self):
        """Instantiate a set of client and server commands."""
        super(Commands, self).__init__()

    def _define_commands(self):
        """Define UCI commands.

        Superclass __init__() is responsible for calling _define_commands()
        at appropriate time.

        """
        super(Commands, self)._define_commands()

        # UCI admin commands
        self.admin_commands = frozenset(
            self.admin_commands.union(frozenset(
                (self.uci,
                 self.debug,
                 self.setoption,
                 self.register,
                 self.quit_,
                 self.engine))))
        self.server_commands = frozenset(
            self.finish_commands.union(self.admin_commands))

        # Add the engine command
        self.defined[Commands.engine] = dict(string=(str,))

        # Adjust for command name clashes
        self.defined[Commands.end] = self.defined[super(Commands, self).stop]
        del self.defined[super(Commands, self).stop]
        self.stop_commands = frozenset((self.end,))
        self.initial_commands = frozenset(
            self.start_commands.union(self.stop_commands))
        self.restart_commands = frozenset(
            self.initial_commands.union(self.admin_commands))
        self.continue_commands = frozenset(
            self.stop_commands.union(self.admin_commands))

        # UCI command definitions
        defined = {
            Commands.uci: dict(),
            Commands.debug: dict(string=(str,)),
            Commands.isready: dict(),
            Commands.setoption: dict(string=(str,)),
            Commands.register: dict(string=(str,)),
            Commands.ucinewgame: dict(),
            Commands.position: dict(string=(str,)),
            Commands.go: dict(string=(str,)),
            Commands.stop: dict(),
            Commands.ponderhit: dict(),
            Commands.quit_: dict(),
            }
        self.defined.update(defined)

        # Admin class was given UCI commands as a clientserver samples example.
        # Not here for now.

        # Give Admin class access to UCI commands.
        # (copied from clientserver/commands.py server_client_mode_commands
        #  binding as closely as possible)
        #self.server_commands = frozenset(
        #    self.server_commands.union(
        #        set(self.defined) -
        #        self.initial_commands -
        #        self.server_commands -
        #        self.connect_commands))


class CLIAdmin(CLIUCI, CLIAdmin):
    """Extend CLIAdmin with UCI command processing defined in CLIUCI."""
    
    intro = 'UCI admin command shell.\nType help or ? to list commands.\n'
    prompt = '> '

    # 'stop' is a UCI command, so use 'end' as the server 'stop' command.

    def help_end(self):
        hs = (
            'end',
            'End session.',
            'A server process that has been started is terminated and',
            'connected clients are bumped immediately without warning.',
            )
        self.write_cmd_response(hs)

    def do_end(self, arg):
        """Process arg like 'end'."""
        return self.stop(arg, Commands.end)

    # 'engine' is used to tell provider which chess engine to start.

    def help_engine(self):
        hs = (
            'engine <command to start engine>',
            'Command used to start the chess engine in UCI mode.',
            'The start command will not do anything until an engine has been',
            'specified, and this command cannot be used after starting the',
            'engine.',
            'Examples are:',
            'engine gnuchess --uci',
            'engine stockfish',
            )
        self.write_cmd_response(hs)

    def do_engine(self, arg):
        """Process arg like 'engine'."""
        if self.not_connected():
            return False
        if not arg:
            return False
        self.client.add_command(('engine', dict(string=arg)))
        self.client.do_request()
        return False


class CLIUser(CLIUCI, CLIUser):
    """Extend CLIUser with UCI command processing defined in CLIUCI."""
    
    intro = 'UCI user command shell.\nType help or ? to list commands.\n'
    prompt = '> '


class Services(Services):
    """Services class using the UCI class, a subclass of default provider."""

    # The arguments in **kwargs to be instantiated.
    # See superclass for details
    _resource_class_args = ()

    def __init__(self, provider=UCI, logger_name=False, **kwargs):
        """"""
        super().__init__(provider=provider, logger_name=logger_name, **kwargs)


class Session(Session):
    """Extend Session with UCI commands and use custom Services class."""

    def __init__(self, services=Services, logger_name=False):
        """"""
        super().__init__(services=services, logger_name=logger_name)

    # The engine command.

    def engine(self, string):
        """Call UCI to do 'engine' and return response."""
        return self.services.provider.engine(string)

    # 'stop' is a UCI command, so 'end' is used as the server 'stop' command.
    # Rebind method names to match.

    end = Session.stop

    def stop(self):
        """Call UCI to do 'stop' and return response."""
        return self.services.provider.stop()

    # The rest of the UCI commands.

    def uci(self):
        """Call UCI to do 'uci' and return response."""
        return self.services.provider.uci()

    def debug(self, string):
        """Call UCI to do 'debug' and return response."""
        return self.services.provider.debug(string)

    def isready(self):
        """Call UCI to do 'isready' and return response."""
        return self.services.provider.isready()

    def setoption(self, string):
        """Call UCI to do 'setoption' and return response."""
        return self.services.provider.setoption(string)

    def register(self, string):
        """Call UCI to do 'register' and return response."""
        return self.services.provider.register(string)

    def ucinewgame(self):
        """Call UCI to do 'ucinewgame' and return response."""
        return self.services.provider.ucinewgame()

    def position(self, string):
        """Call UCI to do 'position' and return response."""
        return self.services.provider.position(string)

    def go(self, string):
        """Call UCI to do 'go' and return response."""
        return self.services.provider.go(string)

    def ponderhit(self):
        """Call UCI to do 'ponderhit' and return response."""
        return self.services.provider.ponderhit()

    def quit(self):
        """Call UCI to do 'quit' and return response."""
        return self.services.provider.quit()


class Request(Request):
    """Request handler built from custom Session and Command classes."""

    def __init__(self, session=Session, commands=Commands, logger_name=False):
        """"""
        super().__init__(
            session=session, commands=commands, logger_name=logger_name)


class Scheduler(Request, Respond):
    """Scheduler built from custom Request and standard Respond classes."""
'''
