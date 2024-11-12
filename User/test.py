import sublime
import sublime_plugin
import os

class ExampleCommand(sublime_plugin.TextCommand):
	"""On windows there is no easy way to open in explorer.exe the directory in
	which the current file is located. This command fixes this issue."""
	def run(self, edit):
		file_name = self.view.file_name()
		if file_name:
			dirname = os.path.dirname(file_name)
			os.startfile(dirname)
