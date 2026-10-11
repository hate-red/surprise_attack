from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.services import product_service
from app.services.ktru_index import load_index
from app.schemas.positions import ParseRequest, ParseResponse, PositionResponse
from app.repositories.positions import PositionRepository


router = APIRouter(prefix="/kgru-positions", tags=["Parsing"])


def validate_user_input(
    user_input: Annotated[
        str,
        Query(
            min_length=3,
            max_length=2000,
            description="Строка запроса пользователя",
            examples=["Стул ученический деревянный с регулировкой по высоте"],
        ),
    ],
) -> str:
    if not user_input.strip():
        raise HTTPException(400, "Строка не может состоять только из пробелов")
    if user_input.strip().isdigit():
        raise HTTPException(400, "Ожидается текст, а не одно число")
    return user_input.strip()


@router.post("/parse", response_model=ParseResponse)
async def parse(
    user_input: Annotated[str, Depends(validate_user_input)],
    body: Annotated[ParseRequest | None, Body()] = None,
) -> ParseResponse:
    """Анализ описания товара.

    Опечатки не блокируют анализ: они возвращаются в поле `spelling`
    вместе с исправленным текстом `corrected_query`. В теле запроса можно
    передать значения, изменённые или подтверждённые пользователем
    (`overrides`), удалённые характеристики (`excluded`) и выбранный код.
    """
    service = product_service.get_parsing_service()
    try:
        return await service.get_validate(user_input, body)
    except product_service.ReferenceNotLoadedError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/typos")
async def check_typos(user_input: Annotated[str, Depends(validate_user_input)]) -> dict:
    """Проверка опечаток по словарю КТРУ/СТЕ (без внешних сервисов)."""
    await load_index()
    return product_service.check_typos_in_text(user_input)


@router.post("/reload-index")
async def reload_index() -> dict:
    """Перестроить индекс после повторного импорта справочника."""
    index = await load_index(force=True)
    return index.stats


@router.get("/{kgru_id}", response_model=PositionResponse)
async def get_position(kgru_id: str) -> PositionResponse:
    position = await PositionRepository.get_one_by_id(id=kgru_id)
    if position is None:
        raise HTTPException(404, "Позиция КТРУ не найдена")
    return PositionResponse.model_validate(position)
