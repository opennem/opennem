from typing import Generator


def user_agent_rotate() -> Generator[str, None, None]:
    pass


try:
    from random_user_agent.user_agent import UserAgent

    # user agent rotator
    user_agent_rotator = UserAgent(limit=100)
except ImportError:
    pass

    user_agent_rotator = None
