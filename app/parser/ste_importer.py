"""
Импорт выгрузок портала поставщиков (СТЕ) — xlsx с колонками
"Конечная категория ПП", "Название характеристики", "Тип характеристики",
"Единица измерения" — в таблицы categories / additional_characteristics.

Это вспомогательный источник: он расширяет словарь формулировок
характеристик, но допустимые значения задаёт только справочник КТРУ.

Запуск (из корня проекта):
    python -m app.parser.ste_importer                         # все *.xlsx из "initial files"
    python -m app.parser.ste_importer путь/Одежда.xlsx путь/Мебель.xlsx

Единицы измерения унифицируются по app/parser/Units_unified.txt
(те же правила, что в Excel-parser.py); единицы из Units_to_remove.txt
считаются мусорными и не сохраняются (сама характеристика остаётся).
xlsx читается стандартной библиотекой (zipfile + XML), без pandas/openpyxl.
"""
from __future__ import annotations

import argparse
import asyncio
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

import asyncpg

from app.config import get_asyncpg_dsn, initial_files_dir


PARSER_DIR = Path(__file__).resolve().parent
UNITS_MAP_FILE = PARSER_DIR / 'Units_unified.txt'
UNITS_FORBIDDEN_FILE = PARSER_DIR / 'Units_to_remove.txt'

COL_CATEGORY = 'конечная категория пп'
COL_NAME = 'название характеристики'
COL_TYPE = 'тип характеристики'
COL_UNITS = 'единица измерения'

SHEET_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL_NS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
PKG_REL_NS = '{http://schemas.openxmlformats.org/package/2006/relationships}'


# ------------------------------------------------------------- нормализация
def normalize(s) -> str:
    if s is None:
        return ''
    s = str(s).lower().replace('ё', 'е').replace('\xa0', ' ')
    s = s.replace('.', '')
    return ' '.join(s.split()).strip()


def load_units_map(path: Path = UNITS_MAP_FILE) -> dict[str, str]:
    """Units_unified.txt -> {нормализованный_вариант: унифицированная_единица}."""
    mapping: dict[str, str] = {}
    if not path.exists():
        return mapping
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^(.*?)\s*\((.*)\)\s*\.?\s*$', line)
        if m:
            unified = m.group(1).strip()
            variants = [v.strip() for v in m.group(2).split(';') if v.strip()]  # '/' входит в сами единицы (г/м2)
        else:
            unified, variants = line, []
        for v in [unified] + variants:
            key = normalize(v)
            if key:
                mapping[key] = unified
    return mapping


def load_units_forbidden(path: Path = UNITS_FORBIDDEN_FILE) -> set[str]:
    if not path.exists():
        return set()
    return {
        normalize(line)
        for line in path.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.strip().startswith('#')
    }


def unify_unit(raw: str | None, units_map: dict[str, str], forbidden: set[str]) -> str | None:
    key = normalize(raw)
    if not key:
        return None
    unified = units_map.get(key, str(raw).strip())
    if normalize(unified) in forbidden:
        return None
    return unified


# ------------------------------------------------------------- чтение xlsx
def _col_index(cell_ref: str) -> int:
    letters = ''.join(ch for ch in cell_ref if ch.isalpha())
    index = 0
    for ch in letters:
        index = index * 26 + (ord(ch.upper()) - ord('A') + 1)
    return index - 1


def iter_xlsx_rows(path: Path):
    """Построчно отдаёт значения всех листов xlsx (списки строк)."""
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if 'xl/sharedStrings.xml' in zf.namelist():
            with zf.open('xl/sharedStrings.xml') as f:
                for _, el in ET.iterparse(f):
                    if el.tag == f'{SHEET_NS}si':
                        shared.append(''.join(t.text or '' for t in el.iter(f'{SHEET_NS}t')))
                        el.clear()

        workbook = ET.fromstring(zf.read('xl/workbook.xml'))
        rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
        targets = {r.get('Id'): r.get('Target') for r in rels.iter(f'{PKG_REL_NS}Relationship')}
        for sheet in workbook.iter(f'{SHEET_NS}sheet'):
            target = targets.get(sheet.get(f'{REL_NS}id'), '')
            sheet_path = target.lstrip('/') if target.startswith('/') else f'xl/{target}'
            with zf.open(sheet_path) as f:
                for _, row in ET.iterparse(f):
                    if row.tag != f'{SHEET_NS}row':
                        continue
                    values: list[str | None] = []
                    for cell in row.iter(f'{SHEET_NS}c'):
                        idx = _col_index(cell.get('r', 'A1'))
                        while len(values) < idx:
                            values.append(None)
                        cell_type = cell.get('t')
                        if cell_type == 'inlineStr':
                            text = ''.join(t.text or '' for t in cell.iter(f'{SHEET_NS}t'))
                        else:
                            v = cell.find(f'{SHEET_NS}v')
                            text = v.text if v is not None else None
                            if cell_type == 's' and text is not None:
                                text = shared[int(text)]
                        values.append(text.strip() if isinstance(text, str) and text.strip() else None)
                    yield values
                    row.clear()


def read_ste_file(path: Path) -> list[tuple[str, str, str, str | None]]:
    """-> [(категория, название характеристики, тип, единица), ...]"""
    rows: list[tuple[str, str, str, str | None]] = []
    header: dict[str, int] | None = None
    for values in iter_xlsx_rows(path):
        normalized = [normalize(v) for v in values]
        if COL_CATEGORY in normalized and COL_NAME in normalized:
            header = {name: normalized.index(name) for name in normalized if name}
            continue
        if header is None:
            continue

        def get(col: str) -> str | None:
            idx = header.get(col) if header else None
            return values[idx] if idx is not None and idx < len(values) else None

        category, name = get(COL_CATEGORY), get(COL_NAME)
        if not category or not name:
            continue
        rows.append((
            ' '.join(category.split()),
            ' '.join(name.split()),
            ' '.join((get(COL_TYPE) or '').split()),
            get(COL_UNITS),
        ))
    return rows


# --------------------------------------------------------------- загрузка
async def import_ste(paths: list[Path], dsn: str | None = None, verbose: bool = True) -> tuple[int, int]:
    units_map = load_units_map()
    forbidden = load_units_forbidden()

    categories: dict[str, int] = {}
    seen: set[tuple[int, str, str, str | None]] = set()
    characteristics: list[tuple[int, str, str, str | None, int]] = []
    for path in paths:
        file_rows = read_ste_file(path)
        if verbose:
            print(f'  {path.name}: {len(file_rows)} строк', flush=True)
        for category, name, kind, raw_unit in file_rows:
            category_id = categories.setdefault(category, len(categories) + 1)
            unit = unify_unit(raw_unit, units_map, forbidden)
            key = (category_id, name.lower().replace('ё', 'е'), kind, unit)
            if key in seen:
                continue
            seen.add(key)
            characteristics.append((len(characteristics) + 1, name, kind, unit, category_id))

    conn = await asyncpg.connect(dsn or get_asyncpg_dsn())
    try:
        async with conn.transaction():
            await conn.execute('TRUNCATE additional_characteristics, categories RESTART IDENTITY')
            await conn.copy_records_to_table(
                'categories',
                records=[(cid, name) for name, cid in categories.items()],
                columns=['id', 'name'],
            )
            await conn.copy_records_to_table(
                'additional_characteristics',
                records=characteristics,
                columns=['id', 'name', 'kind', 'measure_units', 'category_id'],
            )
            for table in ('categories', 'additional_characteristics'):
                await conn.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"
                )
    finally:
        await conn.close()

    if verbose:
        print(f'Категорий СТЕ: {len(categories)}, характеристик: {len(characteristics)}')
    return len(categories), len(characteristics)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Импорт характеристик СТЕ (xlsx) в PostgreSQL')
    parser.add_argument('files', nargs='*', type=Path, help='xlsx-файлы (по умолчанию все из "initial files")')
    args = parser.parse_args(argv)
    files = args.files or sorted(initial_files_dir.glob('*.xlsx'))
    if not files:
        raise SystemExit(f'Не найдено xlsx-файлов в {initial_files_dir}')
    asyncio.run(import_ste(files))


if __name__ == '__main__':
    main()
