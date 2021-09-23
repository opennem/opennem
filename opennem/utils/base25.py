__all__ = ["dumps", "loads"]

from string import ascii_uppercase

alphabet = ascii_uppercase


def int2base(x, base):
    if x < 0:
        sign = -1
    elif x == 0:
        return alphabet[0]
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(alphabet[x % base])
        x = x // base

    if sign < 0:
        digits.append("-")

    digits.reverse()

    return "".join(digits)


def dumps(number: int) -> str:
    """ """
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
    """ """
    if len(value) > 3:
        raise ValueError("base25 input too large")

    return int(value, 25)
