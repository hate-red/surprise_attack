from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services import product_service
from app.schemas.positions import PositionResponse
from app.repositories.positions import PositionRepository


router = APIRouter(prefix="/kgru-positions", tags=["Parsing"])


def validate_user_input(
    user_input: Annotated[
        str,
        Query(
            min_length=3,
            max_length=1055,
            description="Строка запроса пользователя",
            examples=["найди смартфон Samsung 128 ГБ"],
        ),
    ],
) -> str:
    if not user_input.strip():
        raise HTTPException(400, "Строка не может состоять только из пробелов")
    if user_input.strip().isdigit():
        raise HTTPException(400, "Ожидается текст, а не одно число")
    return user_input.strip()


def check_typos(
    user_input: Annotated[str, Depends(validate_user_input)],
) -> str:
    # вызываем функцию модуля, а не метод сервиса
    result = product_service.check_typos_in_text(user_input)
    if result["has_typo"]:
        raise HTTPException(
            status_code=400,
            detail=f"{result['suggestion']}",
        )
    return user_input


@router.post("/parse", response_model=list[PositionResponse])
async def parse(
    user_input: Annotated[str, Depends(check_typos)],
) -> list[PositionResponse]:
    service = product_service.get_parsing_service()
    try:
        return await service.get_validate(user_input) # type: ignore
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{kgru_id}")
async def get_position(kgru_id: str):
    return await PositionRepository.get_one_by_id(id=kgru_id)

