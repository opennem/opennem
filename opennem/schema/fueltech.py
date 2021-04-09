from .core import BaseConfig


class FueltechSchema(BaseConfig):
    code: str
    label: str
    renewable: bool = False
