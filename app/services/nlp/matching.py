"""Сопоставление основ слов: точное совпадение и совпадение по корню."""
from __future__ import annotations

from functools import lru_cache

# Суффиксы прилагательных, отрезаемые для получения "корня":
# "кожан" -> "кож", "аккумуляторн" -> "аккумулятор", "сетев" -> "сет",
# "зимн" -> "зим", "деревя" -> "дерев", "текстильн" -> "текстил" (= "текстиль").
_ROOT_SUFFIXES = (
    'ическ', 'ичн', 'овн', 'енн', 'янн', 'анн', 'ьн',
    'ан', 'ян', 'ов', 'ев', 'ск', 'н', 'я', 'ь',
)

EXACT = 1.0
ROOT = 0.8


@lru_cache(maxsize=300_000)
def root(stem: str) -> str:
    if len(stem) < 4 or not ('а' <= stem[0] <= 'я'):
        return stem
    for suffix in _ROOT_SUFFIXES:
        if stem.endswith(suffix) and len(stem) - len(suffix) >= 3:
            return stem[: -len(suffix)]
    return stem


def stem_similarity(a: str, b: str) -> float:
    """1.0 — одинаковые основы, 0.8 — одно слово образовано от другого
    ("кожан"/"кож", "тканев"/"ткан"), 0 — разные слова."""
    if a == b:
        return EXACT
    if len(a) < 3 or len(b) < 3:
        return 0.0
    ra, rb = root(a), root(b)
    if ra == b or rb == a:
        return ROOT
    if ra == rb and ra != a and rb != b and len(ra) >= 4:
        return ROOT
    return 0.0
