import os
import sys

# Set terminal environment before anything else
os.environ['TERM'] = 'xterm-256color'
os.environ['COLUMNS'] = '90'
os.environ['LINES'] = '30'

# Now run the menu
os.execvp('python3', ['python3', 'WrestlingMenu.py'])
