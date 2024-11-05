"""
https://www.sublimetext.com/docs/build_systems.html#advanced-example
"""
import sublime
import sublime_plugin

import subprocess
import threading
import os


class MyExampleBuildCommand(sublime_plugin.WindowCommand):

    encoding = 'utf-8'
    killed = False
    proc = None
    panel = None
    panel_lock = threading.Lock()

    vcvarsall = False

    def is_enabled(self, lint=False, integration=False, kill=False):
        # The Cancel build option should only be available
        # when the process is still running
        if kill:
            return self.proc is not None and self.proc.poll() is None
        return True

    def run(self, lint=False, integration=False, kill=False):
        if kill:
            if self.proc:
                self.killed = True
                self.proc.terminate()
            return

        # TODO: creare una shell che terrà le variabili d'ambiente e eseguirà il
        # build.bat (come faccio a sapere quando il comando nella shell è terminato?)
        if not self.vcvarsall:
            subprocess.run(
                '"C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvarsall.bat" x64'
            )
            self.vcvarsall = True

        vars = self.window.extract_variables()
        working_dir = vars['file_path']

        with self.panel_lock:
            self.panel = self.window.create_output_panel('exec')

            settings = self.panel.settings()
            settings.set('result_file_regex',  r'^File "([^"]+)" line (\d+) col (\d+)')
            settings.set('result_line_regex', r'^\s+line (\d+) col (\d+)')
            settings.set('result_base_dir', working_dir)

            self.window.run_command('show_panel', {'panel': 'output.exec'})

        if self.proc is not None:
            self.proc.terminate()
            self.proc = None

        args = ['set']
        self.proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            cwd=working_dir
        )
        self.killed = False

        threading.Thread(
            target=self.read_handle,
            args=(self.proc.stdout,)
        ).start()
################################################################################
# TODO: this should all be free functions.
    def read_handle(self, handle):
        chunk_size = 2 ** 13
        out = b''
        while True:
            try:
                data = os.read(handle.fileno(), chunk_size)
                # If exactly the requested number of bytes was
                # read, there may be more data, and the current
                # data may contain part of a multibyte char
                out += data
                if len(data) == chunk_size:
                    continue
                if data == b'' and out == b'':
                    raise IOError('EOF')
                # We pass out to a function to ensure the
                # timeout gets the value of out right now,
                # rather than a future (mutated) version
                self.queue_write(out.decode(self.encoding))
                if data == b'':
                    raise IOError('EOF')
                out = b''
            except (UnicodeDecodeError) as e:
                msg = 'Error decoding output using %s - %s'
                self.queue_write(msg  % (self.encoding, str(e)))
                break
            except (IOError):
                if self.killed:
                    msg = 'Cancelled'
                else:
                    msg = 'Finished'
                self.queue_write('\n[%s]' % msg)
                break

    def queue_write(self, text):
        sublime.set_timeout(lambda: self.do_write(text), 1)

    def do_write(self, text):
        with self.panel_lock:
            self.panel.run_command('append', {'characters': text})
