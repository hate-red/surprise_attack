import json
import re
from pathlib import Path

import pandas as pd


# ============================================================
# 1. НАСТРОЙКИ
# ============================================================
EXCEL_DIR       = Path(r"C:\Users\isymb\OneDrive\Desktop\CodePack\TenderHack\excel_clean")
UNITS_MAP       = Path("Units_unified.txt")            # унификация
UNITS_FORBIDDEN = Path("Units_to_remove.txt")      # ЧЁРНЫЙ список
OUTPUT_JSON     = Path("categories.json")

COL_CATEGORY = "Конечная категория ПП"
COL_NAME     = "Название характеристики"
COL_TYPE     = "Тип характеристики"
COL_UNITS    = "Единица измерения"

NAME_MIN_LEN = 0
NAME_MAX_LEN = 40
MIN_CHARS_PER_CATEGORY = 0

READ_ALL_SHEETS = True
# ============================================================


# ============================================================
# 2. НОРМАЛИЗАЦИЯ
# ============================================================

def normalize(s):
    if s is None:
        return ""
    s = str(s).lower().replace("ё", "е").replace("\xa0", " ")
    s = s.replace(".", "")
    return " ".join(s.split()).strip()


def normalize_header(s):
    if s is None:
        return ""
    s = str(s).lower().replace("ё", "е").replace("\xa0", " ")
    return " ".join(s.split()).strip()


# ============================================================
# 3. ПОИСК КОЛОНОК
# ============================================================

def find_column(columns, target):
    if target is None:
        return None
    t = normalize_header(target)
    for col in columns:
        if normalize_header(col) == t:
            return col
    for col in columns:
        if t in normalize_header(col):
            return col
    return None


# ============================================================
# 4. СПРАВОЧНИКИ
# ============================================================

def load_units_map(path: Path, debug: bool = False) -> dict:
    """units_map.txt → {нормализованный_вариант: унифицированное}."""
    mapping = {}
    if not path.exists():
        print(f"⚠ Справочник не найден: {path}")
        return mapping

    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        m = re.match(r"^(.*?)\s*\((.*)\)\s*\.?\s*$", line)
        if m:
            unified = m.group(1).strip()
            variants = [v.strip() for v in re.split(r"[;,/]", m.group(2)) if v.strip()]
        else:
            unified, variants = None, []
            for sep in (":", " - ", " — ", " = ", "\t"):
                if sep in line:
                    left, right = line.split(sep, 1)
                    unified = left.strip()
                    variants = [v.strip() for v in re.split(r"[;,/]", right) if v.strip()]
                    break
            if unified is None:
                unified = line
                variants = []

        for v in [unified] + variants:
            key = normalize(v)
            if key:
                mapping[key] = unified

        if debug and lineno <= 10:
            print(f"  [{lineno}] unified={unified!r}, variants={variants}")

    return mapping


def load_units_forbidden(path: Path) -> set:
    """
    Чёрный список — по одному значению на строку.
    Возвращает set нормализованных значений.
    """
    forbidden = set()
    if not path.exists():
        print(f"⚠ Чёрный список не найден: {path}")
        return forbidden

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        forbidden.add(normalize(line))

    return forbidden


def unify_unit(raw, units_map: dict):
    """Пусто → None. Иначе — унифицированное значение (или исходное)."""
    key = normalize(raw)
    if not key:
        return None
    return units_map.get(key, str(raw).strip())


def is_unit_forbidden(unified_value, forbidden_set: set) -> bool:
    """True → строку удаляем. Пусто → False (не удаляем)."""
    if unified_value is None:
        return False
    return normalize(unified_value) in forbidden_set


# ============================================================
# 5. ПАРСИНГ EXCEL
# ============================================================

def collect_excel_files(root: Path):
    exts = {".xlsx", ".xls", ".xlsm"}
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in exts)


def read_sheets(path: Path):
    try:
        if READ_ALL_SHEETS:
            return pd.read_excel(path, sheet_name=None, dtype=str)
        return {0: pd.read_excel(path, sheet_name=0, dtype=str)}
    except Exception as e:
        print(f"  ✗ {path.name}: ошибка чтения — {e}")
        return {}


def extract_rows(df: pd.DataFrame):
    cat_col  = find_column(df.columns, COL_CATEGORY)
    name_col = find_column(df.columns, COL_NAME)
    type_col = find_column(df.columns, COL_TYPE)
    unit_col = find_column(df.columns, COL_UNITS)

    if cat_col is None or name_col is None:
        return []

    rows = []
    for _, row in df.iterrows():
        category = row[cat_col]
        category = str(category).strip() if pd.notna(category) else ""
        if not category:
            continue

        char_name = row[name_col]
        char_name = str(char_name).strip() if pd.notna(char_name) else ""

        char_type = ""
        if type_col is not None and pd.notna(row[type_col]):
            char_type = str(row[type_col]).strip()

        units = ""
        if unit_col is not None and pd.notna(row[unit_col]):
            units = str(row[unit_col]).strip()

        rows.append({
            "category": category,
            "type":     char_type,
            "name":     char_name,
            "units":    units,
        })

    return rows


# ============================================================
# 6. СБОРКА
# ============================================================

def is_valid_name(name: str) -> bool:
    if not name:
        return False
    return NAME_MIN_LEN <= len(name) <= NAME_MAX_LEN


def build_categories(rows, units_map, forbidden_set):
    tree = {}
    dropped = []

    for r in rows:
        cat  = r["category"]
        name = r["name"]
        typ  = r["type"]

        if not is_valid_name(name):
            dropped.append((cat, name, f"невалидное название (len={len(name)})"))
            continue

        unified_units = unify_unit(r["units"], units_map)

        if is_unit_forbidden(unified_units, forbidden_set):
            dropped.append(
                (cat, name, f"единица в чёрном списке: {unified_units!r}")
            )
            continue

        tree.setdefault(cat, {})
        key = (name, typ)
        if key not in tree[cat]:
            tree[cat][key] = {
                "name":          name,
                "type":          typ or None,
                "measure_units": unified_units,
            }

    return tree, dropped


def finalize(tree):
    result, skipped = [], []
    for category, chars in tree.items():
        chars_list = list(chars.values())
        if len(chars_list) < MIN_CHARS_PER_CATEGORY:
            skipped.append((category, len(chars_list)))
            continue
        result.append({
            "category":        category,
            "characteristics": chars_list,
        })
    result.sort(key=lambda x: x["category"])
    return result, skipped


# ============================================================
# 7. ГЛАВНОЕ
# ============================================================

def main():
    units_map       = load_units_map(UNITS_MAP)
    units_forbidden = load_units_forbidden(UNITS_FORBIDDEN)
    print(f"Правил унификации:     {len(units_map)}")
    print(f"Запрещённых единиц:    {len(units_forbidden)}")

    files = collect_excel_files(EXCEL_DIR)
    print(f"Excel-файлов:          {len(files)}")
    if not files:
        raise SystemExit(f"Excel-файлов нет в {EXCEL_DIR}")

    all_rows = []
    for i, path in enumerate(files, 1):
        sheets = read_sheets(path)
        file_rows = 0
        for _, df in sheets.items():
            rows = extract_rows(df)
            all_rows.extend(rows)
            file_rows += len(rows)
        print(f"  [{i}/{len(files)}] {path.name}: {file_rows} строк")

    print(f"Всего строк: {len(all_rows)}")

    tree, dropped = build_categories(all_rows, units_map, units_forbidden)
    print(f"Строк отброшено: {len(dropped)}")
    for cat, name, reason in dropped[:10]:
        print(f"    × [{cat}] {name!r}: {reason}")
    if len(dropped) > 10:
        print(f"    ... и ещё {len(dropped) - 10}")

    categories, skipped = finalize(tree)
    print(f"\nКатегорий в JSON:      {len(categories)}")
    print(f"Отброшено (< {MIN_CHARS_PER_CATEGORY}):  {len(skipped)}")
    for cat, n in skipped[:10]:
        print(f"    - {cat} ({n})")
    if len(skipped) > 10:
        print(f"    ... и ещё {len(skipped) - 10}")

    OUTPUT_JSON.write_text(
        json.dumps({"categories": categories}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total_chars = sum(len(c["characteristics"]) for c in categories)
    print(f"\n=== Итог ===")
    print(f"Категорий:             {len(categories)}")
    print(f"Характеристик:         {total_chars}")
    print(f"\nФайл: {OUTPUT_JSON.resolve()}")


if __name__ == "__main__":
    main()