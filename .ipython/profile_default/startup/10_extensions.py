"""iPython startup file that loads extensions"""
from IPython import get_ipython

ipython = get_ipython()

# If in ipython, load autoreload extension
if "ipython" in globals():
    ipython.magic("load_ext autoreload")
    ipython.magic("autoreload 2")

# Display all cell outputs in notebook
from IPython.core.interactiveshell import InteractiveShell  # noqa: E402

InteractiveShell.ast_node_interactivity = "all"
