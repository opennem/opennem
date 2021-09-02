c.TerminalIPythonApp.display_banner = True
c.InteractiveShellApp.log_level = 20
c.InteractiveShellApp.extensions = ["storemagic"]
c.InteractiveShellApp.exec_lines = ["import numpy as np", "import pandas as pd", "import opennem"]
# c.InteractiveShellApp.exec_files = ["methods.py"]
c.TerminalInteractiveShell.highlighting_style = "solarized-dark"
c.InteractiveShell.colors = "Neutral"
c.InteractiveShell.confirm_exit = False
c.InteractiveShell.editor = "vi"
c.InteractiveShell.xmode = "Context"

c.PrefilterManager.multi_line_specials = True

# storemagic config
# auto restores saved variables
c.StoreMagics.autorestore = True
