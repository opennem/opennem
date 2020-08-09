from pydantic import BaseModel


class OpennemBaseModel(BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
        # validate_assignment = True
