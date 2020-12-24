"""
Profiler - profile code in context

Usage:

```py
with profiled():
    code_to_run()
```
"""

import contextlib
import cProfile
import io
import pstats


@contextlib.contextmanager
def profiled():
    pr = cProfile.Profile()
    pr.enable()
    yield
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats()
    # uncomment this to see who's calling what
    # ps.print_callers()
    print(s.getvalue())
