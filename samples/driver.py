# uci_driver.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Sample display of output from multiple chess engines."""

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import sys
import multiprocessing
from queue import Empty

from ..uci_driver import run_driver


class EngineOutput:

    def __init__(self):

        self.uci_drivers_reply = multiprocessing.Queue()
        self.uci_drivers = dict()
        self.counter = 0

        self.root = tkinter.Tk()
        self.root.wm_title('Output from multiple Chess Engines')
        self.root.wm_minsize(width=500, height=600)
        menubar = tkinter.Menu(self.root)
        menu = tkinter.Menu(menubar, name='engine', tearoff=False)
        menubar.add_cascade(label='Engine', menu=menu, underline=0)
        menu.add_command(
            label='Start',
            underline=0,
            command=self.start_engine)
        menu.add_separator()
        menu.add_command(
            label='Quit',
            underline=0,
            command=self.quit_program)
        menu = tkinter.Menu(menubar, name='commands', tearoff=False)
        menubar.add_cascade(label='Commands', menu=menu, underline=0)
        menu.add_command(
            label='uci',
            underline=0,
            command=self.uci)
        menu.add_command(
            label='debug',
            underline=0,
            command=self.debug)
        menu.add_command(
            label='isready',
            underline=0,
            command=self.isready)
        menu.add_command(
            label='setoption',
            underline=0,
            command=self.setoption)
        menu.add_command(
            label='register',
            underline=0,
            command=self.register)
        menu.add_command(
            label='ucinewgame',
            underline=3,
            command=self.ucinewgame)
        menu.add_command(
            label='position',
            underline=0,
            command=self.position)
        menu.add_command(
            label='go',
            underline=0,
            command=self.go)
        menu.add_command(
            label='stop',
            underline=1,
            command=self.stop)
        menu.add_command(
            label='ponderhit',
            underline=1,
            command=self.ponderhit)
        menu.add_command(
            label='quit',
            underline=0,
            command=self.quit_)
        self.root.configure(menu=menubar)
        text = tkinter.Text(self.root)
        scrollbar = tkinter.Scrollbar(
            master=self.root,
            orient=tkinter.VERTICAL,
            command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        text.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE)
        self.text = text

        self.get_engine_responses()

    def quit_program(self):
        
        quitmsg = 'Confirm Quit.'
        dlg = tkinter.messagebox.askquestion(title='Quit', message=quitmsg)
        if dlg == tkinter.messagebox.YES:
            for ud, v in self.uci_drivers.items():
                try:
                    v[1].put('quit')
                except:
                    tkinter.messagebox.showinfo(
                        title='Stop Engine',
                        message=''.join((
                            v[0],
                            ' failed to stop.\n\nYou may have to kill',
                            ' process id ',
                            str(ud.pid),
                            ' manually after this progam finishes.',
                            )),
                        )
            for ud in self.uci_drivers:
                ud.join()
            self.uci_drivers.clear()
            self.root.destroy()

    def start_engine(self):

        if sys.platform == 'win32':
            filetypes = (('Chess Engines', '*.exe'),)
        else:
            filetypes = ()
        engine = tkinter.filedialog.askopenfilename(
            parent=self.root,
            title='Run Chess Engine',
            filetypes=filetypes,
            initialfile='',
            initialdir='~')
        if not engine:
            return

        def get(event):
            self.run_engine(self._contents.get())
            self._toplevel.destroy()
            del self._toplevel
            del self._contents

        self.do_command(engine, get)

    def do_command(self, initial_value, callback):
            
        self._command = initial_value.split(None, maxsplit=1)[0]
        self._toplevel = tkinter.Toplevel(self.root)
        entrythingy = tkinter.Entry(self._toplevel)
        entrythingy.pack(fill=tkinter.BOTH)
        self._contents = tkinter.StringVar()
        self._contents.set(initial_value)
        entrythingy["textvariable"] = self._contents
        entrythingy.bind('<Key-Return>', callback)

    def run_engine(self, program_file_name):
        
        self.counter += 1
        ui_name = ' : '.join((str(self.counter), program_file_name))
        to_driver_queue = multiprocessing.Queue()
        driver = multiprocessing.Process(
            target=run_driver,
            args=(to_driver_queue,
                  self.uci_drivers_reply,
                  program_file_name,
                  ui_name),
            )
        driver.start()
        self.uci_drivers[driver] = (program_file_name, to_driver_queue)

    def send_to_all_engines(self, event):

        command = self._contents.get()
        if command.split()[0] != self._command:
            if tkinter.messagebox.askquestion(
                title='Send to Engine',
                message=''.join(
                    ('Command is not the one used to start dialogue.\n\n',
                     'Do you want to cancel dialogue?',
                     )),
                ) == tkinter.messagebox.YES:
                del self._command
                del self._contents
                self._toplevel.destroy()
                del self._toplevel
            return
        for name, to_driver_queue in self.uci_drivers.values():
            try:
                to_driver_queue.put(command)
            except:
                tkinter.messagebox.showinfo(
                    title='Send to Engine',
                    message=''.join((
                        'Send command\n\n',
                        command,
                        '\n\nto\n\n',
                        name,
                        '\n\nfailed.',
                        )),
                    )
        del self._command
        del self._contents
        self._toplevel.destroy()
        del self._toplevel

    def uci(self):

        self.do_command('uci', self.send_to_all_engines)

    def debug(self):

        self.do_command('debug', self.send_to_all_engines)

    def isready(self):

        self.do_command('isready', self.send_to_all_engines)

    def setoption(self):

        self.do_command('setoption', self.send_to_all_engines)

    def register(self):

        self.do_command('register', self.send_to_all_engines)

    def ucinewgame(self):

        self.do_command('ucinewgame', self.send_to_all_engines)

    def position(self):

        self.do_command('position', self.send_to_all_engines)

    def go(self):

        self.do_command('go', self.send_to_all_engines)

    def stop(self):

        self.do_command('stop', self.send_to_all_engines)

    def ponderhit(self):

        self.do_command('ponderhit', self.send_to_all_engines)

    def quit_(self):

        self.do_command('quit', self.send_to_all_engines)

    def get_engine_responses(self):

        text = self.text
        self.root.after(1000, self.get_engine_responses)
        while True:
            try:
                item = self.uci_drivers_reply.get_nowait()
            except Empty:
                break
            try:
                n, r = item
                text.insert(tkinter.END, ''.join((str(n), '\n')))
                for i in r:
                    try:
                        text.insert(tkinter.END, i)
                    except:
                        text.insert(tkinter.END, '*** unable to insert item')
                    text.insert(tkinter.END, '\n')
            except:
                text.insert(tkinter.END, '*** unable to insert any items')
            

if __name__ == '__main__':

    app = EngineOutput()
    try:
        app.root.mainloop()
    except:
        try:
            app.root.destroy()
        except:
            pass
    finally:
        del app
