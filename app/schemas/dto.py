from pydantic import BaseModel, Field
from typing import Dict, Any

class UserMessageDTO(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)

class ParsedProductDTO(BaseModel):
    name: str = Field(..., min_length=1)
    specs: Dict[str, str] = Field(default_factory=dict)