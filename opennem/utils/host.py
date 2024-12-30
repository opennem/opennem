import socket


def get_hostname() -> str:
    """
    Get the hostname of the machine
    """
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"
