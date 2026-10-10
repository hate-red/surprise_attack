from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, Any

class ParsedProductDTO(BaseModel):
    """
    DTO для хранения результата парсинга товара.
    """
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Название товара"
    )
    
    # Делаем значения строго строками, чтобы избежать проблем с БД/фронтендом
    specs: Dict[str, str] = Field(
        default_factory=dict, 
        description="Характеристики товара"
    )

    @field_validator('specs', mode='before')
    @classmethod
    def normalize_specs(cls, value: Any) -> Dict[str, str]:
        """
        Приводит все значения характеристик к строкам.
        Если LLM вернул {"ОЗУ": 16}, мы превратим это в {"ОЗУ": "16"}.
        """
        if not isinstance(value, dict):
            raise ValueError("specs должен быть словарем")
        
        return {str(k): str(v) for k, v in value.items()}

    @field_validator('name', mode='before')
    @classmethod
    def clean_name(cls, value: str) -> str:
        """Убираем лишние пробелы и кавычки по краям."""
        if isinstance(value, str):
            return value.strip().strip('"').strip("'")
        return value