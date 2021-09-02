"""iPython startup file that loads extensions"""

from IPython import get_ipython

ipython = get_ipython()

if "__IPYTHON__" in globals():
    ipython.magic("load_ext autoreload")
    ipython.magic("autoreload 2")
