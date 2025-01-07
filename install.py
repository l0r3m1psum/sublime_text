import os
import sys
import shutil

if sys.platform == 'win32':
	sublime_user_dir = '%LOCALAPPDATA%\\Programs\\Sublime Text\\Data\\Packages\\User'
elif sys.platform == 'darwin':
	sublime_user_dir = '$HOME/Library/Application Support/Sublime Text/Packages/User'
else:
	raise RuntimeError('unsupported platform')
sublime_user_dir = os.path.expandvars(sublime_user_dir)

shutil.copytree('User', sublime_user_dir, dirs_exist_ok=True)
