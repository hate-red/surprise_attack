from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OKEIResponse(ORMResponse):
    id: int
    name: str
    code: str | None = None


class CharacteristicValueResponse(ORMResponse):
    id: int
    name: str | None = None
    measure_units: str | None = None

    is_range: bool
    range: str | None = None

    is_quality: bool
    quality_description: str | None = None
    concrete_value: float | None = None

    okeis: list[OKEIResponse] = Field(default_factory=list)

    @field_validator('range', mode='before')
    @classmethod
    def range_to_str(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        lower = getattr(value, 'lower', None)
        upper = getattr(value, 'upper', None)
        left = '[' if getattr(value, 'lower_inc', False) else '('
        right = ']' if getattr(value, 'upper_inc', False) else ')'
        return f'{left}{"" if lower is None else lower},{"" if upper is None else upper}{right}'


class CharacteristicResponse(ORMResponse):
    id: int
    name: str
    required: bool
    code: str | None = None
    char_type: int | None = None
    kind: int | None = None
    values: list[CharacteristicValueResponse] = Field(default_factory=list)


class PositionResponse(ORMResponse):
    id: str
    name: str
    okpd2_code: str | None = None
    okpd2_name: str | None = None
    is_template: bool = False
    okeis: list[OKEIResponse] = Field(default_factory=list)
    characteristics: list[CharacteristicResponse] = Field(default_factory=list)


# ====================================================== запрос / ответ /parse
class CharacteristicOverride(BaseModel):
    """Значение характеристики, введённое или подтверждённое пользователем."""
    name: str = Field(..., min_length=1, max_length=500)
    value: str = Field(..., min_length=1, max_length=500)


class ParseRequest(BaseModel):
    overrides: list[CharacteristicOverride] = Field(default_factory=list)
    excluded: list[str] = Field(default_factory=list, description='Характеристики, удалённые пользователем')
    selected_code: str | None = Field(None, description='Код КТРУ, выбранный пользователем из кандидатов')


ResultStatus = Literal['resolved', 'need_more_info', 'low_confidence', 'name_not_found']


class Message(BaseModel):
    level: Literal['success', 'info', 'warning', 'error']
    code: str
    text: str


class SpellingIssueOut(BaseModel):
    original: str
    suggestion: str
    start: int
    end: int


class FragmentOut(BaseModel):
    text: str
    start: int
    end: int
    kind: str


class CharacteristicRow(BaseModel):
    id: str
    name: str
    source: Literal['text', 'user', 'ste', 'unknown', 'reference']
    original: str = ''
    normalized: str = ''
    unit: str = ''
    status: str
    required: bool = False
    char_type: Literal['quality', 'quantity', 'unknown'] = 'unknown'
    matched_range: str | None = None
    notes: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    start: int | None = None
    end: int | None = None
    in_specification: bool = False


class StageOut(BaseModel):
    title: str
    detail: str
    count_before: int | None
    count_after: int
    applied: bool
    kind: str
    note: str | None = None


class CandidateOut(BaseModel):
    code: str
    name: str
    okpd2_code: str | None = None
    okpd2_name: str | None = None
    is_template: bool = False
    matched: int = 0
    validity_note: str | None = None


class SuggestionOut(BaseModel):
    id: str
    name: str
    required: bool
    options: list[dict[str, Any]]
    reason: str


class ProductOut(BaseModel):
    name: str
    names: list[str]
    confidence: str
    matched_text: str


class ParseResponse(BaseModel):
    status: ResultStatus
    message: str
    query: str
    corrected_query: str | None = None
    product: ProductOut | None = None
    ktru_code: str | None = None
    ktru_name: str | None = None
    final_position: CandidateOut | None = None
    characteristics: list[CharacteristicRow] = Field(default_factory=list)
    stages: list[StageOut] = Field(default_factory=list)
    candidates: list[CandidateOut] = Field(default_factory=list)
    candidates_total: int = 0
    suggestions: list[SuggestionOut] = Field(default_factory=list)
    name_refinements: list[dict[str, Any]] = Field(default_factory=list)
    okpd2_refinements: list[dict[str, Any]] = Field(default_factory=list)
    name_alternatives: list[str] = Field(default_factory=list)
    spelling: list[SpellingIssueOut] = Field(default_factory=list)
    unrecognized: list[FragmentOut] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    quality: dict[str, int] = Field(default_factory=dict)
    # совместимость с прежним форматом ответа (list[PositionResponse])
    positions: list[PositionResponse] = Field(default_factory=list)
    timings_ms: dict[str, int] = Field(default_factory=dict)
