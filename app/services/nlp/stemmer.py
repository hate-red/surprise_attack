"""
Стеммер Портера (Snowball) для русского языка.

Реализация алгоритма http://snowball.tartarus.org/algorithms/russian/stemmer.html
без внешних зависимостей. Используется для сопоставления словоформ:
"стулья" -> "стул", "деревянном" -> "деревя", "мужские" -> "мужск".

Описания товаров состоят из существительных и прилагательных, поэтому шаги
для глаголов (деепричастия, возвратные и глагольные окончания) по умолчанию
отключены: иначе "диван" -> "дива", "рукав" -> "рука", "кровать" -> "крова",
а "дивана" -> "диван", т.е. формы одного слова расходятся.
"""
from __future__ import annotations

from functools import lru_cache

VOWELS = set('аеиоуыэюя')

PERFECTIVE_GERUND_1 = ('вшись', 'вши', 'в')            # после а / я
PERFECTIVE_GERUND_2 = ('ившись', 'ывшись', 'ивши', 'ывши', 'ив', 'ыв')
REFLEXIVE = ('ся', 'сь')
ADJECTIVE = (
    'ими', 'ыми', 'его', 'ого', 'ему', 'ому',
    'ее', 'ие', 'ые', 'ое', 'ей', 'ий', 'ый', 'ой', 'ем', 'им', 'ым', 'ом',
    'их', 'ых', 'ую', 'юю', 'ая', 'яя', 'ою', 'ею',
)
PARTICIPLE_1 = ('ем', 'нн', 'вш', 'ющ', 'щ')           # после а / я
PARTICIPLE_2 = ('ивш', 'ывш', 'ующ')
VERB_1 = (                                              # после а / я
    'ешь', 'нно', 'ете', 'йте', 'ла', 'на', 'ли', 'ем', 'ло', 'но', 'ет', 'ют',
    'ны', 'ть', 'й', 'л', 'н',
)
VERB_2 = (
    'уйте', 'ейте', 'ила', 'ыла', 'ена', 'ите', 'или', 'ыли', 'ило', 'ыло', 'ено',
    'ует', 'уют', 'ены', 'ить', 'ыть', 'ишь', 'ей', 'уй', 'ил', 'ыл', 'им', 'ым',
    'ен', 'ят', 'ит', 'ыт', 'ую', 'ю',
)
NOUN = (
    'иями', 'ями', 'ами', 'ией', 'иям', 'ием', 'иях',
    'ев', 'ов', 'ие', 'ье', 'еи', 'ии', 'ей', 'ой', 'ий', 'ям', 'ем', 'ам', 'ом',
    'ах', 'ях', 'ию', 'ью', 'ия', 'ья',
    'а', 'е', 'и', 'й', 'о', 'у', 'ы', 'ь', 'ю', 'я',
)
DERIVATIONAL = ('ость', 'ост')
SUPERLATIVE = ('ейше', 'ейш')


def _sorted(endings: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(endings, key=len, reverse=True))


PERFECTIVE_GERUND_1 = _sorted(PERFECTIVE_GERUND_1)
PERFECTIVE_GERUND_2 = _sorted(PERFECTIVE_GERUND_2)
ADJECTIVE = _sorted(ADJECTIVE)
PARTICIPLE_1 = _sorted(PARTICIPLE_1)
PARTICIPLE_2 = _sorted(PARTICIPLE_2)
VERB_1 = _sorted(VERB_1)
VERB_2 = _sorted(VERB_2)
NOUN = _sorted(NOUN)


def _regions(word: str) -> tuple[int, int]:
    """Начало зон RV и R2 (индексы в слове)."""
    rv = len(word)
    for i, ch in enumerate(word):
        if ch in VOWELS:
            rv = i + 1
            break

    def next_region(start: int) -> int:
        for i in range(start + 1, len(word)):
            if word[i] not in VOWELS and word[i - 1] in VOWELS:
                return i + 1
        return len(word)

    r1 = next_region(0)
    r2 = next_region(r1)
    return rv, r2


def _strip(rv_part: str, endings: tuple[str, ...], preceded_by_a: bool = False) -> str | None:
    for ending in endings:
        if rv_part.endswith(ending):
            if preceded_by_a:
                before = rv_part[: -len(ending)]
                if not before or before[-1] not in 'ая':
                    continue
            return rv_part[: -len(ending)]
    return None


def _remove_adjectival(rv_part: str) -> str | None:
    stripped = _strip(rv_part, ADJECTIVE)
    if stripped is None:
        return None
    participle = _strip(stripped, PARTICIPLE_1, preceded_by_a=True)
    if participle is None:
        participle = _strip(stripped, PARTICIPLE_2)
    return participle if participle is not None else stripped


@lru_cache(maxsize=200_000)
def stem(word: str, verbs: bool = False) -> str:
    word = word.lower().replace('ё', 'е')
    if len(word) < 3 or not any('а' <= ch <= 'я' for ch in word):
        return word

    rv, r2 = _regions(word)
    prefix, rv_part = word[:rv], word[rv:]

    # Шаг 1
    result = None
    if verbs:
        result = _strip(rv_part, PERFECTIVE_GERUND_1, preceded_by_a=True)
        if result is None:
            result = _strip(rv_part, PERFECTIVE_GERUND_2)
    if result is None:
        if verbs:
            reflexive = _strip(rv_part, REFLEXIVE)
            if reflexive is not None:
                rv_part = reflexive
        result = _remove_adjectival(rv_part)
        if result is None and verbs:
            result = _strip(rv_part, VERB_1, preceded_by_a=True)
            if result is None:
                result = _strip(rv_part, VERB_2)
        if result is None:
            result = _strip(rv_part, NOUN)
        if result is None:
            result = rv_part
    rv_part = result

    # Шаг 2
    if rv_part.endswith('и'):
        rv_part = rv_part[:-1]

    # Шаг 3: словообразовательные окончания в R2
    r2_in_rv = max(0, r2 - rv)
    for ending in DERIVATIONAL:
        if rv_part.endswith(ending) and len(rv_part) - len(ending) >= r2_in_rv:
            rv_part = rv_part[: -len(ending)]
            break

    # Шаг 4
    if rv_part.endswith('нн'):
        rv_part = rv_part[:-1]
    else:
        superlative = _strip(rv_part, SUPERLATIVE)
        if superlative is not None:
            rv_part = superlative
            if rv_part.endswith('нн'):
                rv_part = rv_part[:-1]
        elif rv_part.endswith('ь'):
            rv_part = rv_part[:-1]

    return prefix + rv_part
