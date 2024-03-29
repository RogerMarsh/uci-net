# driver.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Sample display of output from multiple chess engines."""

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import sys
import multiprocessing
from queue import Empty
from urllib.parse import urlsplit

from ..uci_driver_over_tcp import UCIDriverOverTCP
from ..engine import CommandsToEngine


# Copied from chesstab/core/uci.py
def run_driver(to_driver_queue, to_ui_queue, path, args, ui_name):
    """Run the process or thread driving communication with chess engine."""
    driver = UCIDriverOverTCP(to_ui_queue, ui_name)
    try:
        driver.start_engine(path, args)
    except Exception:
        to_ui_queue.put(("start failed", (ui_name,)))
        return
    to_ui_queue.put(("started", (ui_name,)))
    while True:
        command = to_driver_queue.get()
        if command == CommandsToEngine.quit_:
            break
        driver.send_to_engine(command)
    driver.quit_engine()


class EngineOutput:
    """An application to communicate with chess engines with UCI commands.

    The commands are typed by the user and engine responses are displayed.

    """

    def __init__(self):
        """Start application."""
        self.uci_drivers_reply = multiprocessing.Queue()
        self.uci_drivers = dict()
        self.counter = 0

        self.root = tkinter.Tk()
        self.root.wm_title("Output from multiple Chess Engines")
        self.root.wm_minsize(width=500, height=600)
        menubar = tkinter.Menu(self.root)
        menu = tkinter.Menu(menubar, name="engine", tearoff=False)
        menubar.add_cascade(label="Engine", menu=menu, underline=0)
        menu.add_command(
            label="Start Local", underline=6, command=self.start_local_engine
        )
        menu.add_command(
            label="Start Remote", underline=6, command=self.start_remote_engine
        )
        menu.add_separator()
        menu.add_command(label="Quit", underline=0, command=self.quit_program)
        menu = tkinter.Menu(menubar, name="commands", tearoff=False)
        menubar.add_cascade(label="Commands", menu=menu, underline=0)
        menu.add_command(
            label=CommandsToEngine.uci, underline=0, command=self.uci
        )
        menu.add_command(
            label=CommandsToEngine.debug, underline=0, command=self.debug
        )
        menu.add_command(
            label=CommandsToEngine.isready, underline=0, command=self.isready
        )
        menu.add_command(
            label=CommandsToEngine.setoption,
            underline=0,
            command=self.setoption,
        )
        menu.add_command(
            label=CommandsToEngine.register, underline=0, command=self.register
        )
        menu.add_command(
            label=CommandsToEngine.ucinewgame,
            underline=3,
            command=self.ucinewgame,
        )
        menu.add_command(
            label=CommandsToEngine.position, underline=0, command=self.position
        )
        menu.add_command(
            label=CommandsToEngine.go, underline=0, command=self.go
        )
        menu.add_command(
            label=CommandsToEngine.stop, underline=1, command=self.stop
        )
        menu.add_command(
            label=CommandsToEngine.ponderhit,
            underline=1,
            command=self.ponderhit,
        )
        menu.add_command(
            label=CommandsToEngine.quit_, underline=0, command=self.quit_
        )
        self.root.configure(menu=menubar)
        text = tkinter.Text(self.root)
        scrollbar = tkinter.Scrollbar(
            master=self.root, orient=tkinter.VERTICAL, command=text.yview
        )
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        text.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE)
        self.text = text

        self.get_engine_responses()

    def quit_program(self):
        """Quit."""
        quitmsg = "Confirm Quit."
        dlg = tkinter.messagebox.askquestion(title="Quit", message=quitmsg)
        if dlg == tkinter.messagebox.YES:
            for ucid, value in self.uci_drivers.items():
                try:
                    value[1].put(CommandsToEngine.quit_)
                except Exception:
                    tkinter.messagebox.showinfo(
                        title="Stop Engine",
                        message="".join(
                            (
                                value[0],
                                " failed to stop.\n\nYou may have to kill",
                                " process id ",
                                str(ucid.pid),
                                " manually after this progam finishes.",
                            )
                        ),
                    )
            for ucid in self.uci_drivers:
                ucid.join()
            self.uci_drivers.clear()
            self.root.destroy()

    def start_local_engine(self):
        """Start chess engine by specifying local executable filename."""
        if sys.platform == "win32":
            filetypes = (("Chess Engines", "*.exe"),)
        else:
            filetypes = ()
        engine = tkinter.filedialog.askopenfilename(
            parent=self.root,
            title="Run Chess Engine",
            filetypes=filetypes,
            initialfile="",
            initialdir="~",
        )
        if not engine:
            return

        def get(event):
            # get is bound to a tkinter.Entry widget as the callback.
            text = self._contents.get()
            url = urlsplit(text)
            if url.port or url.hostname:
                tkinter.messagebox.showinfo(
                    title="Start Local Engine",
                    message="Starting a remote engine is not allowed here",
                )
                return
            text = text.split(maxsplit=1)
            self.run_engine(text[0], text[1] if len(text) > 1 else None)
            self._toplevel.destroy()
            del self._toplevel
            del self._contents

        self.do_command(engine, get)

    def start_remote_engine(self):
        """Start chess engine by specifying URL with hostname and port."""

        def get(event):
            # get is bound to a tkinter.Entry widget as the callback.
            text = self._contents.get()
            url = urlsplit(text)
            if not (url.port and url.hostname):
                tkinter.messagebox.showinfo(
                    title="Start Remote Engine",
                    message="Specify hostname and port for remote engine",
                )
                return
            self.run_engine(text, None)
            self._toplevel.destroy()
            del self._toplevel
            del self._contents

        self.do_command("//", get)

    def do_command(self, initial_value, callback):
        """Process engine command typed by user with callback function."""
        self._command = initial_value.split(None, maxsplit=1)[0]
        self._toplevel = tkinter.Toplevel(self.root)
        entrythingy = tkinter.Entry(self._toplevel)
        entrythingy.pack(fill=tkinter.BOTH)
        self._contents = tkinter.StringVar()
        self._contents.set(initial_value)
        entrythingy["textvariable"] = self._contents
        entrythingy.bind("<Key-Return>", callback)

    def run_engine(self, program_file_name, args):
        """Run chess engine program_file_name in a separate process."""
        self.counter += 1
        ui_name = " : ".join((str(self.counter), program_file_name))
        to_driver_queue = multiprocessing.Queue()
        driver = multiprocessing.Process(
            target=run_driver,
            args=(
                to_driver_queue,
                self.uci_drivers_reply,
                program_file_name,
                args,
                ui_name,
            ),
        )
        driver.start()
        self.uci_drivers[driver] = (program_file_name, to_driver_queue)

    def send_to_all_engines(self, event):
        """Send a command to all engines.

        send_to_all_engines is bound to a tkinter.Entry widget as the callback.

        """
        command = self._contents.get()
        if command.split()[0] != self._command:
            if (
                tkinter.messagebox.askquestion(
                    title="Send to Engine",
                    message="".join(
                        (
                            "Command is not the one used to start dialogue.",
                            "\n\nDo you want to cancel dialogue?",
                        )
                    ),
                )
                == tkinter.messagebox.YES
            ):
                del self._command
                del self._contents
                self._toplevel.destroy()
                del self._toplevel
            return
        for name, to_driver_queue in self.uci_drivers.values():
            try:
                to_driver_queue.put(command)
            except Exception:
                tkinter.messagebox.showinfo(
                    title="Send to Engine",
                    message="".join(
                        (
                            "Send command\n\n",
                            command,
                            "\n\nto\n\n",
                            name,
                            "\n\nfailed.",
                        )
                    ),
                )
        del self._command
        del self._contents
        self._toplevel.destroy()
        del self._toplevel

    def uci(self):
        """Send uci command to all engines."""
        self.do_command(CommandsToEngine.uci, self.send_to_all_engines)

    def debug(self):
        """Send debug command to all engines."""
        self.do_command(CommandsToEngine.debug, self.send_to_all_engines)

    def isready(self):
        """Send isready command to all engines."""
        self.do_command(CommandsToEngine.isready, self.send_to_all_engines)

    def setoption(self):
        """Send setoption command to all engines."""
        self.do_command(CommandsToEngine.setoption, self.send_to_all_engines)

    def register(self):
        """Send register command to all engines."""
        self.do_command(CommandsToEngine.register, self.send_to_all_engines)

    def ucinewgame(self):
        """Send newgame command to all engines."""
        self.do_command(CommandsToEngine.ucinewgame, self.send_to_all_engines)

    def position(self):
        """Send position command to all engines."""
        self.do_command(CommandsToEngine.position, self.send_to_all_engines)

    def go(self):
        """Send go command to all engines."""
        self.do_command(CommandsToEngine.go, self.send_to_all_engines)

    def stop(self):
        """Send stop command to all engines."""
        self.do_command(CommandsToEngine.stop, self.send_to_all_engines)

    def ponderhit(self):
        """Send ponderhit command to all engines."""
        self.do_command(CommandsToEngine.ponderhit, self.send_to_all_engines)

    def quit_(self):
        """Send quit command to all engines."""
        self.do_command(CommandsToEngine.quit_, self.send_to_all_engines)

    def get_engine_responses(self):
        """Process engine responses."""
        text = self.text
        self.root.after(1000, self.get_engine_responses)
        while True:
            try:
                item = self.uci_drivers_reply.get_nowait()
            except Empty:
                break
            try:
                name, response = item
                text.insert(tkinter.END, "".join((str(name), "\n")))
                for clause in response:
                    try:
                        text.insert(tkinter.END, clause)
                    except Exception:
                        text.insert(tkinter.END, "*** unable to insert item")
                    text.insert(tkinter.END, "\n")
            except Exception:
                text.insert(tkinter.END, "*** unable to insert any items")


if __name__ == "__main__":

    app = EngineOutput()
    try:
        app.root.mainloop()
    except Exception:
        try:
            app.root.destroy()
        except Exception:
            pass
    finally:
        del app
