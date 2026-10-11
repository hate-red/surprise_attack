"""
Адаптер ответа LLM (Qwen, app/services/get_evals.py) к детерминированному конвейеру.

LLM возвращает два JSON: {"name": ...} и {"характеристика": "значение", ...}.
Конвейер разбирает текст, поэтому JSON превращается в описание, которое он понимает
лучше всего: наименование и пары «характеристика: значение», разделённые «;».
Конвейер режет текст на сегменты по «,» «;» и переводам строк, и каждое значение
остаётся рядом со своей характеристикой. Слитная строка «name char1 val1 char2 val2»
этого не даёт: значения «перетекают» к соседним характеристикам.

Всё, что может сломаться на стороне LLM (нет модели, таймаут, невалидный JSON,
```json-обёртка, null вместо наименования), даёт None — анализ идёт по исходному тексту.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field, replace

logger = logging.getLogger(__name__)

# «регулировка по высоте: есть» -> «регулировка по высоте» (признак есть),
# «подлокотники: нет» -> «без подлокотники» (конвейер читает «без …» как «Нет»)
YES_VALUES = {'да', 'есть', 'имеется', 'имеются', 'присутствует', 'присутствуют', 'true', 'yes', '+', 'наличие'}
NO_VALUES = {'нет', 'отсутствует', 'отсутствуют', 'false', 'no', '-', 'без', 'не имеется'}
# поля наименования, которые в JSON характеристик повторять не нужно
SKIP_KEYS = {'name', 'наименование', 'название', 'товар', 'model', 'модель', 'manufacturer',
             'производитель', 'country', 'страна', 'страна производства'}

# лимит ответа сервиса — 5–6 с; не успела модель — анализ идёт по исходному тексту,
# а её ответ, когда придёт, попадает в кэш и используется при следующем запросе
LLM_TIMEOUT_S = float(os.environ.get('LLM_TIMEOUT', '5'))
_CACHE_SIZE = 256


@dataclass(slots=True)
class LlmDescription:
    name: str | None
    pairs: list[tuple[str, str]] = field(default_factory=list)
    text: str = ''
    elapsed_ms: int = 0


def llm_enabled() -> bool:
    """LLM выключается переменной окружения LLM_ENABLED=0."""
    return os.environ.get('LLM_ENABLED', '1').lower() in ('1', 'true', 'yes', 'on')


# --------------------------------------------------------------------- JSON
def parse_llm_json(raw) -> dict:
    """JSON-объект из ответа модели: без ```json-обёртки, пояснений вокруг,
    висячих запятых. Не получилось — пустой dict."""
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    text = re.sub(r'```(?:json)?', '', str(raw), flags=re.IGNORECASE)
    start = text.find('{')
    if start < 0:
        return {}
    depth, in_string, escaped = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return _loads(text[start:i + 1])
    return _loads(text[start:] + '}' * depth)  # ответ оборвался по max_tokens


def _loads(chunk: str) -> dict:
    for candidate in (chunk, re.sub(r',\s*([}\]])', r'\1', chunk)):
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        return value if isinstance(value, dict) else {}
    return {}


# ------------------------------------------------------------------ описание
def _clean(text: str) -> str:
    text = ' '.join(str(text).replace(';', ' ').split())
    # «белый, синий» -> «белый и синий»: запятая с пробелом разрезала бы сегмент;
    # десятичная запятая «0,5» остаётся
    return re.sub(r'\s*,\s+', ' и ', text).strip(' ,.:')


def _value_text(value) -> str:
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'да' if value else 'нет'
    if isinstance(value, (int, float)):
        return str(int(value)) if float(value).is_integer() else str(value)
    if isinstance(value, (list, tuple)):
        return ' и '.join(v for v in (_value_text(x) for x in value) if v)
    if isinstance(value, dict):
        return ' '.join(f'{_clean(k)} {_value_text(v)}'.strip() for k, v in value.items())
    return _clean(value)


# ---------------------------------------------------------------- опора на текст
def _source_terms(text: str) -> tuple[list[str], set[str]]:
    from app.services.nlp.text import normalize_text, tokenize, word_stem
    tokens = tokenize(normalize_text(text))
    stems = [word_stem(t.norm) for t in tokens if t.is_word and len(t.norm) > 1]
    numbers = {t.norm.replace(',', '.') for t in tokens if t.is_number}
    return stems, numbers


def _grounded(phrase: str, stems: list[str], numbers: set[str], share: float = 0.5) -> bool:
    """Слова и числа фразы встречаются в исходном описании (с точностью до формы слова)."""
    from app.services.nlp.matching import stem_similarity
    from app.services.nlp.text import normalize_text, tokenize, word_stem
    tokens = [t for t in tokenize(normalize_text(phrase)) if (t.is_word and len(t.norm) > 2) or t.is_number]
    if not tokens:
        return True
    source_numbers = {float(n) for n in numbers if _is_float(n)}
    hits = 0
    for t in tokens:
        if t.is_number:
            value = t.norm.replace(',', '.')
            hits += (float(value) in source_numbers) if _is_float(value) else (value in numbers)
        else:
            stem = word_stem(t.norm)
            hits += any(stem_similarity(stem, s) > 0 for s in stems)
    return hits >= max(1, round(len(tokens) * share))


def _is_float(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def build_description(name_raw, chars_raw, source_text: str | None = None) -> LlmDescription | None:
    """Ответы LLM -> «Наименование; характеристика: значение; …» или None.

    С source_text (исходным описанием) остаются только наименование и значения, которые в
    нём действительно есть: модель не должна «дописывать» характеристики, которых
    пользователь не указывал, — иначе вместо честного «уточните» вышел бы выдуманный код."""
    name_obj = parse_llm_json(name_raw)
    chars_obj = parse_llm_json(chars_raw)
    name = _value_text(name_obj.get('name')) if name_obj else ''
    if name.lower() in ('null', 'none'):
        name = ''
    stems, numbers = _source_terms(source_text) if source_text else ([], set())
    if source_text and name and not _grounded(name, stems, numbers, share=0.3):
        logger.info('LLM: наименование «%s» не опирается на описание — пропущено', name)
        name = ''

    pairs: list[tuple[str, str]] = []
    parts: list[str] = [name] if name else []
    for key, value in chars_obj.items():
        key_text = _clean(key)
        value_text = _value_text(value)
        if not key_text or key_text.lower() in SKIP_KEYS or value_text.lower() in ('', 'null', 'none'):
            continue  # пустое значение: модель не нашла его в тексте
        lowered = value_text.lower()
        if source_text:
            # признак «есть/нет» проверяем по названию, остальное — по значению
            evidence = key_text if lowered in YES_VALUES | NO_VALUES else value_text
            if not _grounded(evidence, stems, numbers):
                logger.info('LLM: «%s: %s» нет в описании — пропущено', key_text, value_text)
                continue
        pairs.append((key_text, value_text))
        if lowered in YES_VALUES:
            parts.append(key_text)
        elif lowered in NO_VALUES:
            parts.append(f'без {key_text}')
        elif lowered.startswith(key_text.lower()):
            parts.append(value_text)
        else:
            parts.append(f'{key_text}: {value_text}')
    if not name and not pairs:
        return None
    return LlmDescription(name=name or None, pairs=pairs, text='; '.join(parts))


# ------------------------------------------------------------------ вызов LLM
_cache: OrderedDict[str, LlmDescription | None] = OrderedDict()
_pending: dict[str, asyncio.Task] = {}
_disabled_reason: str | None = None


async def describe_with_llm(text: str) -> LlmDescription | None:
    """Описание от LLM для текста (кэш + таймаут) или None.

    Повторные запросы с тем же текстом (правка значения в интерфейсе, «Обновить»)
    берут результат из кэша и не ждут модель."""
    if not llm_enabled() or _disabled_reason:
        return None
    key = ' '.join(text.split()).lower()
    if key in _cache:
        _cache.move_to_end(key)
        cached = _cache[key]
        return replace(cached, elapsed_ms=0) if cached is not None else None
    task = _pending.get(key)
    if task is None:
        task = asyncio.ensure_future(_generate(key, text))
        _pending[key] = task
    try:
        # shield: по таймауту генерация не прерывается и её результат попадёт в кэш
        return await asyncio.wait_for(asyncio.shield(task), timeout=LLM_TIMEOUT_S)
    except asyncio.TimeoutError:
        logger.warning('LLM не ответила за %.1f с — анализ по исходному тексту', LLM_TIMEOUT_S)
        return None


async def _generate(key: str, text: str) -> LlmDescription | None:
    global _disabled_reason
    started = time.perf_counter()
    try:
        from app.services import get_evals  # llama_cpp загружается только при включённой LLM
        name_raw, chars_raw = await asyncio.to_thread(get_evals.generate, text)
    except (ImportError, FileNotFoundError, ValueError) as exc:
        # нет llama_cpp или файла модели: не пытаемся на каждом запросе
        _disabled_reason = f'{type(exc).__name__}: {exc}'
        logger.warning('LLM отключена: %s', _disabled_reason)
        return None
    except Exception:  # noqa: BLE001 — ошибка модели не должна ронять анализ
        logger.exception('Ошибка LLM — анализ по исходному тексту')
        return None
    finally:
        _pending.pop(key, None)
    description = build_description(name_raw, chars_raw, source_text=text)
    if description is not None:
        description.elapsed_ms = int((time.perf_counter() - started) * 1000)
    logger.info('LLM за %d мс: %r -> %r', int((time.perf_counter() - started) * 1000), text,
                description.text if description else None)
    _cache[key] = description
    if len(_cache) > _CACHE_SIZE:
        _cache.popitem(last=False)
    return description
