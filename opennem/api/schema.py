from pydantic import BaseModel, ConfigDict, Field


class ApiBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )


class UpdateResponse(BaseModel):
    success: bool = True
    records: list = []


class FueltechResponse(ApiBase):
    success: bool = True

    # @TODO fix circular references
    # records: List[FueltechSchema]


class APINetworkRegion(ApiBase):
    code: str
    timezone: str | None = None


class APINetworkSchema(ApiBase):
    code: str
    country: str
    label: str

    regions: list[APINetworkRegion] | None = None
    timezone: str | None = Field(None, description="Network timezone")
    interval_size: int = Field(..., description="Size of network interval in minutes")
