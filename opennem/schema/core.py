from pydantic import BaseModel, ConfigDict


class PropertyBaseModel(BaseModel):
    """
    Workaround for serializing properties with pydantic until
    https://github.com/samuelcolvin/pydantic/issues/935
    is solved
    """

    @classmethod
    def get_properties(cls):  # type: ignore
        return [prop for prop in dir(cls) if isinstance(getattr(cls, prop), property) and prop not in ("__values__", "fields")]

    def dict(self, *args, **kwargs) -> dict:  # type: ignore
        self.__dict__.update({prop: getattr(self, prop) for prop in self.get_properties()})

        return super().dict(*args, **kwargs)


class BaseConfig(PropertyBaseModel):
    model_config = ConfigDict(
        from_attributes=True, str_strip_whitespace=True, arbitrary_types_allowed=True, validate_assignment=True
    )
