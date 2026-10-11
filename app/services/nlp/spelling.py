"""
Проверка опечаток по словарю предметной области (без внешних сервисов).

Словарь — словоформы из наименований, характеристик и значений КТРУ,
а также из выгрузок СТЕ (KtruIndex.vocabulary). Слово считается
опечаткой, если ни оно, ни его основа не встречаются в словаре, а в словаре
есть близкое слово (расстояние Левенштейна 1, для длинных слов — 2) с той же
первой буквой. Это консервативно: общеупотребительные слова вне словаря
не "исправляются" на случайные термины.
"""
from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import process
from rapidfuzz.distance import OSA

from app.services.nlp.text import Token, word_stem


@dataclass(slots=True)
class SpellingIssue:
    original: str
    suggestion: str
    start: int
    end: int
    distance: int


# Общеупотребительные слова описаний товаров вне словаря КТРУ: не исправляются.
GENERAL_WORDS = frozenset("""
китай россия рф германия италия турция япония корея сша тайвань вьетнам индия беларусь белоруссия
польша чехия франция испания казахстан узбекистан швеция финляндия малайзия таиланд индонезия
бренд марка модель артикул производитель изготовитель страна происхождения упаковка коробка
комплект набор штук шт новый новая новое новые оригинал оригинальный гарантия цвет размер
белый черный серый синий красный зеленый желтый коричневый бежевый голубой розовый фиолетовый
оранжевый бордовый хаки темный светлый ltd llc inc ооо зао оао ао ип
""".split())


class SpellChecker:
    def __init__(self, vocabulary: dict[str, int], known_stems: set[str]) -> None:
        self.vocabulary = vocabulary
        self.known_stems = known_stems | {word_stem(w) for w in GENERAL_WORDS}
        self._by_letter: dict[str, list[str]] = {}
        for word in vocabulary:
            if len(word) >= 3 and 'а' <= word[0] <= 'я':
                self._by_letter.setdefault(word[0], []).append(word)

    def is_known(self, word: str) -> bool:
        return word in self.vocabulary or word_stem(word) in self.known_stems

    def suggest(self, word: str) -> tuple[str, int] | None:
        if len(word) < 4 or not ('а' <= word[0] <= 'я'):
            return None
        if self.is_known(word):
            return None
        max_distance = 1 if len(word) <= 7 else 2
        choices = self._by_letter.get(word[0], [])
        if not choices:
            return None
        # OSA: перестановка соседних букв ("ученичсекий") — одна правка
        matches = process.extract(
            word, choices, scorer=OSA.distance,
            score_cutoff=max_distance, limit=10,
        )
        if not matches:
            return None
        # удвоенная буква ("стулл" -> "стул") — самая частая опечатка набора
        undoubled = {word[:i] + word[i + 1:] for i in range(1, len(word)) if word[i] == word[i - 1]}
        best = min(
            matches,
            key=lambda m: (m[1], m[0] not in undoubled, -self.vocabulary.get(m[0], 0),
                           abs(len(m[0]) - len(word))),
        )
        return best[0], int(best[1])

    def check_tokens(self, tokens: list[Token]) -> list[SpellingIssue]:
        issues = []
        for token in tokens:
            if not token.is_word or token.is_stopword:
                continue
            suggestion = self.suggest(token.norm)
            if suggestion:
                issues.append(SpellingIssue(
                    original=token.text, suggestion=suggestion[0],
                    start=token.start, end=token.end, distance=suggestion[1],
                ))
        return issues


def apply_corrections(text: str, issues: list[SpellingIssue]) -> str:
    """Текст с применёнными исправлениями (регистр первой буквы сохраняется)."""
    result = []
    last = 0
    for issue in sorted(issues, key=lambda i: i.start):
        result.append(text[last:issue.start])
        replacement = issue.suggestion
        if issue.original[:1].isupper():
            replacement = replacement[:1].upper() + replacement[1:]
        result.append(replacement)
        last = issue.end
    result.append(text[last:])
    return ''.join(result)
