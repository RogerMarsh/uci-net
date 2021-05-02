# cli_user_thread.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

from multiprocessing.dummy import freeze_support
import os

from clientserver.samples.cli_user_thread import run_user

from .. import CLIUser


if __name__ == '__main__':

    freeze_support()
    run_user(CLIUser, log_directory=os.path.join('~', '__uci_user_logs'))
