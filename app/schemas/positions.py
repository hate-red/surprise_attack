from pydantic import BaseModel, ConfigDict, Field


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OKEIResponse(ORMResponse):
    id: str
    name: str


class CharacteristicValueResponse(ORMResponse):
    id: str

    is_range: bool
    range: str | None = None

    is_quality: bool
    quality_description: str | None = None

    okeis: list[OKEIResponse] = Field(default_factory=list)


class CharacteristicResponse(ORMResponse):
    id: str
    name: str
    required: bool
    values: list[CharacteristicValueResponse] = Field(default_factory=list)


class PositionResponse(ORMResponse):
    id: str
    name: str
    okeis: list[OKEIResponse] = Field(default_factory=list)
    characteristics: list[CharacteristicResponse] = Field(default_factory=list)
