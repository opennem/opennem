import os
import sys
import termios
import tty
from distutils.util import strtobool


def getch() -> str:
    """Read single character from standard input without echo."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def prompt_user_yes_or_no(question: str, default: str | None = None) -> bool:
    """Prompts the user to confirm input"""
    prompt: str = ""

    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"Unknown setting '{default}' for default.")

    c: str = ""

    print(f"{question} {prompt}: ", end="", flush=True)

    while c not in ("y", "n"):
        print(c)
        c = getch().lower()

    return strtobool(c)


if __name__ == "__main__":
    if not prompt_user_yes_or_no("Continue?"):
        print("No")
        os._exit(0)
    else:
        print("Yes")
