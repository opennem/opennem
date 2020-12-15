__all__ = ["dumps", "loads"]


alphabet = "ZAC2B3EF4GH5TK67P8RS9WXY"


def dumps(number: int) -> str:
    """"""
    if not isinstance(number, int):
        raise TypeError("number must be an integer")

    if number < 0:
        return "-" + dumps(-number)

    value = ""

    while number != 0:
        number, index = divmod(number, len(alphabet))
        value = alphabet[index] + value

    return value or "0"


def loads(value: str) -> int:
    """"""
    if len(value) > 13:
        raise ValueError("base24 input too large")

    return int(value, 24)
