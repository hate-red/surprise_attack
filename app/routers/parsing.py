from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.dto import UserMessageDTO, ParsedProductDTO
from app.services.product_service import ProductParsingService, get_parsing_service

router = APIRouter(prefix="/api/v1", tags=["Parsing"])

@router.post(
    "/parse-message",
    response_model=ParsedProductDTO,
    status_code=status.HTTP_200_OK,
    summary="Извлечь товар из текста"
)
async def parse_user_message(
    payload: UserMessageDTO,
    service: ProductParsingService = Depends(get_parsing_service)
):
    raw_text = payload.message
    
    try:
        parsed_result = await service.extract_product(raw_text)
        return parsed_result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обработке сообщения"
        )