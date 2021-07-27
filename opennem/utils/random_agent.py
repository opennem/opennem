"""
Simple random agent module that picks a random user agent from a list in
an external file.

This replaces unreliable external libraries that don't get updated.
"""
from random import choice
from typing import List

from opennem.core.loader import load_data

_RANDOM_AGENTS: List[str] = []


def _load_user_agents() -> List[str]:
    """Load list of user agents from data source"""
    _agents: bytes = load_data("user_agents.txt", from_project=True)

    agents = [
        i.decode("utf-8")
        for i in _agents.splitlines()
        if len(i) > 0 and not i.decode("utf-8").startswith("More ")
    ]

    return agents


def get_random_agent() -> str:
    """Return a random browser user agent"""
    global _RANDOM_AGENTS

    if len(_RANDOM_AGENTS) == 0:
        _RANDOM_AGENTS = _load_user_agents()

    return choice(_RANDOM_AGENTS)


if __name__ == "__main__":
    print(get_random_agent())
