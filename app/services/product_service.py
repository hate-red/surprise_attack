from __future__ import annotations
from pyaspeller import YandexSpeller


from typing import Any


mock_objects: list[dict[str, Any]] = [
    # ... ваш список без изменений ...
]


def check_typos_in_text(text: str) -> dict[str, Any]:
    """
    Заглушка. Когда подключите YandexSpeller — реализуйте здесь.
    """
    if not text or not isinstance(text, str):
        return {"has_typo": False, "suggestion": text}

    speller = YandexSpeller()
    fixed = speller.spelled(text)
    return {"has_typo": fixed != text, "suggestion": fixed}



class ProductParsingService:
    def __init__(self, llm_client=None, ner_model=None):
        self.llm = llm_client
        self.ner = ner_model

    async def get_validate(self, text: str) -> list[dict[str, Any]]:
        if len(text) < 3:
            raise ValueError("Слишком короткий текст, не похоже на запрос товара")

        typo_result = check_typos_in_text(text)
        if typo_result["has_typo"]:
            raise ValueError(
                f"Строка с опечаткой! Попробуйте ввести: {typo_result['suggestion']}"
            )

        return mock_objects

    def _parse_llm_response(self, raw_response: str) -> list[dict[str, Any]]:
        raise NotImplementedError


def get_parsing_service() -> ProductParsingService:
    return ProductParsingService(llm_client=None, ner_model=None)