"""
Единицы измерения: справочник ОКЕИ из КТРУ + написания в свободном тексте.

Каждая единица относится к физической величине (dimension) и имеет
коэффициент перевода в базовую единицу этой величины. Это позволяет
сравнить "45 см" со значением КТРУ "≥ 400 и < 500 Миллиметр".
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Unit:
    key: str
    symbol: str
    dimension: str
    factor: float  # множитель к базовой единице величины


_UNITS = [
    # длина (база — мм)
    Unit('nm', 'нм', 'length', 1e-6), Unit('um', 'мкм', 'length', 1e-3),
    Unit('mm', 'мм', 'length', 1.0), Unit('cm', 'см', 'length', 10.0),
    Unit('dm', 'дм', 'length', 100.0), Unit('m', 'м', 'length', 1000.0),
    Unit('km', 'км', 'length', 1e6), Unit('inch', 'дюйм', 'length', 25.4),
    # масса (база — г)
    Unit('mg', 'мг', 'mass', 1e-3), Unit('g', 'г', 'mass', 1.0),
    Unit('kg', 'кг', 'mass', 1000.0), Unit('t', 'т', 'mass', 1e6),
    # объём (база — мл)
    Unit('mm3', 'мм³', 'volume', 1e-3), Unit('ml', 'мл', 'volume', 1.0),
    Unit('l', 'л', 'volume', 1000.0), Unit('m3', 'м³', 'volume', 1e6),
    # площадь (база — мм²)
    Unit('mm2', 'мм²', 'area', 1.0), Unit('cm2', 'см²', 'area', 100.0),
    Unit('m2', 'м²', 'area', 1e6), Unit('km2', 'км²', 'area', 1e12),
    Unit('ha', 'га', 'area', 1e10),
    # поверхностная плотность (ткани)
    Unit('gm2', 'г/м²', 'areal_density', 1.0),
    # плотность
    Unit('kgm3', 'кг/м³', 'density', 1.0),
    # мощность (база — Вт)
    Unit('w', 'Вт', 'power', 1.0), Unit('kw', 'кВт', 'power', 1e3),
    Unit('mw', 'МВт', 'power', 1e6), Unit('hp', 'л.с.', 'power', 735.49875),
    Unit('va', 'В·А', 'apparent_power', 1.0), Unit('kva', 'кВ·А', 'apparent_power', 1e3),
    # электричество
    Unit('v', 'В', 'voltage', 1.0), Unit('kv', 'кВ', 'voltage', 1e3),
    Unit('ma', 'мА', 'current', 1e-3), Unit('a', 'А', 'current', 1.0),
    Unit('mah', 'мА·ч', 'charge', 1e-3), Unit('ah', 'А·ч', 'charge', 1.0),
    Unit('ohm', 'Ом', 'resistance', 1.0),
    # частота
    Unit('hz', 'Гц', 'frequency', 1.0), Unit('khz', 'кГц', 'frequency', 1e3),
    Unit('mhz', 'МГц', 'frequency', 1e6), Unit('ghz', 'ГГц', 'frequency', 1e9),
    Unit('rpm', 'об/мин', 'rotation', 1.0), Unit('rps', 'об/с', 'rotation', 60.0),
    # время (база — с)
    Unit('us', 'мкс', 'time', 1e-6), Unit('ms', 'мс', 'time', 1e-3),
    Unit('s', 'с', 'time', 1.0), Unit('min', 'мин', 'time', 60.0),
    Unit('h', 'ч', 'time', 3600.0), Unit('day', 'сут', 'time', 86400.0),
    Unit('month', 'мес', 'calendar', 1.0), Unit('year', 'год', 'calendar', 12.0),
    # температура, углы, проценты
    Unit('degc', '°C', 'temperature', 1.0), Unit('kelvin', 'K', 'temperature_k', 1.0),
    Unit('deg', '°', 'angle', 1.0), Unit('arcmin', "'", 'angle', 1 / 60),
    Unit('arcsec', '"', 'angle', 1 / 3600),
    Unit('pct', '%', 'percent', 1.0),
    # штучные
    Unit('pcs', 'шт', 'count', 1.0), Unit('kpcs', 'тыс. шт', 'count', 1000.0),
    Unit('pair', 'пар', 'pair', 1.0), Unit('person', 'чел', 'person', 1.0),
    Unit('sheet', 'лист', 'sheet', 1.0), Unit('unit', 'ед', 'unit', 1.0),
    Unit('point', 'балл', 'point', 1.0), Unit('rub', 'руб', 'money', 1.0),
    # информация
    Unit('bit', 'бит', 'data', 0.125), Unit('byte', 'байт', 'data', 1.0),
    Unit('kb', 'КБ', 'data', 1024.0), Unit('mb', 'МБ', 'data', 1024.0 ** 2),
    Unit('gb', 'ГБ', 'data', 1024.0 ** 3), Unit('tb', 'ТБ', 'data', 1024.0 ** 4),
    Unit('bps', 'бит/с', 'data_rate', 1.0), Unit('kbps', 'Кбит/с', 'data_rate', 1e3),
    Unit('mbps', 'Мбит/с', 'data_rate', 1e6), Unit('gbps', 'Гбит/с', 'data_rate', 1e9),
    Unit('mbyteps', 'МБ/с', 'data_rate', 8e6), Unit('gbyteps', 'ГБ/с', 'data_rate', 8e9),
    # давление (база — Па)
    Unit('pa', 'Па', 'pressure', 1.0), Unit('kpa', 'кПа', 'pressure', 1e3),
    Unit('mpa', 'МПа', 'pressure', 1e6), Unit('bar', 'бар', 'pressure', 1e5),
    Unit('mbar', 'мбар', 'pressure', 100.0), Unit('atm', 'атм', 'pressure', 101325.0),
    Unit('mmhg', 'мм рт. ст.', 'pressure', 133.322), Unit('cmh2o', 'см вод. ст.', 'pressure', 98.0665),
    # энергия (база — Дж)
    Unit('j', 'Дж', 'energy', 1.0), Unit('kj', 'кДж', 'energy', 1e3),
    Unit('wh', 'Вт·ч', 'energy', 3600.0), Unit('kwh', 'кВт·ч', 'energy', 3.6e6),
    # прочее
    Unit('db', 'дБ', 'sound', 1.0), Unit('lm', 'лм', 'luminous_flux', 1.0),
    Unit('lx', 'лк', 'illuminance', 1.0), Unit('n', 'Н', 'force', 1.0),
    Unit('tesla', 'Тл', 'magnetic', 1.0),
    Unit('mps', 'м/с', 'speed', 1.0), Unit('kmh', 'км/ч', 'speed', 1 / 3.6),
    Unit('mph', 'м/ч', 'speed', 1 / 3600),
    Unit('m3h', 'м³/ч', 'flow', 1.0), Unit('m3s', 'м³/с', 'flow', 3600.0),
    Unit('km3day', 'тыс. м³/сут', 'flow', 1000 / 24), Unit('km3h', 'тыс. м³/ч', 'flow', 1000.0),
    Unit('th', 'т/ч', 'mass_flow', 1.0), Unit('tday', 'т/сут', 'mass_flow', 1 / 24),
    Unit('kgs', 'кг/с', 'mass_flow', 3.6),
    Unit('ktyear', 'тыс. т/год', 'mass_flow', 1000 / 8760), Unit('mtyear', 'млн т/год', 'mass_flow', 1e6 / 8760),
    Unit('ci', 'Ки', 'radioactivity', 1.0),
]
UNITS: dict[str, Unit] = {u.key: u for u in _UNITS}


# Наименования ОКЕИ из выгрузки КТРУ -> ключ единицы
OKEI_NAMES = {
    'миллиметр': 'mm', 'сантиметр': 'cm', 'дециметр': 'dm', 'метр': 'm',
    'погонный метр': 'm', 'километр; тысяча метров': 'km', 'нанометр': 'nm',
    'микрометр': 'um', 'дюйм (25,4 мм)': 'inch',
    'миллиграмм': 'mg', 'грамм': 'g', 'килограмм': 'kg',
    'тонна; метрическая тонна (1000 кг)': 't',
    'кубический миллиметр': 'mm3', 'кубический сантиметр; миллилитр': 'ml',
    'литр; кубический дециметр': 'l', 'кубический метр': 'm3',
    'квадратный миллиметр': 'mm2', 'квадратный сантиметр': 'cm2',
    'квадратный метр': 'm2', 'квадратный километр': 'km2', 'гектар': 'ha',
    'килограмм на кубический метр': 'kgm3',
    'ватт': 'w', 'киловатт': 'kw', 'мегаватт; тысяча киловатт': 'mw',
    'лошадиная сила': 'hp', 'вольт-ампер': 'va', 'киловольт-ампер': 'kva',
    'вольт': 'v', 'киловольт': 'kv', 'ампер': 'a', 'ампер-час (3,6 ккл)': 'ah',
    'ом': 'ohm', 'герц': 'hz', 'килогерц': 'khz', 'мегагерц': 'mhz', 'гигагерц': 'ghz',
    'оборот в минуту': 'rpm', 'оборот в секунду': 'rps',
    'микросекунда': 'us', 'миллисекунда': 'ms', 'секунда': 's', 'минута': 'min',
    'час': 'h', 'сутки': 'day', 'месяц': 'month', 'год': 'year',
    'градус цельсия': 'degc', 'кельвин': 'kelvin', 'градус (плоского угла)': 'deg',
    'минута (плоского угла)': 'arcmin', 'секунда (плоского угла)': 'arcsec',
    'процент': 'pct', 'штука': 'pcs', 'тысяча штук': 'kpcs', 'пара (2 шт.)': 'pair',
    'человек': 'person', 'лист': 'sheet', 'единица': 'unit', 'балл': 'point', 'рубль': 'rub',
    'бит': 'bit', 'байт': 'byte', 'килобайт': 'kb', 'мегабайт': 'mb', 'гигабайт': 'gb',
    'терабайт': 'tb', 'бит в секунду': 'bps', 'килобит в секунду': 'kbps',
    'мегабит в секунду': 'mbps', 'гигабит в секунду': 'gbps',
    'мегабайт в секунду': 'mbyteps', 'гигабайт в секунду': 'gbyteps',
    'паскаль': 'pa', 'килопаскаль': 'kpa', 'мегапаскаль': 'mpa', 'бар': 'bar',
    'миллибар': 'mbar', 'физическая атмосфера (101325 па)': 'atm',
    'миллиметр ртутного столба': 'mmhg', 'сантиметр водяного столба': 'cmh2o',
    'джоуль': 'j', 'килоджоуль': 'kj', 'ватт-час': 'wh', 'киловатт-час': 'kwh',
    'децибел': 'db', 'люмен': 'lm', 'люкс': 'lx', 'ньютон': 'n', 'тесла': 'tesla',
    'метр в секунду': 'mps', 'километр в час': 'kmh', 'метр в час': 'mph',
    'кубический метр в час': 'm3h', 'кубический метр в секунду': 'm3s',
    'тысяча кубических метров в сутки': 'km3day',
    'тонна в час': 'th', 'тонна в сутки': 'tday', 'килограмм в секунду': 'kgs',
    'тысяча метров кубических в час': 'km3h', 'тысяча тонн в год': 'ktyear',
    'миллион тонн в год': 'mtyear', 'кюри': 'ci',
}


def unit_from_okei(name: str | None) -> Unit | None:
    if not name:
        return None
    key = OKEI_NAMES.get(' '.join(name.lower().replace('ё', 'е').split()))
    return UNITS.get(key) if key else None


# Написания единиц в тексте пользователя: (регулярное выражение, ключ, "слабая")
# "Слабые" однобуквенные формы ("в", "с", "м", "г", "т", "а", "н", "л") совпадают
# с предлогами/сокращениями и принимаются, только если характеристика ждёт
# именно эту величину.
_ALIASES: list[tuple[str, str, bool]] = [
    (r'мм\s?рт\.?\s?ст\.?', 'mmhg', False),
    (r'см\s?вод\.?\s?ст\.?', 'cmh2o', False),
    (r'миллиметр(?:ов|а|ы)?', 'mm', False), (r'мм', 'mm', False), (r'mm', 'mm', False),
    (r'сантиметр(?:ов|а|ы)?', 'cm', False), (r'см', 'cm', False), (r'cm', 'cm', False),
    (r'дециметр(?:ов|а|ы)?', 'dm', False), (r'дм', 'dm', False),
    (r'километр(?:ов|а|ы)?', 'km', False), (r'км', 'km', False),
    (r'микрон(?:ов|а|ы)?', 'um', False), (r'мкм', 'um', False),
    (r'нанометр(?:ов|а|ы)?', 'nm', False), (r'нм', 'nm', False),
    (r'погонн(?:ый|ых|ого)\s+метр(?:ов|а)?', 'm', False), (r'пог\.?\s?м', 'm', False),
    (r'метр(?:ов|а|ы)?', 'm', False), (r'м', 'm', True),
    (r'дюйм(?:ов|а|ы)?', 'inch', False), (r'"', 'inch', False), (r"''", 'inch', False),
    (r'миллиграмм(?:ов|а|ы)?', 'mg', False), (r'мг', 'mg', False),
    (r'килограмм(?:ов|а|ы)?', 'kg', False), (r'кг', 'kg', False), (r'kg', 'kg', False),
    (r'грамм(?:ов|а|ы)?', 'g', False), (r'гр\.?', 'g', False), (r'г', 'g', True),
    (r'тонн(?:а|ы)?', 't', False), (r'т', 't', True),
    (r'миллилитр(?:ов|а|ы)?', 'ml', False), (r'мл', 'ml', False), (r'ml', 'ml', False),
    (r'литр(?:ов|а|ы)?', 'l', False), (r'л', 'l', True),
    (r'куб\.?\s?см', 'ml', False), (r'см3', 'ml', False), (r'см³', 'ml', False),
    (r'куб\.?\s?м(?:етр(?:ов|а)?)?', 'm3', False), (r'м3', 'm3', False), (r'м³', 'm3', False),
    (r'дм3', 'l', False),
    (r'кв\.?\s?мм', 'mm2', False), (r'мм2', 'mm2', False), (r'мм²', 'mm2', False),
    (r'кв\.?\s?см', 'cm2', False), (r'см2', 'cm2', False), (r'см²', 'cm2', False),
    (r'кв\.?\s?м(?:етр(?:ов|а)?)?', 'm2', False), (r'м2', 'm2', False), (r'м²', 'm2', False),
    (r'га', 'ha', False),
    (r'г\s?/\s?м2', 'gm2', False), (r'г\s?/\s?м²', 'gm2', False), (r'г\s?/\s?кв\.?\s?м', 'gm2', False),
    (r'гр\s?/\s?м2', 'gm2', False),
    (r'кг\s?/\s?м3', 'kgm3', False), (r'кг\s?/\s?м³', 'kgm3', False),
    (r'киловатт(?:ов|а|ы)?', 'kw', False), (r'квт', 'kw', False), (r'kw', 'kw', False),
    (r'мегаватт(?:ов|а|ы)?', 'mw', False), (r'мвт', 'mw', False),
    (r'ватт(?:ов|а|ы)?', 'w', False), (r'вт', 'w', False), (r'w', 'w', False),
    (r'л\.\s?с\.?', 'hp', False), (r'лошадин(?:ая|ых)\s+сил[аы]?', 'hp', False),
    (r'кв\s?[·*.]?\s?а', 'kva', False), (r'в\s?[·*]\s?а', 'va', False), (r'ва', 'va', False),
    (r'киловольт(?:ов|а)?', 'kv', False), (r'кв', 'kv', False),
    (r'вольт(?:ов|а|ы)?', 'v', False), (r'в', 'v', True), (r'v', 'v', False),
    (r'ма\s?[·*/]?\s?ч', 'mah', False), (r'mah', 'mah', False),
    (r'ампер[-\s]?час(?:ов|а)?', 'ah', False), (r'а\s?[·*/]?\s?ч', 'ah', False), (r'ah', 'ah', False),
    (r'миллиампер(?:ов|а)?', 'ma', False), (r'ма', 'ma', False),
    (r'ампер(?:ов|а|ы)?', 'a', False), (r'а', 'a', True),
    (r'ом', 'ohm', False),
    (r'гигагерц(?:ов|а)?', 'ghz', False), (r'ггц', 'ghz', False),
    (r'мегагерц(?:ов|а)?', 'mhz', False), (r'мгц', 'mhz', False),
    (r'килогерц(?:ов|а)?', 'khz', False), (r'кгц', 'khz', False),
    (r'герц(?:ов|а)?', 'hz', False), (r'гц', 'hz', False),
    (r'об\.?\s?/\s?мин\.?', 'rpm', False), (r'оборот(?:ов|а|ы)?\s+в\s+минуту', 'rpm', False),
    (r'rpm', 'rpm', False), (r'об\.?\s?/\s?с', 'rps', False),
    (r'миллисекунд(?:а|ы)?', 'ms', False), (r'мс', 'ms', False),
    (r'секунд(?:а|ы)?', 's', False), (r'сек\.?', 's', False), (r'с', 's', True),
    (r'минут(?:а|ы)?', 'min', False), (r'мин\.?', 'min', False),
    (r'час(?:ов|а)?', 'h', False), (r'ч', 'h', False),
    (r'сут(?:ок|ки)?', 'day', False),
    (r'месяц(?:ев|а)?', 'month', False), (r'мес\.?', 'month', False),
    (r'год(?:а)?', 'year', False), (r'лет', 'year', False),
    (r'°\s?c', 'degc', False), (r'°\s?с', 'degc', False),
    (r'градус(?:ов|а)?\s+цельсия', 'degc', False),
    (r'градус(?:ов|а)?', 'deg', False), (r'°', 'deg', False),
    (r'процент(?:ов|а)?', 'pct', False), (r'%', 'pct', False),
    (r'тыс\.?\s?шт\.?', 'kpcs', False),
    (r'штук(?:и)?', 'pcs', False), (r'шт\.?', 'pcs', False), (r'pcs', 'pcs', False),
    (r'пар(?:а|ы)?', 'pair', False),
    (r'человек', 'person', False), (r'чел\.?', 'person', False),
    (r'лист(?:ов|а)?', 'sheet', False),
    (r'терабайт(?:ов|а)?', 'tb', False), (r'тб', 'tb', False), (r'tb', 'tb', False),
    (r'гигабайт(?:ов|а)?', 'gb', False), (r'гб', 'gb', False), (r'gb', 'gb', False),
    (r'мегабайт(?:ов|а)?', 'mb', False), (r'мб', 'mb', False), (r'mb', 'mb', False),
    (r'килобайт(?:ов|а)?', 'kb', False), (r'кб', 'kb', False),
    (r'гбит\s?/\s?с', 'gbps', False), (r'мбит\s?/\s?с', 'mbps', False), (r'кбит\s?/\s?с', 'kbps', False),
    (r'мегапаскал(?:ь|я|ей)', 'mpa', False), (r'мпа', 'mpa', False),
    (r'килопаскал(?:ь|я|ей)', 'kpa', False), (r'кпа', 'kpa', False),
    (r'паскал(?:ь|я|ей)', 'pa', False), (r'па', 'pa', False),
    (r'мбар', 'mbar', False), (r'бар(?:а|ов)?', 'bar', False), (r'атм\.?', 'atm', False),
    (r'квт\s?[·*]?\s?ч', 'kwh', False), (r'вт\s?[·*]?\s?ч', 'wh', False),
    (r'кдж', 'kj', False), (r'дж', 'j', False),
    (r'децибел(?:ов|а)?', 'db', False), (r'дб', 'db', False),
    (r'люмен(?:ов|а)?', 'lm', False), (r'лм', 'lm', False),
    (r'люкс(?:ов|а)?', 'lx', False), (r'лк', 'lx', False),
    (r'ньютон(?:ов|а)?', 'n', False), (r'н', 'n', True),
    (r'м\s?/\s?с', 'mps', False), (r'км\s?/\s?ч', 'kmh', False),
    (r'м3\s?/\s?ч', 'm3h', False), (r'м³\s?/\s?ч', 'm3h', False),
    (r'т\s?/\s?ч', 'th', False),
]
_ALIASES.sort(key=lambda a: len(a[0]), reverse=True)
_ALIAS_RES = [
    (re.compile(r'[ ]?(?:' + pattern + r')(?![a-zа-я0-9])', re.IGNORECASE), key, weak)
    for pattern, key, weak in _ALIASES
]


@dataclass(slots=True)
class UnitMatch:
    unit: Unit
    start: int
    end: int
    text: str
    weak: bool


def match_unit_at(text: str, pos: int) -> UnitMatch | None:
    """Единица измерения, записанная в тексте сразу после позиции pos."""
    best: UnitMatch | None = None
    for regex, key, weak in _ALIAS_RES:
        m = regex.match(text, pos)
        if m and (best is None or m.end() > best.end):
            best = UnitMatch(UNITS[key], m.start(), m.end(), m.group(0).strip(), weak)
    return best


def convert(value: float, source: Unit, target: Unit) -> float | None:
    if source.dimension != target.dimension:
        return None
    return value * source.factor / target.factor


def unit_symbol(name: str | None) -> str:
    unit = unit_from_okei(name)
    if unit:
        return unit.symbol
    return name or ''
