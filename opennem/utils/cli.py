import os
import sys
import termios
import tty


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


def yes_or_no(question: str) -> bool:
    """Prompts the user to confirm input"""
    c: str = ""

    print("{} (Y/n): ".format(question), end="", flush=True)

    while c not in ("y", "n"):
        print(c)
        c = getch().lower()

    return c == "y"


if __name__ == "__main__":
    if not yes_or_no("Continue?"):
        print("No")
        os._exit(0)
    else:
        print("Yes")
