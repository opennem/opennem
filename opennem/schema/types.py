"""
OpenNEM Custom Schema Types


"""

from typing import Any, Callable, Dict, Generator, Union

from pydantic.networks import AnyUrl
from pydantic.validators import str_validator

from opennem.core.normalizers import validate_twitter_handle

AnyCallable = Callable[..., Any]

CallableGenerator = Generator[AnyCallable, None, None]


class PostgresSqlAlchemyDsn(AnyUrl):
    """DSN for Postgres for latest sqlalchemy which doesn't allow `postgres` as the scheme"""

    allowed_schemes = {"postgresql"}
    user_required = True


class TwitterHandle(str):
    """Twitter Handle type for Pydantic schemas"""

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type="string", format="twitter_handle")

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[str]) -> str:
        if validate_twitter_handle(value):
            return value

        raise ValueError("Invalid twitter handle")
