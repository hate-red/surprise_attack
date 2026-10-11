"""
Индекс справочника КТРУ в памяти процесса.

Строится один раз из PostgreSQL (не из XML) и содержит только лёгкие данные:
  - наименования позиций, сгруппированные по одинаковому названию,
    с основами слов и весами IDF — для поиска наименования товара;
  - словарь словоформ из наименований, характеристик и значений КТРУ
    и выгрузок СТЕ — для проверки опечаток;
  - словарь названий характеристик КТРУ и СТЕ — чтобы отличить
    "характеристику не этого товара" от "нераспознанной характеристики".
Характеристики и значения конкретных кандидатов читаются из БД на каждый
запрос (PositionRepository.get_characteristic_rows).
"""
from __future__ import annotations

import asyncio
import logging
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from app.repositories.additional_characteristics import AdditionalCharacteristicRepository
from app.repositories.positions import (
    CharacteristicRepositroy,
    CharacteristicValueRepository,
    PositionRepository,
)
from app.services.nlp.matching import root
from app.services.nlp.text import STOPWORDS, WORD_RE, normalize_phrase, tokenize, word_stem

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PositionInfo:
    id: str
    name: str
    okpd2_code: str | None
    okpd2_name: str | None
    is_template: bool
    application_date_start: datetime | None
    application_date_end: datetime | None
    parent_code: str | None
    group: int = -1


@dataclass(slots=True)
class NameGroup:
    idx: int
    name: str
    norm: str
    stems: tuple[str, ...]          # основы значимых слов по порядку
    position_ids: list[str] = field(default_factory=list)

    @property
    def stem_set(self) -> frozenset[str]:
        return frozenset(self.stems)


@dataclass(slots=True)
class PhraseEntry:
    """Название характеристики (КТРУ или СТЕ) для глобального словаря."""
    name: str
    stems: tuple[str, ...]
    count: int = 0
    categories: list[str] = field(default_factory=list)
    kinds: set[str] = field(default_factory=set)

    @property
    def is_flag(self) -> bool:
        """Признак "да/нет" в выгрузке СТЕ ("Трехместный", "Изолированные ручки")."""
        return bool(self.kinds) and self.kinds <= {'Признак'}


class KtruIndex:
    def __init__(self) -> None:
        self.loaded = False
        self.loaded_at: float | None = None
        self.positions: dict[str, PositionInfo] = {}
        self.groups: list[NameGroup] = []
        self.group_by_norm: dict[str, int] = {}
        self.stem_to_groups: dict[str, set[int]] = defaultdict(set)
        self.root_to_stems: dict[str, set[str]] = defaultdict(set)
        self.name_idf: dict[str, float] = {}
        self.char_idf: dict[str, float] = {}
        self.vocabulary: Counter[str] = Counter()
        self.vocabulary_stems: set[str] = set()
        self.ktru_characteristics: dict[str, PhraseEntry] = {}
        self.ste_characteristics: dict[str, PhraseEntry] = {}
        self.ste_categories: dict[str, list[tuple[str, str, str | None]]] = {}
        self.ste_category_stems: dict[str, tuple[str, ...]] = {}
        self.ste_category_chars: dict[str, set[str]] = {}
        self.phrase_stem_index: dict[str, set[str]] = defaultdict(set)
        self.stats: dict[str, int] = {}

    # ------------------------------------------------------------------ build
    def _add_words(self, text: str, weight: int = 1) -> None:
        for word in WORD_RE.findall(normalize_phrase(text)):
            if len(word) >= 2:
                self.vocabulary[word] += weight
                self.vocabulary_stems.add(word_stem(word))

    def build(
        self,
        position_rows: list[tuple],
        characteristic_names: list[tuple[str, int]],
        quality_values: list[str],
        ste_rows: list[tuple[str, str, str, str | None]],
    ) -> None:
        started = time.perf_counter()
        self.__init__()

        for row in position_rows:
            info = PositionInfo(*row)
            norm = normalize_phrase(info.name)
            group_idx = self.group_by_norm.get(norm)
            if group_idx is None:
                stems = tuple(
                    t.stem for t in tokenize(norm)
                    if t.is_word and not t.is_stopword and len(t.norm) > 1
                )
                group_idx = len(self.groups)
                self.groups.append(NameGroup(group_idx, ' '.join(info.name.split()), norm, stems))
                self.group_by_norm[norm] = group_idx
                for s in set(stems):
                    self.stem_to_groups[s].add(group_idx)
                    self.root_to_stems[root(s)].add(s)
                self._add_words(info.name, 3)
            info.group = group_idx
            self.groups[group_idx].position_ids.append(info.id)
            self.positions[info.id] = info
            if info.okpd2_name:
                self._add_words(info.okpd2_name)

        n_groups = max(len(self.groups), 1)
        self.name_idf = {
            s: math.log((n_groups + 1) / (len(g) + 1)) + 1.0 for s, g in self.stem_to_groups.items()
        }

        char_df: Counter[str] = Counter()
        for name, count in characteristic_names:
            norm = normalize_phrase(name)
            entry = self.ktru_characteristics.get(norm)
            if entry is None:
                stems = tuple(
                    t.stem for t in tokenize(norm) if t.is_word and not t.is_stopword
                )
                entry = PhraseEntry(name=' '.join(name.split()), stems=stems)
                self.ktru_characteristics[norm] = entry
                for s in set(stems):
                    char_df[s] += 1
                    self.phrase_stem_index[s].add(norm)
            entry.count += int(count)
            self._add_words(name, 2)
        n_chars = max(len(self.ktru_characteristics), 1)
        self.char_idf = {s: math.log((n_chars + 1) / (df + 1)) + 1.0 for s, df in char_df.items()}

        for value in quality_values:
            self._add_words(value)

        for category, name, kind, unit in ste_rows:
            self.ste_categories.setdefault(category, []).append((name, kind, unit))
            norm = normalize_phrase(name)
            self.ste_category_chars.setdefault(category, set()).add(norm)
            entry = self.ste_characteristics.get(norm)
            if entry is None:
                stems = tuple(t.stem for t in tokenize(norm) if t.is_word and not t.is_stopword)
                entry = PhraseEntry(name=' '.join(name.split()), stems=stems)
                self.ste_characteristics[norm] = entry
                for s in set(stems):
                    self.phrase_stem_index[s].add('ste:' + norm)
            entry.count += 1
            if kind:
                entry.kinds.add(kind)
            if len(entry.categories) < 5 and category not in entry.categories:
                entry.categories.append(category)
            self._add_words(name)
        for category in self.ste_categories:
            self._add_words(category)
            self.ste_category_stems[category] = tuple(
                t.stem for t in tokenize(normalize_phrase(category)) if t.is_word and not t.is_stopword
            )

        self.loaded = True
        self.loaded_at = time.time()
        self.stats = {
            'positions': len(self.positions),
            'name_groups': len(self.groups),
            'ktru_characteristic_names': len(self.ktru_characteristics),
            'ste_categories': len(self.ste_categories),
            'ste_characteristic_names': len(self.ste_characteristics),
            'vocabulary': len(self.vocabulary),
            'build_ms': int((time.perf_counter() - started) * 1000),
        }
        logger.info('KTRU index built: %s', self.stats)

    # ---------------------------------------------------------------- helpers
    def idf(self, stem: str) -> float:
        value = self.name_idf.get(stem)
        if value is not None:
            return value
        return math.log(len(self.groups) + 1) + 1.0

    def char_weight(self, stem: str) -> float:
        return self.char_idf.get(stem, math.log(len(self.ktru_characteristics) + 1) + 1.0)

    def is_known_word(self, word: str) -> bool:
        return word in self.vocabulary or word_stem(word) in self.vocabulary_stems

    def best_ste_category(self, stems: set[str]) -> str | None:
        """Категория портала поставщиков, ближайшая к наименованию товара."""
        from app.services.nlp.matching import stem_similarity

        best: tuple[int, int, str] | None = None
        for category, cat_stems in self.ste_category_stems.items():
            if not cat_stems:
                continue
            overlap = sum(1 for c in set(cat_stems) if any(stem_similarity(c, s) > 0 for s in stems))
            if overlap == 0 or not any(stem_similarity(cat_stems[0], s) > 0 for s in stems):
                continue
            key = (overlap, -len(cat_stems), category)
            if best is None or key[:2] > best[:2]:
                best = key
        return best[2] if best else None

    def find_phrase(self, stems: list[str]) -> tuple[str | None, PhraseEntry | None, str]:
        """Название характеристики КТРУ или СТЕ, содержащее все значимые основы фразы.

        -> (норма названия, запись, источник 'ktru' | 'ste') или (None, None, '').
        """
        content = list(dict.fromkeys(s for s in stems if s not in STOPWORDS and len(s) > 1))
        if not content:
            return None, None, ''
        candidates: set[str] | None = None
        for s in content:
            found = self.phrase_stem_index.get(s)
            if not found:
                return None, None, ''
            candidates = set(found) if candidates is None else candidates & found
            if not candidates:
                return None, None, ''

        def entry_of(key: str) -> tuple[PhraseEntry, str]:
            if key.startswith('ste:'):
                return self.ste_characteristics[key[4:]], 'ste'
            return self.ktru_characteristics[key], 'ktru'

        def rank(key: str) -> tuple[float, int, int]:
            entry, source = entry_of(key)
            coverage = len(content) / max(len(set(entry.stems)), 1)
            return (coverage, 1 if source == 'ktru' else 0, entry.count)

        best = max(candidates or (), key=rank, default=None)
        if best is None:
            return None, None, ''
        entry, source = entry_of(best)
        return (best[4:] if source == 'ste' else best), entry, source


_index = KtruIndex()
_lock = asyncio.Lock()


async def load_index(force: bool = False) -> KtruIndex:
    """Ленивая загрузка индекса из БД (один раз на процесс)."""
    global _index
    if _index.loaded and not force:
        return _index
    async with _lock:
        if _index.loaded and not force:
            return _index
        position_rows = await PositionRepository.get_index_rows()
        characteristic_names = await CharacteristicRepositroy.get_distinct_names()
        quality_values = await CharacteristicValueRepository.get_distinct_quality_values()
        ste_rows = await AdditionalCharacteristicRepository.get_all_with_categories()
        index = KtruIndex()
        await asyncio.to_thread(index.build, position_rows, characteristic_names, quality_values, ste_rows)
        _index = index
        return _index


def get_index() -> KtruIndex:
    return _index
