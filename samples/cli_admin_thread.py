# cli_admin_thread.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

from multiprocessing.dummy import freeze_support
import os

from clientserver.samples.cli_admin_thread import run_admin

from .. import Scheduler
from .. import CLIAdmin
from .. import Session


if __name__ == '__main__':

    freeze_support()
    run_admin(CLIAdmin,
              Session,
              Scheduler,
              log_directory=os.path.join('~', '__uci_admin_logs'))
