from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request

from app.repositories.batches import ImportBatchRepository
from app.schemas.batches import BatchDetailOut, BatchItemDetailOut, BatchOut
from app.services.batch_service import CsvFormatError, parse_descriptions, schedule_batch


router = APIRouter(prefix='/batches', tags=['CSV batches'])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@router.post('', response_model=BatchOut, status_code=201)
async def upload_batch(
    request: Request,
    filename: Annotated[str, Query(min_length=1, max_length=255, description='Имя загружаемого файла')] = 'upload.csv',
) -> BatchOut:
    """Загрузка CSV (тело запроса — содержимое файла, одна колонка описаний).

    Пакет создаётся сразу, строки обрабатываются в фоне; прогресс — GET /batches/{id}.
    """
    raw = await request.body()
    if not raw:
        raise HTTPException(400, 'Пустой файл')
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, 'Файл больше 5 МБ')
    try:
        descriptions = parse_descriptions(raw)
    except CsvFormatError as exc:
        raise HTTPException(400, str(exc))
    batch = await ImportBatchRepository.create_with_items(filename, descriptions)
    schedule_batch(batch.id)
    return BatchOut.model_validate(batch)


@router.get('', response_model=list[BatchOut])
async def list_batches(limit: Annotated[int, Query(ge=1, le=100)] = 20) -> list[BatchOut]:
    return [BatchOut.model_validate(b) for b in await ImportBatchRepository.list_recent(limit)]


@router.get('/{batch_id}', response_model=BatchDetailOut)
async def get_batch(batch_id: int) -> BatchDetailOut:
    batch = await ImportBatchRepository.get_with_items(batch_id)
    if batch is None:
        raise HTTPException(404, 'Пакет не найден')
    return BatchDetailOut.model_validate(batch)


@router.get('/{batch_id}/items/{item_id}', response_model=BatchItemDetailOut)
async def get_batch_item(batch_id: int, item_id: int) -> BatchItemDetailOut:
    item = await ImportBatchRepository.get_item(batch_id, item_id)
    if item is None:
        raise HTTPException(404, 'Строка пакета не найдена')
    return BatchItemDetailOut.model_validate(item)
