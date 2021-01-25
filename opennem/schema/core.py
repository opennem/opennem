from pydantic import BaseModel


class PropertyBaseModel(BaseModel):
    """
    Workaround for serializing properties with pydantic until
    https://github.com/samuelcolvin/pydantic/issues/935
    is solved
    """

    @classmethod
    def get_properties(cls):
        return [
            prop
            for prop in dir(cls)
            if isinstance(getattr(cls, prop), property) and prop not in ("__values__", "fields")
        ]

    def dict(self, *args, **kwargs) -> "DictStrAny":
        self.__dict__.update({prop: getattr(self, prop) for prop in self.get_properties()})

        return super().dict(*args, **kwargs)


class BaseConfig(PropertyBaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True

        arbitrary_types_allowed = True
        validate_assignment = True

        json_encoders = {
            # datetime: lambda v: v.isotime(),
            # Decimal: lambda v: float(v),
        }
