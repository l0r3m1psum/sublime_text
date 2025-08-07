"""This module is supposed to be put in your PYTHONPATH and than be a drop-in
replacement for Python's breakpoint() function by setting the environment
variable PYTHONBREAKPOINT=sublime_text_pdb.set_trace

https://ajmalsiddiqui.me/blog/extending-the-python-debugger/
https://sublime-text-unofficial-documentation.readthedocs.io/en/latest/reference/commands.html
"""

import os
import pdb
import sys

# subprocess.run is not used because importing the subprocess module changes the
# behavior of pdb when reaching the end of the program i.e. it starts stepping
# into the threading module.

class SublimeTextPdb(pdb.Pdb):
	def user_line(self, frame):

		file = frame.f_globals.get("__file__", "")
		if file and self.subl_path:
			lineno = frame.f_lineno
			file_and_lineno = "%s:%d" % (file, lineno)
			exit_code_or_neg_signal = os.spawnv(
				os.P_WAIT,
				self.subl_path,
				("subl", "--background", file_and_lineno)
			)
			move_cmd = "move_to {\"to\": \"eol\", \"extend\": true}"
			# https://discuss.python.org/t/how-to-deal-with-unsafe-broken-os-spawn-arg-handling-behavior-on-windows/20829
			if os.name == "nt":
				move_cmd = move_cmd.replace("\"", "\\\"")
				move_cmd = "\"%s\"" % move_cmd
			# FIXME: sometimes this randomly hangs on Windows.
			exit_code_or_neg_signal = os.spawnv(
				os.P_WAIT,
				self.subl_path,
				("subl", "--command", move_cmd, "--background")
			)

		super().user_line(frame)

def set_trace(*args, **kwargs):
	paths = os.environ.get("PATH", "").split(os.pathsep)
	if os.name == "nt":
		exts = os.environ.get("PATHEXT", "").split(os.pathsep)
	else:
		exts = ("",)

	exts = [ext.lower() for ext in exts]

	for path in paths:
		try:
			file_list = os.listdir(path)
		except:
			file_list = ()

		if os.name == "nt":
			file_list = [file.lower() for file in file_list]

		for ext in exts:
			subl_file_name = "subl" + ext
			if subl_file_name in file_list:
				subl_path = os.path.join(path, "subl")
				break
		# Horrible trick to break out of the outer loop if we find the path.
		else:
			continue
		break
	else:
		subl_path = ""

	sublime_text_debugger = SublimeTextPdb(*args, **kwargs)
	sublime_text_debugger.subl_path = subl_path
	caller_frame = sys._getframe(1)
	sublime_text_debugger.set_trace(frame=caller_frame)
