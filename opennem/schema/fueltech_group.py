from .core import BaseConfig


class FueltechGroupSchema(BaseConfig):
    code: str
    label: str
    color: str | None = None
    renewable: bool = False
