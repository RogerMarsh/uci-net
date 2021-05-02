# uci_driver.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Universal Chess Interface (UCI) communication with chess engine driver.

UCIDriver was originally in UCI (uci.py) as the extension of Provider class
for chess engines, but it should be available independently.

"""

from .uci_mixin import UCIMixin, UCIError


class UCIDriver(UCIMixin):
    """Implement non-Provider UCI communication with chess engines.

    """
    def __init__(self, to_ui_queue, ui_name):
        """Create a database state instance."""
        super().__init__()
        self.init_mixin(to_ui_queue, ui_name)


def run_driver(to_driver_queue, to_ui_queue, path, args, ui_name):
    """"""
    driver = UCIDriver(to_ui_queue, ui_name)
    try:
        driver.start_engine(path, args)
    except:
        to_ui_queue.put(('start failed', (ui_name,)))
        return
    to_ui_queue.put(('started', (ui_name,)))
    while True:
        command = to_driver_queue.get()
        if command == 'quit':
            break
        driver.send_to_engine(command)
    driver.quit_engine()
