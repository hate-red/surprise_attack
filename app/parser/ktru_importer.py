"""
Импорт справочника КТРУ из выгрузок nsiKTRUNew в PostgreSQL.

Запуск (из корня проекта):
    python -m app.parser.ktru_importer                       # папка "initial files/xmls"
    python -m app.parser.ktru_importer --xml-dir путь/к/xml
    docker compose run --rm fastapi python -m app.parser.ktru_importer

Правила:
  - читаются только актуальные выгрузки nsiKTRUNew_all*actual*.xml;
    файлы *not-actual* / *not_actual* игнорируются;
  - загружаются только позиции со статусом ACTIVE;
  - характеристики с <actual>false</actual> пропускаются;
  - каждое значение сохраняется ровно в том виде, в каком оно задано в XML:
      * <qualityDescription>        -> качественное значение (is_quality)
      * <rangeSet><valueRange>      -> диапазон NUMRANGE c учётом
                                       строгих/нестрогих границ (is_range)
      * <valueSet><concreteValue>   -> точное число (concrete_value)
    единица измерения значения (<OKEI>) хранится в measure_units и в связи
    characteristic_value_okei;
  - ничего не придумывается: если в XML нет ограничений, в БД их тоже нет.

Таблицы КТРУ (positions, characteristics, characteristic_values, okei и
связи) очищаются и загружаются заново в одной транзакции: при ошибке
в базе остаётся прежнее состояние.
"""
from __future__ import annotations

import argparse
import asyncio
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET

import asyncpg

from app.config import get_asyncpg_dsn, ktru_xml_dir


NS = '{http://zakupki.gov.ru/oos/types/1}'

ACTUAL_EXPORT_RE = re.compile(r'^nsiKTRUNew_all.*actual.*\.xml$', re.IGNORECASE)
NOT_ACTUAL_RE = re.compile(r'not[-_]?actual', re.IGNORECASE)

MIN_NOTATION = {'greater': '>', 'greaterOrEqual': '≥'}
MAX_NOTATION = {'less': '<', 'lessOrEqual': '≤'}


def is_actual_export(filename: str) -> bool:
    return bool(ACTUAL_EXPORT_RE.match(filename)) and not NOT_ACTUAL_RE.search(filename)


def _text(elem: ET.Element | None, path: str) -> str | None:
    if elem is None:
        return None
    found = elem.find(path)
    if found is None or found.text is None:
        return None
    value = found.text.strip()
    return value or None


def _bool(value: str | None) -> bool:
    return (value or '').strip().lower() == 'true'


def _int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value.replace(',', '.').replace(' ', ''))
    except InvalidOperation:
        return None


def _datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=None)
    except ValueError:
        return None


def _fmt_number(value: Decimal) -> str:
    text = format(value.normalize(), 'f') if value == value.to_integral() else format(value, 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text.replace('.', ',')


@dataclass
class ImportStats:
    files: int = 0
    positions_seen: int = 0
    positions_active: int = 0
    duplicates: int = 0
    characteristics: int = 0
    characteristics_not_actual: int = 0
    values_quality: int = 0
    values_range: int = 0
    values_concrete: int = 0
    values_empty: int = 0
    invalid_ranges: int = 0
    okei: int = 0


@dataclass
class Batch:
    positions: list[tuple] = field(default_factory=list)
    position_okei: list[tuple] = field(default_factory=list)
    characteristics: list[tuple] = field(default_factory=list)
    values: list[tuple] = field(default_factory=list)
    value_okei: list[tuple] = field(default_factory=list)
    new_okei: list[tuple] = field(default_factory=list)


class KtruXmlImporter:
    def __init__(self) -> None:
        self.stats = ImportStats()
        self.okei_ids: dict[str, int] = {}
        self.seen_codes: set[str] = set()
        self.next_char_id = 1
        self.next_value_id = 1

    # ---------------------------------------------------------------- OKEI
    def _okei_id(self, batch: Batch, code: str | None, name: str | None) -> int | None:
        if not code and not name:
            return None
        key = code or f'name:{name}'
        okei_id = self.okei_ids.get(key)
        if okei_id is None:
            okei_id = len(self.okei_ids) + 1
            self.okei_ids[key] = okei_id
            batch.new_okei.append((okei_id, name or code, code))
            self.stats.okei += 1
        return okei_id

    # ---------------------------------------------------------- positions
    def parse_position(self, data: ET.Element, batch: Batch) -> None:
        self.stats.positions_seen += 1
        if _text(data, f'{NS}status') != 'ACTIVE':
            return
        code = _text(data, f'{NS}code')
        name = _text(data, f'{NS}name')
        if not code or not name:
            return
        if code in self.seen_codes:
            self.stats.duplicates += 1
            return
        self.seen_codes.add(code)
        self.stats.positions_active += 1

        rubricators = [
            r.findtext(f'{NS}name') for r in data.iterfind(f'{NS}rubricators/{NS}rubricatorInfo')
        ]
        batch.positions.append((
            code,
            ' '.join(name.split()),
            _text(data, f'{NS}OKPD2/{NS}code'),
            _text(data, f'{NS}OKPD2/{NS}name'),
            'ACTIVE',
            _int(_text(data, f'{NS}version')),
            _bool(_text(data, f'{NS}isTemplate')),
            _text(data, f'{NS}parentPositionInfo/{NS}code'),
            _datetime(_text(data, f'{NS}applicationDateStart')),
            _datetime(_text(data, f'{NS}applicationDateEnd')),
            '; '.join(r for r in rubricators if r) or None,
        ))

        seen_okei: set[int] = set()
        for okei in data.iterfind(f'{NS}OKEIs/{NS}OKEI'):
            okei_id = self._okei_id(batch, _text(okei, f'{NS}code'), _text(okei, f'{NS}name'))
            if okei_id is not None and okei_id not in seen_okei:
                seen_okei.add(okei_id)
                batch.position_okei.append((code, okei_id))

        for char in data.iterfind(f'{NS}characteristics/{NS}characteristic'):
            self.parse_characteristic(code, char, batch)

    def parse_characteristic(self, position_code: str, char: ET.Element, batch: Batch) -> None:
        if not _bool(_text(char, f'{NS}actual')):
            self.stats.characteristics_not_actual += 1
            return
        name = _text(char, f'{NS}name')
        if not name:
            return
        char_id = self.next_char_id
        self.next_char_id += 1
        self.stats.characteristics += 1
        batch.characteristics.append((
            char_id,
            ' '.join(name.split()),
            _bool(_text(char, f'{NS}isRequired')),
            _text(char, f'{NS}code'),
            _int(_text(char, f'{NS}type')),
            _int(_text(char, f'{NS}kind')),
            _int(_text(char, f'{NS}choiceType')),
            position_code,
        ))
        for value in char.iterfind(f'{NS}values/{NS}value'):
            self.parse_value(char_id, value, batch)

    def _add_value(self, batch: Batch, char_id: int, okei_ids: list[int], **columns) -> None:
        value_id = self.next_value_id
        self.next_value_id += 1
        batch.values.append((
            value_id,
            columns['name'],
            columns.get('measure_units'),
            columns.get('is_range', False),
            columns.get('range'),
            columns.get('is_quality', False),
            columns.get('quality_description'),
            columns.get('concrete_value'),
            columns.get('value_code'),
            columns.get('value_format'),
            char_id,
        ))
        for okei_id in okei_ids:
            batch.value_okei.append((value_id, okei_id))

    def parse_value(self, char_id: int, value: ET.Element, batch: Batch) -> None:
        value_code = _text(value, f'{NS}valueCode')
        value_format = _text(value, f'{NS}valueFormat')
        okei_ids: list[int] = []
        unit_names: list[str] = []
        for okei in value.iter(f'{NS}OKEI'):
            okei_code, okei_name = _text(okei, f'{NS}code'), _text(okei, f'{NS}name')
            okei_id = self._okei_id(batch, okei_code, okei_name)
            if okei_id is not None and okei_id not in okei_ids:
                okei_ids.append(okei_id)
                unit_names.append(okei_name or okei_code or '')
        unit = '; '.join(u for u in unit_names if u) or None
        unit_suffix = f' {unit}' if unit else ''

        common = dict(measure_units=unit, value_code=value_code, value_format=value_format)
        produced = False

        quality = _text(value, f'{NS}qualityDescription')
        if quality is not None:
            produced = True
            self.stats.values_quality += 1
            self._add_value(
                batch, char_id, okei_ids,
                name=' '.join(quality.split()), is_quality=True,
                quality_description=' '.join(quality.split()), **common,
            )

        for value_range in value.iterfind(f'{NS}rangeSet/{NS}valueRange'):
            produced = True
            min_value = _decimal(_text(value_range, f'{NS}min'))
            max_value = _decimal(_text(value_range, f'{NS}max'))
            min_notation = _text(value_range, f'{NS}minMathNotation')
            max_notation = _text(value_range, f'{NS}maxMathNotation')
            parts = []
            if min_value is not None:
                parts.append(f'{MIN_NOTATION.get(min_notation or "", "≥")} {_fmt_number(min_value)}')
            if max_value is not None:
                parts.append(f'{MAX_NOTATION.get(max_notation or "", "≤")} {_fmt_number(max_value)}')
            label = ' и '.join(parts) + unit_suffix if parts else (unit or 'диапазон')

            pg_range = None
            if min_value is not None and max_value is not None and min_value > max_value:
                # некорректный диапазон в источнике: не исправляем данные,
                # сохраняем подпись без числовых границ
                self.stats.invalid_ranges += 1
            else:
                pg_range = asyncpg.Range(
                    lower=min_value,
                    upper=max_value,
                    lower_inc=min_value is not None and min_notation != 'greater',
                    upper_inc=max_value is not None and max_notation != 'less',
                )
            self.stats.values_range += 1
            self._add_value(
                batch, char_id, okei_ids,
                name=label, is_range=True, range=pg_range, **common,
            )

        for concrete in value.iterfind(f'{NS}valueSet/{NS}concreteValue'):
            number = _decimal(concrete.text.strip() if concrete.text else None)
            if number is None:
                continue
            produced = True
            self.stats.values_concrete += 1
            self._add_value(
                batch, char_id, okei_ids,
                name=_fmt_number(number) + unit_suffix, concrete_value=number, **common,
            )

        if not produced:
            self.stats.values_empty += 1

    # -------------------------------------------------------------- files
    def parse_file(self, path: Path) -> Batch:
        batch = Batch()
        for _, elem in ET.iterparse(path, events=('end',)):
            if elem.tag != f'{NS}position':
                continue
            data = elem.find(f'{NS}data')
            if data is not None:
                self.parse_position(data, batch)
            elem.clear()
        return batch


POSITION_COLUMNS = [
    'id', 'name', 'okpd2_code', 'okpd2_name', 'status', 'version', 'is_template',
    'parent_code', 'application_date_start', 'application_date_end', 'rubricators',
]
CHARACTERISTIC_COLUMNS = [
    'id', 'name', 'required', 'code', 'char_type', 'kind', 'choice_type', 'position_id',
]
VALUE_COLUMNS = [
    'id', 'name', 'measure_units', 'is_range', 'range', 'is_quality',
    'quality_description', 'concrete_value', 'value_code', 'value_format',
    'characteristic_id',
]

KTRU_TABLES = (
    'characteristic_value_okei', 'characteristic_values', 'characteristics',
    'position_okei', 'positions', 'okei',
)


async def copy_batch(conn: asyncpg.Connection, batch: Batch) -> None:
    if batch.new_okei:
        await conn.copy_records_to_table('okei', records=batch.new_okei, columns=['id', 'name', 'code'])
    if batch.positions:
        await conn.copy_records_to_table('positions', records=batch.positions, columns=POSITION_COLUMNS)
    if batch.position_okei:
        await conn.copy_records_to_table(
            'position_okei', records=batch.position_okei, columns=['position_id', 'okei_id'])
    if batch.characteristics:
        await conn.copy_records_to_table(
            'characteristics', records=batch.characteristics, columns=CHARACTERISTIC_COLUMNS)
    if batch.values:
        await conn.copy_records_to_table(
            'characteristic_values', records=batch.values, columns=VALUE_COLUMNS)
    if batch.value_okei:
        await conn.copy_records_to_table(
            'characteristic_value_okei', records=batch.value_okei,
            columns=['characteristic_value_id', 'okei_id'])


def find_export_files(xml_dir: Path) -> list[Path]:
    return sorted(p for p in xml_dir.glob('*.xml') if is_actual_export(p.name))


async def import_ktru(xml_dir: Path, dsn: str | None = None, verbose: bool = True) -> ImportStats:
    files = find_export_files(xml_dir)
    if not files:
        raise FileNotFoundError(f'В {xml_dir} нет файлов nsiKTRUNew_all*actual*.xml')
    skipped = sorted(p.name for p in xml_dir.glob('*.xml') if not is_actual_export(p.name))

    importer = KtruXmlImporter()
    conn = await asyncpg.connect(dsn or get_asyncpg_dsn())
    started = time.perf_counter()
    try:
        async with conn.transaction():
            await conn.execute(f'TRUNCATE {", ".join(KTRU_TABLES)} RESTART IDENTITY')
            for index, path in enumerate(files, 1):
                batch = importer.parse_file(path)
                await copy_batch(conn, batch)
                importer.stats.files += 1
                if verbose:
                    print(
                        f'  [{index}/{len(files)}] {path.name}: +{len(batch.positions)} позиций, '
                        f'+{len(batch.characteristics)} характеристик, +{len(batch.values)} значений',
                        flush=True,
                    )
            for table in ('okei', 'characteristics', 'characteristic_values'):
                await conn.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"
                )
        await conn.execute('ANALYZE positions, characteristics, characteristic_values, okei')
    finally:
        await conn.close()

    if verbose:
        s = importer.stats
        print('\n=== Импорт КТРУ завершён ===')
        print(f'Файлов загружено:            {s.files}')
        if skipped:
            print(f'Файлов пропущено (не actual): {len(skipped)}')
        print(f'Позиций в выгрузке:          {s.positions_seen}')
        print(f'Позиций ACTIVE загружено:    {s.positions_active}')
        print(f'Дубликатов кодов пропущено:  {s.duplicates}')
        print(f'Характеристик:               {s.characteristics} '
              f'(неактуальных пропущено: {s.characteristics_not_actual})')
        print(f'Значений качественных:       {s.values_quality}')
        print(f'Значений-диапазонов:         {s.values_range} (некорректных границ: {s.invalid_ranges})')
        print(f'Значений точных чисел:       {s.values_concrete}')
        print(f'Значений без содержимого:    {s.values_empty}')
        print(f'Единиц ОКЕИ:                 {s.okei}')
        print(f'Время: {time.perf_counter() - started:.1f} c')
    return importer.stats


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Импорт КТРУ (nsiKTRUNew XML) в PostgreSQL')
    parser.add_argument('--xml-dir', type=Path, default=ktru_xml_dir,
                        help='папка с файлами nsiKTRUNew_all_actual_*.xml')
    args = parser.parse_args(argv)
    if not args.xml_dir.is_dir():
        sys.exit(f'Папка не найдена: {args.xml_dir}')
    asyncio.run(import_ktru(args.xml_dir))


if __name__ == '__main__':
    main()
