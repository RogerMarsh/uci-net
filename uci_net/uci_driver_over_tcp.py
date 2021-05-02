# uci_driver_over_tcp.py
# Copyright 2017 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Universal Chess Interface (UCI) communication with chess engine driver.

"""

import sys
from urllib.parse import urlsplit

from .uci_driver import UCIDriver


class UCIDriverOverTCP(UCIDriver):
    """Implement communication with chess engine processes.

    """

    def insert_remote_hostname_port(self, args):
        """Prepend args with tcp_client command if args[0] has hostname or port.

        If hostname or port is present prepend args to connect to remote host
        over tcp and have the remote UCI chess engine do analysis.

        tcp_client uses default hostname or port if that item is absent.

        Otherwise the UCI chess engine on localhost is used directly.

        """
        url = urlsplit(args[0])
        if url.port or url.hostname:
            args.insert(0, 'uci.tcp_client')
            args.insert(0, '-m')
            args.insert(
                0,
                ''.join(('python',
                         ('' if sys.platform == 'win32' else
                          '.'.join(str(e) for e in sys.version_info[:2])))))
