"""
OpenNEM Sys Utilities

"""


def is_running_interactive() -> bool:
    """Check if we're running in an REPL"""
    try:
        import __main__ as m

        return not hasattr(m, "__file__")
    except Exception as e:
        print(e)
        pass

    return False


def clean_exit() -> None:
    """Clean exit from the application with garbage collection, etc."""
    pass
