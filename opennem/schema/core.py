from pydantic import BaseModel


class BaseConfig(BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True

        arbitrary_types_allowed = True
        validate_assignment = True

        json_encoders = {
            # datetime: lambda v: v.isotime(),
            # Decimal: lambda v: float(v),
        }
