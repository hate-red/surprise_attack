"""
Нормализация и токенизация русского текста описаний товаров.

- регистр, пробелы, "ё" -> "е", типографские кавычки и тире;
- десятичные запятая и точка ("15,6" == "15.6");
- типовые сокращения ("кол-во" -> "количество", "д/" -> "для" ...);
- основа слова по стеммеру (stemmer.stem) с учётом беглых гласных
  ("молоток"/"молотка", "перчатки"/"перчаток").
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from app.services.nlp.stemmer import stem as _snowball_stem


# Служебные слова: не несут смысла для сопоставления наименований.
STOPWORDS = frozenset({
    'и', 'в', 'во', 'на', 'с', 'со', 'для', 'из', 'по', 'от', 'до', 'к', 'ко',
    'о', 'об', 'или', 'а', 'при', 'под', 'над', 'у', 'за', 'не', 'же', 'то',
    'это', 'как', 'что', 'бы', 'ли', 'также', 'так', 'его', 'ее', 'их', 'том',
    'числе', 'тч', 'шт', 'др', 'прочие', 'прочий', 'прочее', 'кроме', 'включая',
    'менее', 'более', 'не', 'без', 'между',
})

# Сокращения, раскрываемые на уровне токенов (смещения в тексте не меняются).
TOKEN_ABBREVIATIONS = {
    'диам': 'диаметр', 'выс': 'высота', 'шир': 'ширина', 'дл': 'длина',
    'гл': 'глубина', 'макс': 'максимальный', 'толщ': 'толщина',
    'напр': 'напряжение', 'нерж': 'нержавеющий', 'разм': 'размер',
    'хар': 'характеристика', 'кол': 'количество', 'колво': 'количество',
    'мат': 'материал', 'произв': 'производитель', 'вкл': 'включительно',
}
# последовательности токенов: "кол-во", "к-во", "д/"
SEQUENCE_ABBREVIATIONS = [
    (('кол', '-', 'во'), 'количество'),
    (('к', '-', 'во'), 'количество'),
    (('д', '/'), 'для'),
]

# Синонимы, которые в КТРУ и в описаниях пишутся по-разному (на уровне основ).
STEM_SYNONYMS = {
    'вес': 'масс',          # "вес 5 кг"  ~ "Масса молотка"
    'расцветк': 'цвет',
    'матрас': 'матрац',     # в КТРУ "Матрац"
    'емкост': 'емкост',
}

_QUOTES = str.maketrans({
    '«': '"', '»': '"', '“': '"', '”': '"', '„': '"', '″': '"',
    '‘': "'", '’': "'", '‚': "'",
    '–': '-', '—': '-', '−': '-', '‐': '-', '‑': '-',
    '\xa0': ' ', ' ': ' ', ' ': ' ', '\t': ' ',
    '×': 'x', '⨯': 'x',
    'ё': 'е', 'Ё': 'Е',
})

WORD_RE = re.compile(r'[a-zа-я]+', re.IGNORECASE)
TOKEN_RE = re.compile(
    r'(?P<number>\d+(?:[.,]\d+)?)'
    r'|(?P<word>[a-zа-я]+)'
    r'|(?P<sym>[%°"/:;,()\-<>≤≥=+*]|\n)',
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Посимвольная замена (длина строки и смещения не меняются)."""
    return (text or '').translate(_QUOTES)


def normalize_phrase(text: str) -> str:
    """Нижний регистр, "ё"->"е", без лишних пробелов — для сравнения строк."""
    text = normalize_text(text).lower()
    return ' '.join(text.split())




@lru_cache(maxsize=300_000)
def word_stem(word: str) -> str:
    """Основа слова с учётом беглой гласной в суффиксах -ок/-ек/-ец."""
    word = word.lower().replace('ё', 'е')
    if not word or not word[0].isalpha():
        return word
    if not ('а' <= word[0] <= 'я' or 'а' <= word[-1] <= 'я'):
        return word  # латиница / модели — без изменений
    base = _snowball_stem(word)
    if len(base) >= 5 and base[-2:] in ('ок', 'ек', 'ец') and base[-3] not in 'аеиоуыэюя':
        base = base[:-2] + base[-1]
    return STEM_SYNONYMS.get(base, base)


@dataclass(slots=True)
class Token:
    text: str          # как в исходной строке
    norm: str          # нижний регистр, "ё" -> "е"
    kind: str          # word | number | sym
    start: int
    end: int
    stem: str = ''

    @property
    def is_word(self) -> bool:
        return self.kind == 'word'

    @property
    def is_number(self) -> bool:
        return self.kind == 'number'

    @property
    def is_stopword(self) -> bool:
        return self.kind == 'word' and self.norm in STOPWORDS


def tokenize(text: str, expand: bool = True) -> list[Token]:
    raw_tokens: list[Token] = []
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup or 'sym'
        raw = m.group(0)
        norm = raw.lower().replace('ё', 'е')
        if kind == 'number':
            norm = norm.replace(',', '.')
        raw_tokens.append(Token(text=raw, norm=norm, kind=kind, start=m.start(), end=m.end()))

    tokens: list[Token] = []
    i = 0
    while i < len(raw_tokens):
        token = raw_tokens[i]
        if expand:
            merged = False
            for sequence, replacement in SEQUENCE_ABBREVIATIONS:
                n = len(sequence)
                window = raw_tokens[i:i + n]
                if len(window) == n and tuple(t.norm for t in window) == sequence and all(
                    window[k + 1].start == window[k].end for k in range(n - 1)
                ):
                    token = Token(
                        text=text[window[0].start:window[-1].end], norm=replacement,
                        kind='word', start=window[0].start, end=window[-1].end,
                    )
                    i += n - 1
                    merged = True
                    break
            if not merged and token.kind == 'word' and token.norm in TOKEN_ABBREVIATIONS:
                token.norm = TOKEN_ABBREVIATIONS[token.norm]
        if token.kind == 'word':
            token.stem = word_stem(token.norm)
        else:
            token.stem = token.norm
        tokens.append(token)
        i += 1
    return tokens


def content_stems(text: str) -> list[str]:
    """Основы значимых слов фразы (без служебных слов и чисел)."""
    return [
        t.stem for t in tokenize(normalize_text(text))
        if t.is_word and not t.is_stopword and len(t.norm) > 1
    ]


def all_word_stems(text: str) -> list[str]:
    return [t.stem for t in tokenize(normalize_text(text)) if t.is_word]


def parse_number(value: str) -> float | None:
    try:
        return float(value.replace(',', '.').replace(' ', ''))
    except (ValueError, AttributeError):
        return None


def format_number(value: float) -> str:
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    text = f'{value:.6f}'.rstrip('0').rstrip('.')
    return text.replace('.', ',')
