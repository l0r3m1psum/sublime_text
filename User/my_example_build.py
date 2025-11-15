import sublime
import sublime_plugin

import subprocess
import threading
import os

# from typing import override

# https://www.sublimetext.com/docs/build_systems.html#advanced-example
class MyExampleBuildCommand(sublime_plugin.WindowCommand):

    encoding = 'utf-8'
    killed = False
    proc = None
    panel = None
    panel_lock = threading.Lock()

    # @override
    def is_enabled(self, kill=False):
        # The Cancel build option should only be available
        # when the process is still running
        if kill:
            return self.proc is not None and self.proc.poll() is None
        return True

    # @override
    def run(self, kill=False):
        if kill:
            if self.proc:
                self.killed = True
                self.proc.terminate()
            return

        vars = self.window.extract_variables()
        working_dir = vars['file_path']

        with self.panel_lock:
            self.panel, self.input_panel = self.window.create_io_panel('exec', lambda s: self.handle_input(s))

            settings = self.panel.settings()
            settings.set('result_file_regex', r'^File "([^"]+)" line (\d+) col (\d+)')
            settings.set('result_line_regex', r'^\s+line (\d+) col (\d+)')
            settings.set('result_base_dir', working_dir)

            self.window.run_command('show_panel', {'panel': 'output.exec'})

        if self.proc is not None:
            self.proc.terminate()
            self.proc = None

        args = ['python3', vars['file_name']]
        env = os.environ.copy()
        env.update({
            "PYTHONPATH": os.path.join(vars['packages'], "User"),
            "PYTHONBREAKPOINT": "sublime_text_pdb.set_trace",
        })
        self.proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=working_dir,
            env=env,
        )

        self.killed = False

        threading.Thread(
            target=self.read_handle,
            args=(self.proc.stdout,)
        ).start()

    def handle_input(self, s):
        os.write(self.proc.stdin.fileno(), (s+"\n").encode(self.encoding))
        self.queue_write(s+"\n")

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
