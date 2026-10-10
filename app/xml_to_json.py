"""
Парсер nsiKTRU XML → JSON.

Правила:
  - только ACTIVE позиции;
  - только позиции, чьё name есть в файле целевых наименований;
  - характеристики с actual=false отбрасываются;
  - value с <rangeSet> → is_range=true; без → is_quality=true;
  - OKEI у value ищется в любом месте под <value>;
  - ktru_code — только у позиции; id — у OKEI, характеристики, value.

Вход:
  - config.ktru_file_paths (список путей к .xml или .zip)
  - names_clothing_furniture_tools.txt (одно имя на строку, UTF-8)

Выход:
  - ktru_db.json
"""

import json
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

from config import ktru_file_paths


# ----------------------- НАСТРОЙКИ -----------------------
NAMES_FILE  = Path("names_clothing_furniture_tools.txt")
OUTPUT_JSON = Path("ktru_db.json")
MATCH_MODE  = "exact"          # "exact" | "contains"
SKIP_NOT_ACTUAL = True         # пропускать файлы, в имени которых 'not-actual'
# ---------------------------------------------------------


# ============ НОРМАЛИЗАЦИЯ ============

_ws = re.compile(r"\s+")

def normalize(s):
    if s is None:
        return ""
    s = str(s).lower().replace("ё", "е")
    s = s.replace("\xa0", " ").replace("\u2009", " ").replace("\u202f", " ")
    return _ws.sub(" ", s).strip()


# ============ XML-УТИЛИТЫ ============

def localname(tag):
    if tag is None:
        return ""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def get_text(parent, name):
    if parent is None:
        return ""
    for child in parent:
        if localname(child.tag) == name:
            return (child.text or "").strip()
    return ""


def find_child(parent, name):
    if parent is None:
        return None
    for child in parent:
        if localname(child.tag) == name:
            return child
    return None


def find_children(parent, name):
    if parent is None:
        return []
    return [c for c in parent if localname(c.tag) == name]


def to_float(s):
    if s is None or s == "":
        return None
    try:
        return float(str(s).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def to_bool(s):
    return str(s).strip().lower() == "true"


# ============ ЦЕЛЕВЫЕ ИМЕНА ============

def load_target_names(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Не найден {path}. Одно наименование на строку, UTF-8.")
    names = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                names.append(line)
    return names


def matches(name, targets_norm, mode):
    n = normalize(name)
    if mode == "exact":
        return n in targets_norm
    if mode == "contains":
        return any(t and t in n for t in targets_norm if t)
    raise ValueError(f"Неизвестный MATCH_MODE: {mode}")


# ============ ПАРСИНГ ============

def parse_okei_list(container_elem):
    """<oos:OKEIs> → [{'id','name'}, ...]"""
    result = []
    if container_elem is None:
        return result
    for okei in find_children(container_elem, "OKEI"):
        code = get_text(okei, "code")
        name = get_text(okei, "name")
        if code or name:
            result.append({"id": code, "name": name})
    return result


def extract_okeis_from_value(value_elem):
    """Все OKEI под <oos:value> на любой глубине, без дублей."""
    result = []
    seen = set()
    for child in value_elem.iter():
        if localname(child.tag) != "OKEI":
            continue
        code = get_text(child, "code")
        name = get_text(child, "name")
        if not code and not name:
            continue
        key = (code, name)
        if key in seen:
            continue
        seen.add(key)
        result.append({"id": code, "name": name})
    return result


def extract_range(value_elem):
    """Первый <valueRange> внутри <rangeSet>, или None."""
    range_set = find_child(value_elem, "rangeSet")
    if range_set is None:
        return None
    vrs = find_children(range_set, "valueRange")
    if not vrs:
        return None
    vr = vrs[0]
    return {
        "min_notation": get_text(vr, "minMathNotation") or None,
        "min_value":    to_float(get_text(vr, "min")),
        "max_notation": get_text(vr, "maxMathNotation") or None,
        "max_value":    to_float(get_text(vr, "max")),
    }


def extract_quality_description(value_elem):
    """name → descriptionValue → code → valueCode → прямой текст."""
    for tag in ("name", "descriptionValue", "code", "valueCode"):
        txt = get_text(value_elem, tag)
        if txt:
            return txt
    return (value_elem.text or "").strip() or None


def parse_value(value_elem, char_code, vi):
    okeis = extract_okeis_from_value(value_elem)
    rng = extract_range(value_elem)
    is_range = rng is not None
    is_quality = not is_range
    quality_description = extract_quality_description(value_elem) if is_quality else None
    return {
        "id":                  f"{char_code}-v{vi}",
        "is_range":            is_range,
        "range":               rng,
        "is_quality":          is_quality,
        "quality_description": quality_description,
        "okeis":               okeis,
    }


def parse_characteristic(char_elem, ci):
    actual = to_bool(get_text(char_elem, "actual"))
    if not actual:
        return None
    code = get_text(char_elem, "code") or f"char-{ci}"
    name = get_text(char_elem, "name")
    required = to_bool(get_text(char_elem, "isRequired"))

    values = []
    values_container = find_child(char_elem, "values")
    if values_container is not None:
        for vi, v_elem in enumerate(find_children(values_container, "value")):
            values.append(parse_value(v_elem, code, vi))

    return {
        "id":       code,
        "name":     name,
        "required": required,
        "values":   values,
    }


def parse_position(pos_elem):
    data = find_child(pos_elem, "data")
    if data is None:
        return None

    code = get_text(data, "code")
    name = get_text(data, "name")
    if not code or not name:
        return None

    # OKPD2
    okpd2 = None
    okpd2_elem = find_child(data, "OKPD2")
    if okpd2_elem is not None:
        okpd2_code = get_text(okpd2_elem, "code")
        okpd2_name = get_text(okpd2_elem, "name")
        if okpd2_code or okpd2_name:
            okpd2 = {"id": okpd2_code, "name": okpd2_name}

    # OKEI позиции
    okeis = parse_okei_list(find_child(data, "OKEIs"))

    # Характеристики
    characteristics = []
    chars_container = find_child(data, "characteristics")
    if chars_container is not None:
        for ci, char_elem in enumerate(find_children(chars_container, "characteristic")):
            char = parse_characteristic(char_elem, ci)
            if char is not None:
                characteristics.append(char)

    return {
        "ktru_code":       code,
        "name":            name,
        "okpd2":           okpd2,
        "okeis":           okeis,
        "characteristics": characteristics,
    }


def iter_positions(root):
    """Все <oos:position> в дереве, независимо от namespace."""
    for elem in root.iter():
        if localname(elem.tag) == "position":
            yield elem


def parse_xml_bytes(xml_bytes: bytes, targets_norm, match_mode):
    """Парсит XML-байты, возвращает список подходящих dict-позиций."""
    root = ET.fromstring(xml_bytes)
    result = []
    for pos_elem in iter_positions(root):
        data = find_child(pos_elem, "data")
        if data is None:
            continue

        # Только ACTIVE
        if get_text(data, "status") != "ACTIVE":
            continue

        # Фильтр по имени
        name = get_text(data, "name")
        if not name or not matches(name, targets_norm, match_mode):
            continue

        pos = parse_position(pos_elem)
        if pos is not None:
            result.append(pos)
    return result


def iter_xml_from_zip(path: Path):
    if path.suffix.lower() != ".zip":
        return
    with zipfile.ZipFile(path) as zf:
        for inner in zf.namelist():
            if inner.lower().endswith(".xml"):
                with zf.open(inner) as f:
                    yield inner, f.read()


# ============ ГЛАВНОЕ ============

def parse_export_xml(ktru_paths: list[Path]):
    target_names = load_target_names(NAMES_FILE)
    targets_norm = {normalize(n) for n in target_names}
    print(f"Наименований в файле: {len(target_names)}")

    paths = [Path(p) for p in ktru_paths]
    print(f"Путей в config: {len(paths)}")

    positions_by_ktru_code = {}
    matched_names = set()

    for i, path in enumerate(paths, 1):
        if SKIP_NOT_ACTUAL and "not-actual" in path.name.lower():
            continue

        try:
            if path.suffix.lower() == ".zip":
                for xml_name, xml_bytes in iter_xml_from_zip(path):
                    if SKIP_NOT_ACTUAL and "not-actual" in xml_name.lower():
                        continue
                    for pos in parse_xml_bytes(xml_bytes, targets_norm, MATCH_MODE):
                        matched_names.add(pos["name"])
                        positions_by_ktru_code.setdefault(pos["ktru_code"], pos)
            elif path.suffix.lower() == ".xml":
                xml_bytes = path.read_bytes()
                for pos in parse_xml_bytes(xml_bytes, targets_norm, MATCH_MODE):
                    matched_names.add(pos["name"])
                    positions_by_ktru_code.setdefault(pos["ktru_code"], pos)
            else:
                print(f"  [{i}/{len(paths)}] пропущен {path.name}: неизвестный формат")
                continue
        except Exception as e:
            print(f"  [{i}/{len(paths)}] {path.name}: ошибка {e}")
            continue

        print(f"  [{i}/{len(paths)}] {path.name}")

    result = {"positions": list(positions_by_ktru_code.values())}

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # --- статистика ---
    total_chars = total_values = total_ranges = 0
    values_with_okei = values_without_okei = 0
    for p in result["positions"]:
        for c in p["characteristics"]:
            total_chars += 1
            for v in c["values"]:
                total_values += 1
                if v["is_range"]:
                    total_ranges += 1
                if v["okeis"]:
                    values_with_okei += 1
                else:
                    values_without_okei += 1

    not_found = sorted(set(target_names) - matched_names, key=normalize)

    print(f"\n=== Итог ===")
    print(f"Уникальных кодов в JSON:      {len(result['positions'])}")
    print(f"Уникальных наименований:      {len(matched_names)} из {len(target_names)}")
    print(f"Характеристик:                {total_chars}")
    print(f"Значений (value):             {total_values}")
    print(f"  с range:                    {total_ranges}")
    print(f"  с OKEI:                     {values_with_okei}")
    print(f"  без OKEI:                   {values_without_okei}")
    print(f"\nНе найдено в XML ({len(not_found)}):")
    for n in not_found[:50]:
        print(f"  - {n}")
    if len(not_found) > 50:
        print(f"  ... и ещё {len(not_found) - 50}")
    print(f"\nФайл: {OUTPUT_JSON.resolve()}")

    return result


if __name__ == "__main__":
    parse_export_xml(ktru_file_paths)