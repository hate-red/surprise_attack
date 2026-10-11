"""
Пакетная обработка CSV с описаниями товаров (одна колонка — одно описание).

Строки сохраняются в import_batch_items и обрабатываются в фоне тем же
конвейером, что и POST /kgru-positions/parse. Статусы строк и прогресс
пакета читаются фронтендом через GET /batches/{id}.
"""
from __future__ import annotations

import asyncio
import csv
import io
import logging
import re

from app.models.batches import (
    BATCH_STATUS_DONE,
    BATCH_STATUS_ERROR,
    BATCH_STATUS_PROCESSING,
)
from app.repositories.batches import ImportBatchRepository
from app.services.product_service import get_parsing_service

logger = logging.getLogger(__name__)

MAX_ROWS = 2000
MAX_DESCRIPTION_LENGTH = 2000
HEADER_WORDS = {
    'описание', 'описание товара', 'наименование', 'наименование товара', 'товар',
    'description', 'name', 'product', 'текст', 'запрос',
}

_tasks: set[asyncio.Task] = set()
_running: set[int] = set()


class CsvFormatError(ValueError):
    pass


def decode_csv(raw: bytes) -> str:
    for encoding in ('utf-8-sig', 'cp1251'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise CsvFormatError('Не удалось определить кодировку файла (ожидается UTF-8 или Windows-1251).')


def parse_descriptions(raw: bytes) -> list[str]:
    """CSV с одной колонкой описаний -> список описаний.

    Строки в кавычках разбираются по правилам CSV; строки без кавычек берутся
    целиком, поэтому запятые внутри описания ("масса 0,5 кг, сталь") не
    разрывают его. Первая строка пропускается, если это заголовок.
    """
    text = decode_csv(raw)
    if not text.strip():
        raise CsvFormatError('Файл пуст.')
    sample = text[:4096]
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=';\t|').delimiter
    except csv.Error:
        delimiter = ','

    descriptions: list[str] = []
    for record in csv.reader(io.StringIO(text), delimiter=delimiter):
        cells = [c.strip() for c in record]
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue
        if delimiter == ',' and len(non_empty) > 1:
            # строка без кавычек: восстанавливаем исходный текст целиком
            description = ', '.join(non_empty)
            description = re.sub(r'(\d), (\d)', r'\1,\2', description)
        else:
            description = '; '.join(non_empty)
        description = ' '.join(description.split())
        descriptions.append(description[:MAX_DESCRIPTION_LENGTH])
    if descriptions and descriptions[0].strip().strip('"').lower() in HEADER_WORDS:
        descriptions = descriptions[1:]
    descriptions = [d for d in descriptions if len(d) >= 3]
    if not descriptions:
        raise CsvFormatError('В файле нет описаний товаров (строк длиной от 3 символов).')
    if len(descriptions) > MAX_ROWS:
        raise CsvFormatError(f'Слишком много строк: {len(descriptions)} (максимум {MAX_ROWS}).')
    return descriptions


async def process_batch(batch_id: int) -> None:
    if batch_id in _running:
        return
    _running.add(batch_id)
    service = get_parsing_service()
    try:
        await ImportBatchRepository.set_batch_status(batch_id, BATCH_STATUS_PROCESSING)
        for item_id in await ImportBatchRepository.pending_item_ids(batch_id):
            await ImportBatchRepository.set_item(item_id, status=BATCH_STATUS_PROCESSING)
            description = await ImportBatchRepository.get_item_description(item_id)
            try:
                result = await service.get_validate(description or '')
                await ImportBatchRepository.set_item(
                    item_id,
                    status=BATCH_STATUS_DONE,
                    result_status=result.status,
                    ktru_code=result.ktru_code,
                    candidates_count=result.candidates_total,
                    result=result.model_dump(mode='json'),
                    error=None,
                )
            except Exception as exc:  # строка с ошибкой не останавливает пакет
                logger.exception('batch %s item %s failed', batch_id, item_id)
                await ImportBatchRepository.set_item(item_id, status=BATCH_STATUS_ERROR, error=str(exc)[:500])
            await ImportBatchRepository.refresh_progress(batch_id)
        await ImportBatchRepository.set_batch_status(batch_id, BATCH_STATUS_DONE)
    except Exception as exc:
        logger.exception('batch %s failed', batch_id)
        await ImportBatchRepository.set_batch_status(batch_id, BATCH_STATUS_ERROR, str(exc)[:500])
    finally:
        _running.discard(batch_id)


def schedule_batch(batch_id: int) -> None:
    task = asyncio.create_task(process_batch(batch_id))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def resume_unfinished_batches() -> None:
    """После перезапуска сервера дообрабатывает незавершённые пакеты."""
    for batch_id in await ImportBatchRepository.unfinished_ids():
        schedule_batch(batch_id)
