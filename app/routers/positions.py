from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.positions import (
    PositionResponse,
    OKEIResponse,
    CharacteristicResponse,
    CharacteristicValueResponse
)
from app.repositories.positions import PositionRepository


router = APIRouter(prefix='/kgru-positions', tags=['Parsing'])


@router.get('/{kgru_id}')
async def get_position(kgru_id: str) -> PositionResponse | None:
    position = await PositionRepository.get_one_or_none(id=kgru_id)

    return position


@router.get('/{char_id}')
async def get_char(kgru_id: str) -> CharacteristicResponse | None:
    position = await PositionRepository.get_one_or_none(id=kgru_id)

    return position


# @router.post(
#     '/parse-message',
#     response_model=ParsedProductDTO,
#     status_code=status.HTTP_200_OK,
#     summary='Извлечь товар из текста'
# )
# async def parse_user_message(
#     payload: UserMessageDTO,
#     service: ProductParsingService = Depends(get_parsing_service)
# ):
#     raw_text = payload.message
    
#     try:
#         parsed_result = await service.extract_product(raw_text)
#         return parsed_result
        
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail='Ошибка при обработке сообщения'
#         )