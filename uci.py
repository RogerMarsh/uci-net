# uci.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Universal Chess Interface (UCI) communication with chess engines.

The 'Description of the universal chess interface (UCI)    April  2006' seems
difficult to understand.  I failed to find a separate document claiming to
define the UCI protocol, so assume the description is also the definition.

See www.stmintz.com/ccc/index.php?id=142012 for a discussion of many points in
the form of a reply to a post.  Original post at ~=141940.

The text of //ucichessengine.wordpress.com/description-of-uci-protocol viewed
on 5 August 2015 seems to be the same.

Compare the descriptions of isready and readyok.

isready:

this is used to synchronize the engine with the GUI. When the GUI has sent a
command or multiple commands that can take some time to complete,
this command can be used to wait for the engine to be ready again or
to ping the engine to find out if it is still alive.
E.g. this should be sent after setting the path to the tablebases as this can
take some time.
This command is also required once before the engine is asked to do any search
to wait for the engine to finish initializing.
This command must always be answered with "readyok" and can be sent also when
the engine is calculating in which case the engine should also immediately
answer with "readyok" without stopping the search.

readyok:

This must be sent when the engine has received an "isready" command and has
processed all input and is ready to accept new commands now.
It is usually sent after a command that can take some time to be able to wait
for the engine, but it can be used anytime, even when the engine is searching,
and must always be answered with "isready".


There are four ways of replacing the two 'it's in the last sentence of the
description of readyok:

'isready' is usually sent after a command that can take some time to be able to
wait for the engine, but 'isready' can be used anytime, even when the engine is
searching, and must always be answered with "isready".

'readyok' is usually sent after a command that can take some time to be able to
wait for the engine, but 'readyok' can be used anytime, even when the engine is
searching, and must always be answered with "isready".

'isready' is usually sent after a command that can take some time to be able to
wait for the engine, but 'readyok' can be used anytime, even when the engine is
searching, and must always be answered with "isready".

'readyok' is usually sent after a command that can take some time to be able to
wait for the engine, but 'isready' can be used anytime, even when the engine is
searching, and must always be answered with "isready".

Replacing both 'it's with 'readyok' makes sense only if the GUI sends readyok
and the engine sends isready.  Replacing one 'it' with 'readyok', and the other
'it' with 'isready' implies either the GUI or the engine, or perhaps both, can
send either or both 'readyok' and 'isready' at any time.  Replacing both 'it's
with 'isready' implies an infinite loop because sending one of these commands
demands the other command is sent back.

An inconclusive discussion of the problem with isready and readyok appears at
//www.open-chess.org under View topic - UCI Interfacing questions.

Replacing both 'it's with 'isready' and '"isready"' with '"readyok"' makes sense
because the engine sends readyok in response to the GUI sending isready.

This module assumes the apparently sensible replacements yield the intended
specification.

"""

# Use the multiprocessing API for threading
from multiprocessing import dummy

from . import Provider
from .uci_mixin import UCIMixin, UCIError


class UCI(Provider, UCIMixin):
    """Extend Provider to implement UCI communication with chess engines.

    Provider assumes a strict send and reply sequence, while the UCI protocol
    allows the reply to be optional.  Some important types of UCI question are
    strict send and reply, including those with a reachable finish condition.

    The best achieved in the UCI protocol is 'reply as soon as possible'.

    """
    
    _shared_state = {}

    def __init__(self):
        """Create a database state instance."""
        if len(self.__dict__):
            # Subclass of Borg but first instantiation binds attributes
            return
        super().__init__()
        self.init_mixin(dummy.Queue(), None)

    def uci(self):
        """Call UCI to do 'uci' and return response."""
        if not self.engine_process:
            return ()
        self.send_to_engine('uci')
        return self.to_ui_queue.get()

    def debug(self, string):
        """Call UCI to do 'debug' and return response."""
        if not self.engine_process:
            return ()
        self.send_to_engine(' '.join(('debug', string)))

        # No commands from engine in response to debug command.
        
        return ()

    def isready(self):
        """Call UCI to do 'isready' and return response."""
        if not self.engine_process:
            return ()
        self.send_to_engine('isready')
        return self.to_ui_queue.get()

    def setoption(self, string):
        """Call UCI to do 'setoption' and return response."""
        if not self.engine_process:
            return ()
        self.send_to_engine(' '.join(('setoption', string)))

        # No commands from engine in response to debug command.
        
        return ()

    def register(self, string):
        """Call UCI to do 'register' and return response."""
        if not self.engine_process:
            return ()
        self.send_to_engine(' '.join(('register', string)))

        # No commands from engine in response to debug command.
        
        return ()

    def ucinewgame(self):
        """Call UCI to do 'ucinewgame' and return response."""
        if not self.engine_process:
            return ()
        self.send_to_engine('ucinewgame')

        # No commands from engine in response to ucinewgame command.
        
        return ()

    def position(self, string):
        """Call UCI to do 'position' and return response."""
        if not self.engine_process:
            return ()
        self.send_to_engine(' '.join(('position', string)))

        # No commands from engine in response to position command.
        
        return ()

    def go(self, string):
        """Call UCI to do 'go' and return response."""
        if not self.engine_process:
            return ()
        self.send_to_engine(' '.join(('go', string)))
        return self.to_ui_queue.get()

    def stop(self):
        """Call UCI to do 'stop' and return response."""
        if not self.engine_process:
            return ()
        self.send_to_engine('stop')
        try:
            return self.to_ui_queue.get(timeout=1)
        except dummy.Empty:
            return ()

    def ponderhit(self):
        """Call UCI to do 'ponderhit' and return response."""
        return ()

    def quit(self):
        """Call UCI to do 'quit' and return response."""
        if not self.engine_process:
            return True
        return self.quit_engine()

    def start_provider(self, user, host, path):
        """Start chess engine at path in UCI mode for user on host."""
        session = super().start_provider(user, host, path)
        if not session:
            return session

        return session

    def stop_provider(self):
        """Stop chess engine and return True if close down is allowed."""
        if not super().stop_provider():
            return ()
        return self.quit()

    def engine(self, string):
        """Set command to start engine."""
        if self.engine_process:
            return ()

        self.start_engine(string)

        # No commands sent to engine.

        return ('Engine command ',)
