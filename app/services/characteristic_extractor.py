"""
Извлечение и проверка характеристик из текста по справочнику КТРУ.

1. CandidateSchema — характеристики позиций-кандидатов, объединённые по
   названию: допустимые значения, диапазоны, единицы, обязательность.
2. CharacteristicExtractor — находит в тексте упоминания характеристик,
   качественные значения, числа с единицами и диапазоны, связывает их,
   нормализует (единицы, регистр, десятичный разделитель) и проверяет по
   ограничениям КТРУ каждой позиции-кандидата.

Все ограничения берутся из БД. Если у характеристики в КТРУ нет ни перечня,
ни диапазона, значение не считается ошибочным ("ограничений нет").
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from rapidfuzz import fuzz, process

from app.services.ktru_index import KtruIndex
from app.services.nlp.matching import root, stem_similarity
from app.services.nlp.text import (
    STOPWORDS,
    Token,
    format_number,
    normalize_phrase,
    tokenize,
)
from app.services.nlp.units import Unit, UnitMatch, convert, match_unit_at, unit_from_okei

BOOLEAN_LABELS = {'да', 'нет'}
NEGATIONS = {'без', 'нет', 'отсутствует', 'отсутствуют', 'не'}
GENERIC_CHAR_STEMS = {'тип', 'вид', 'налич', 'количеств', 'материал', 'форм', 'размер'}
# слова-связки в названиях характеристик, которые пользователь обычно не пишет:
# "Наличие режима реверса" ~ "с реверсом"
FILLER_CHAR_STEMS = {'налич', 'режим', 'функц', 'возможн', 'признак'}

STATUS_OK = 'ok'                      # значение допустимо по КТРУ
STATUS_NO_CONSTRAINTS = 'no_constraints'  # в КТРУ нет перечня/диапазона
STATUS_INVALID = 'invalid'            # значение не допускается КТРУ
STATUS_UNIT_MISMATCH = 'unit_mismatch'
STATUS_AMBIGUOUS = 'ambiguous'        # неясно, к какой характеристике относится
STATUS_NO_VALUE = 'no_value'          # характеристика названа без значения
STATUS_STE = 'ste_only'               # есть только в выгрузке СТЕ
STATUS_OTHER_KTRU = 'not_applicable'  # есть в КТРУ, но не у этих позиций
STATUS_UNRECOGNIZED = 'unrecognized'  # нет ни в КТРУ, ни в СТЕ
STATUS_MISSING = 'missing'            # не указана пользователем
STATUS_CONFLICT = 'conflict'          # допустима, но противоречит другим условиям


# ============================================================ схема КТРУ
@dataclass(slots=True)
class ValueOption:
    id: int
    label: str
    kind: str                       # quality | range | concrete
    norm: str = ''
    stems: tuple[str, ...] = ()
    unit_name: str | None = None
    unit: Unit | None = None
    lower: float | None = None
    upper: float | None = None
    lower_inc: bool = True
    upper_inc: bool = True
    number: float | None = None

    def contains(self, value: float) -> bool:
        if self.kind == 'concrete':
            return self.number is not None and abs(self.number - value) <= 1e-9 * max(1.0, abs(value))
        if self.kind != 'range':
            return False
        if self.lower is not None:
            if value < self.lower or (value == self.lower and not self.lower_inc):
                return False
        if self.upper is not None:
            if value > self.upper or (value == self.upper and not self.upper_inc):
                return False
        return True

    def contains_interval(self, lo: float | None, hi: float | None) -> bool:
        if self.kind == 'concrete':
            return lo is not None and hi is not None and lo == hi and self.contains(lo)
        if self.kind != 'range':
            return False
        if lo is None or hi is None:
            # одностороннее условие пользователя ("не менее 40")
            if lo is not None:
                return self.lower is not None and self.contains(lo) and self.upper is None
            if hi is not None:
                return self.upper is not None and self.contains(hi) and self.lower is None
            return False
        return self.contains(lo) and self.contains(hi)


@dataclass(slots=True)
class PositionChar:
    id: int
    position_id: str
    name: str
    required: bool
    char_type: int | None
    kind: int | None
    choice_type: int | None
    options: list[ValueOption] = field(default_factory=list)

    @property
    def is_numeric(self) -> bool:
        return self.char_type == 2 or any(o.kind in ('range', 'concrete') for o in self.options)

    @property
    def has_constraints(self) -> bool:
        return bool(self.options)


@dataclass(slots=True)
class QualityLabel:
    label: str
    norm: str
    stems: tuple[str, ...]
    positions: set[str] = field(default_factory=set)


@dataclass(slots=True)
class UnifiedChar:
    key: str
    name: str
    stems: tuple[str, ...]
    by_position: dict[str, PositionChar] = field(default_factory=dict)
    labels: dict[str, QualityLabel] = field(default_factory=dict)
    units: dict[str, Unit] = field(default_factory=dict)
    numeric_votes: int = 0

    @property
    def is_numeric(self) -> bool:
        return self.numeric_votes * 2 >= len(self.by_position) and self.numeric_votes > 0

    @property
    def is_boolean(self) -> bool:
        return bool(self.labels) and set(self.labels) <= BOOLEAN_LABELS

    @property
    def required(self) -> bool:
        return any(pc.required for pc in self.by_position.values())

    @property
    def kind(self) -> int | None:
        kinds = [pc.kind for pc in self.by_position.values() if pc.kind is not None]
        return min(kinds) if kinds else None

    def option_labels(self, positions: set[str] | None = None, limit: int = 60) -> list[str]:
        labels: dict[str, None] = {}
        for pid, pc in self.by_position.items():
            if positions is not None and pid not in positions:
                continue
            for option in pc.options:
                labels.setdefault(option.label, None)
                if len(labels) >= limit:
                    return list(labels)
        return list(labels)

    def unit_symbol(self) -> str | None:
        for unit in self.units.values():
            return unit.symbol
        return None


def _range_bounds(value) -> tuple[float | None, float | None, bool, bool]:
    if value is None:
        return None, None, True, True
    lower = float(value.lower) if value.lower is not None else None
    upper = float(value.upper) if value.upper is not None else None
    return lower, upper, bool(value.lower_inc), bool(value.upper_inc)


class CandidateSchema:
    """Характеристики позиций-кандидатов, объединённые по названию."""

    def __init__(self, rows: list[tuple]) -> None:
        self.chars: dict[str, UnifiedChar] = {}
        self.position_chars: dict[str, dict[str, PositionChar]] = defaultdict(dict)
        self.stem_index: dict[str, set[str]] = defaultdict(set)
        self.label_index: dict[str, set[tuple[str, str]]] = defaultdict(set)
        # корень -> основы (для поиска форм "регулировкой" ~ "регулировка", "кожаный" ~ "кожа")
        self.stem_roots: dict[str, set[str]] = defaultdict(set)
        self.label_roots: dict[str, set[str]] = defaultdict(set)
        by_char_id: dict[int, PositionChar] = {}

        for (char_id, position_id, name, required, char_type, kind, choice_type,
             value_id, value_name, measure_units, is_range, value_range, is_quality,
             quality_description, concrete_value) in rows:
            pc = by_char_id.get(char_id)
            if pc is None:
                pc = PositionChar(char_id, position_id, name, bool(required), char_type, kind, choice_type)
                by_char_id[char_id] = pc
                key = normalize_phrase(name)
                uc = self.chars.get(key)
                if uc is None:
                    core = re.sub(r'\([^)]*\)', ' ', key)
                    stems = tuple(t.stem for t in tokenize(core) if t.is_word and t.norm not in STOPWORDS) or tuple(
                        t.stem for t in tokenize(key) if t.is_word and t.norm not in STOPWORDS)
                    uc = UnifiedChar(key=key, name=name, stems=stems)
                    self.chars[key] = uc
                    for s in set(stems):
                        self.stem_index[s].add(key)
                        self.stem_roots[root(s)].add(s)
                uc.by_position[position_id] = pc
                self.position_chars[position_id][key] = pc
            if value_id is None:
                continue
            unit = unit_from_okei(measure_units)
            if is_quality:
                label = ' '.join((quality_description or value_name or '').split())
                norm = normalize_phrase(label)
                option = ValueOption(
                    id=value_id, label=label, kind='quality', norm=norm,
                    stems=tuple(t.stem for t in tokenize(norm) if t.kind in ('word', 'number')),
                    unit_name=measure_units, unit=unit,
                )
            elif is_range:
                lower, upper, lower_inc, upper_inc = _range_bounds(value_range)
                option = ValueOption(
                    id=value_id, label=value_name, kind='range', unit_name=measure_units, unit=unit,
                    lower=lower, upper=upper, lower_inc=lower_inc, upper_inc=upper_inc,
                )
            else:
                option = ValueOption(
                    id=value_id, label=value_name, kind='concrete', unit_name=measure_units, unit=unit,
                    number=float(concrete_value) if concrete_value is not None else None,
                )
            pc.options.append(option)

        for uc in self.chars.values():
            for pid, pc in uc.by_position.items():
                if pc.is_numeric:
                    uc.numeric_votes += 1
                for option in pc.options:
                    if option.unit is not None:
                        uc.units.setdefault(option.unit.key, option.unit)
                    if option.kind == 'quality' and option.norm:
                        ql = uc.labels.get(option.norm)
                        if ql is None:
                            ql = QualityLabel(option.label, option.norm, option.stems)
                            uc.labels[option.norm] = ql
                            content = [x for x in option.stems if x not in STOPWORDS]
                            if content:
                                self.label_index[content[0]].add((uc.key, option.norm))
                                self.label_roots[root(content[0])].add(content[0])
                        ql.positions.add(pid)

    @staticmethod
    def _similar(stem: str, index: dict[str, set], roots: dict[str, set[str]]) -> set[str]:
        """Основы из индекса, совпадающие со stem точно или по корню."""
        found = {stem} if stem in index else set()
        r = root(stem)
        for candidate in roots.get(stem, set()) | roots.get(r, set()) | ({r} if r in index else set()):
            if stem_similarity(candidate, stem) > 0:
                found.add(candidate)
        return found

    def similar_name_stems(self, stem: str) -> set[str]:
        return self._similar(stem, self.stem_index, self.stem_roots)

    def similar_label_stems(self, stem: str) -> set[str]:
        return self._similar(stem, self.label_index, self.label_roots)

    def positions_with(self, key: str) -> set[str]:
        uc = self.chars.get(key)
        return set(uc.by_position) if uc else set()


# ============================================================ результаты
@dataclass
class Extracted:
    key: str | None
    name: str
    source: str                       # text | user | ste | unknown
    original: str = ''
    start: int | None = None
    end: int | None = None
    value_text: str = ''
    value_kind: str = 'quality'       # quality | number | interval | boolean | none
    label: str | None = None          # нормализованное качественное значение
    number: float | None = None
    interval: tuple[float | None, float | None] | None = None
    user_unit: Unit | None = None
    unit_assumed: bool = False
    status: str = STATUS_OK
    normalized: str = ''
    unit_display: str = ''
    matched_option: str | None = None  # подпись диапазона/значения КТРУ
    notes: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    confidence: float = 1.0
    accepted_positions: set[str] = field(default_factory=set)
    positions_with_char: set[str] = field(default_factory=set)
    token_indices: set[int] = field(default_factory=set)

    @property
    def usable(self) -> bool:
        return self.status in (STATUS_OK, STATUS_NO_CONSTRAINTS) and self.key is not None


@dataclass
class NumberExpr:
    start_tok: int
    end_tok: int                       # включительно
    start: int
    end: int
    kind: str                          # number | interval | dims
    value: float | None = None
    lo: float | None = None
    hi: float | None = None
    lo_inc: bool = True
    hi_inc: bool = True
    dims: list[float] = field(default_factory=list)
    unit: UnitMatch | None = None
    text: str = ''


@dataclass
class Mention:
    key: str
    score: float
    tokens: set[int]
    start_tok: int
    end_tok: int
    negated: bool = False


@dataclass
class LabelHit:
    key: str
    label_norm: str
    tokens: set[int]
    start_tok: int
    end_tok: int
    similarity: float


# ============================================================ извлечение
COMPARATORS_LOW = {'от', 'не менее', 'свыше', 'более', 'больше', 'выше', 'не ниже', 'минимум', '>', '≥', '>='}
COMPARATORS_HIGH = {'до', 'не более', 'менее', 'меньше', 'ниже', 'не выше', 'максимум', '<', '≤', '<='}
EXCLUSIVE = {'свыше', 'более', 'больше', 'выше', 'менее', 'меньше', 'ниже', '>', '<'}


class CharacteristicExtractor:
    def __init__(self, text: str, tokens: list[Token], schema: CandidateSchema, index: KtruIndex,
                 name_token_indices: set[int], name_stems: set[str]) -> None:
        self.text = text
        self.lower_text = text.lower().replace('ё', 'е')
        self.tokens = tokens
        self.schema = schema
        self.index = index
        self.name_tokens = set(name_token_indices)
        self.name_stems = name_stems
        self.consumed: set[int] = set(name_token_indices)
        self.results: list[Extracted] = []
        self.unrecognized_fragments: list[dict] = []
        self.ste_category = index.best_ste_category(name_stems) if name_stems else None
        self.assigned: dict[str, set[str]] = {}  # характеристика -> уже извлечённые значения

    # ------------------------------------------------------------ segments
    def _segments(self) -> list[tuple[int, int]]:
        segments, start = [], 0
        for i, t in enumerate(self.tokens):
            if t.kind == 'sym' and t.norm in (',', ';', '\n'):
                if i > start:
                    segments.append((start, i - 1))
                start = i + 1
        if start < len(self.tokens):
            segments.append((start, len(self.tokens) - 1))
        return segments

    # -------------------------------------------------- characteristic names
    def _find_mentions(self, seg: tuple[int, int]) -> list[Mention]:
        lo, hi = seg
        word_idx = [
            i for i in range(lo, hi + 1)
            if self.tokens[i].is_word and not self.tokens[i].is_stopword and i not in self.name_tokens
        ]
        candidate_keys: set[str] = set()
        for i in word_idx:
            for s in self.schema.similar_name_stems(self.tokens[i].stem):
                candidate_keys |= self.schema.stem_index[s]

        mentions: list[Mention] = []
        for key in candidate_keys:
            uc = self.schema.chars[key]
            stems = [s for s in uc.stems if s not in FILLER_CHAR_STEMS] or list(uc.stems)
            if not stems:
                continue
            total = sum(self.index.char_weight(s) for s in stems)
            matched_weight = 0.0
            tokens: set[int] = set()
            matched_text = 0
            for s in stems:
                best_tok, best_sim = None, 0.0
                for i in word_idx:
                    sim = stem_similarity(s, self.tokens[i].stem)
                    if sim > best_sim:
                        best_tok, best_sim = i, sim
                if best_tok is not None:
                    matched_weight += self.index.char_weight(s) * best_sim
                    tokens.add(best_tok)
                    matched_text += 1
                elif any(stem_similarity(s, ns) > 0 for ns in self.name_stems):
                    # слово из наименования товара: "Масса молотка" при товаре "молоток"
                    matched_weight += self.index.char_weight(s) * 0.7
            if matched_text == 0:
                continue
            coverage = matched_weight / total if total else 0.0
            content_stems = [s for s in stems if s not in GENERIC_CHAR_STEMS]
            only_generic = bool(content_stems) and len(stems) > 1 and not any(
                stem_similarity(s, self.tokens[i].stem) > 0 for s in content_stems for i in tokens
            )
            span = max(tokens) - min(tokens)
            head_hit = any(stem_similarity(stems[0], self.tokens[i].stem) > 0 for i in tokens)
            if only_generic:
                # "размер 52" ~ "Российский размер": общее слово допускается, только если
                # оно есть в названии единственной характеристики кандидатов
                matched_stems = {s for s in stems if any(
                    stem_similarity(s, self.tokens[i].stem) > 0 for i in tokens)}
                unique = all(len(self.schema.stem_index.get(s, ())) == 1 for s in matched_stems)
                if not (unique and len(tokens) == len(matched_stems) and matched_stems):
                    continue
                coverage = 0.5
            elif coverage < 0.6 and not (matched_text >= 2 and head_hit and coverage >= 0.4):
                continue
            if span > len(stems) + 3:
                continue
            first = min(tokens)
            negated = any(
                self.tokens[j].norm in NEGATIONS for j in range(max(lo, first - 2), first)
            )
            mentions.append(Mention(key, coverage + 0.02 * len(stems), tokens, first, max(tokens), negated))

        # жадно оставляем лучшие непересекающиеся упоминания
        mentions.sort(key=lambda m: (-m.score, -len(m.tokens)))
        chosen: list[Mention] = []
        used: set[int] = set()
        for m in mentions:
            if m.tokens & used:
                continue
            chosen.append(m)
            used |= m.tokens
        return sorted(chosen, key=lambda m: m.start_tok)

    # --------------------------------------------------------- quality labels
    def _find_labels(self, seg: tuple[int, int]) -> list[LabelHit]:
        lo, hi = seg
        hits: list[LabelHit] = []
        word_idx = [i for i in range(lo, hi + 1) if self.tokens[i].kind in ('word', 'number')]
        seen: set[tuple[str, str]] = set()
        for i in word_idx:
            stem = self.tokens[i].stem
            keys = set(self.schema.label_index.get(stem, set()))
            if self.tokens[i].is_word:
                for s in self.schema.similar_label_stems(stem):
                    keys |= self.schema.label_index[s]
            for key, label_norm in keys:
                if (key, label_norm) in seen:
                    continue
                uc = self.schema.chars[key]
                ql = uc.labels[label_norm]
                stems = [s for s in ql.stems if s not in STOPWORDS] or list(ql.stems)
                if not stems:
                    continue
                tokens: set[int] = set()
                sims = []
                for s in stems:
                    best = (None, 0.0)
                    for j in range(i, min(hi, i + len(ql.stems) + 2) + 1):
                        if j in tokens:
                            continue
                        sim = 1.0 if self.tokens[j].stem == s else (
                            stem_similarity(s, self.tokens[j].stem) if self.tokens[j].is_word else 0.0)
                        if sim > best[1]:
                            best = (j, sim)
                    if best[0] is None:
                        break
                    tokens.add(best[0])
                    sims.append(best[1])
                if len(sims) != len(stems):
                    continue
                if _is_negative_label(label_norm):
                    first = min(tokens)
                    if not any(self.tokens[j].norm in NEGATIONS for j in range(max(lo, first - 2), first)):
                        continue
                    tokens |= {j for j in range(max(lo, first - 2), first) if self.tokens[j].norm in NEGATIONS}
                seen.add((key, label_norm))
                hits.append(LabelHit(key, label_norm, tokens, min(tokens), max(tokens), sum(sims) / len(sims)))
        return hits

    # ---------------------------------------------------------------- numbers
    def _find_numbers(self, seg: tuple[int, int]) -> list[NumberExpr]:
        lo, hi = seg
        out: list[NumberExpr] = []
        i = lo
        toks = self.tokens
        while i <= hi:
            t = toks[i]
            if not t.is_number:
                i += 1
                continue
            # число внутри артикула/модели: "i5-12500H", "SKDB-UT6-883", "PH2"
            if _inside_code(self.text, t.start, t.end):
                i += 1
                continue
            prev = toks[i - 1] if i > 0 else None
            if prev is not None and prev.end == t.start and prev.is_word and not prev.norm in ('x', 'х'):
                i += 1
                continue
            nxt = toks[i + 1] if i + 1 < len(toks) else None
            if nxt is not None and nxt.start == t.end and nxt.is_word and nxt.norm not in ('x', 'х') \
                    and match_unit_at(self.text, t.end) is None:
                i += 1
                continue

            value = float(t.norm)
            # габариты: 120x60x75
            dims = [value]
            j = i
            while j + 2 <= hi and toks[j + 1].norm in ('x', 'х', '*') and toks[j + 2].is_number:
                dims.append(float(toks[j + 2].norm))
                j += 2
            if len(dims) >= 2:
                unit = match_unit_at(self.text, toks[j].end)
                end = unit.end if unit else toks[j].end
                while j + 1 <= hi and toks[j + 1].start < end:
                    j += 1
                out.append(NumberExpr(i, j, t.start, end, 'dims', dims=dims, unit=unit,
                                      text=self.text[t.start:end]))
                i = j + 1
                continue

            # интервал: "40-50", "от 40 до 50"
            unit = match_unit_at(self.text, t.end)
            end_tok = i
            expr = NumberExpr(i, i, t.start, t.end, 'number', value=value, unit=unit)
            k = i + 1
            if unit is not None:
                while k <= hi and toks[k].start < unit.end:
                    k += 1
            if k + 1 <= hi and toks[k].norm in ('-', 'до') and toks[k + 1].is_number and (
                toks[k].norm == 'до' or toks[k].start - (unit.end if unit else t.end) <= 1
            ):
                hi_value = float(toks[k + 1].norm)
                unit2 = match_unit_at(self.text, toks[k + 1].end)
                expr = NumberExpr(i, k + 1, t.start, unit2.end if unit2 else toks[k + 1].end, 'interval',
                                  lo=value, hi=hi_value, unit=unit2 or unit)
                end_tok = k + 1
                if unit2 is not None:
                    while end_tok + 1 <= hi and toks[end_tok + 1].start < unit2.end:
                        end_tok += 1
            else:
                if unit is not None:
                    while end_tok + 1 <= hi and toks[end_tok + 1].start < unit.end:
                        end_tok += 1
                    expr.end = unit.end
            expr.end_tok = end_tok

            # компараторы перед числом: "не менее 40", "от 40", "до 50", "≥ 40"
            comparator = None
            if i - 1 >= lo:
                w1 = toks[i - 1].norm
                w2 = f'{toks[i - 2].norm} {w1}' if i - 2 >= lo else ''
                if w2 in COMPARATORS_LOW or w2 in COMPARATORS_HIGH:
                    comparator, expr.start_tok, expr.start = w2, i - 2, toks[i - 2].start
                elif w1 in COMPARATORS_LOW or w1 in COMPARATORS_HIGH:
                    comparator, expr.start_tok, expr.start = w1, i - 1, toks[i - 1].start
            if expr.kind == 'number' and comparator:
                if comparator in COMPARATORS_LOW:
                    expr.kind, expr.lo, expr.hi = 'interval', value, None
                    expr.lo_inc = comparator not in EXCLUSIVE
                else:
                    expr.kind, expr.lo, expr.hi = 'interval', None, value
                    expr.hi_inc = comparator not in EXCLUSIVE
            expr.text = self.text[expr.start:expr.end]
            out.append(expr)
            i = end_tok + 1
        return out

    # ------------------------------------------------------------- validation
    def _convert_for(self, option: ValueOption, value: float, unit: Unit | None) -> float | None:
        if unit is None or option.unit is None:
            return value
        return convert(value, unit, option.unit)

    def _validate_number(self, uc: UnifiedChar, ex: Extracted) -> None:
        unit = ex.user_unit
        positions_with = set(uc.by_position)
        ex.positions_with_char = positions_with
        accepted: set[str] = set()
        matched: dict[str, ValueOption] = {}
        unit_ok = False
        no_constraints = True
        target_unit: Unit | None = next(iter(uc.units.values()), None)

        if unit is not None and uc.units and not any(u.dimension == unit.dimension for u in uc.units.values()):
            ex.status = STATUS_UNIT_MISMATCH
            expected = ', '.join(sorted({u.symbol for u in uc.units.values()}))
            ex.notes.append(f'Единица «{unit.symbol}» несовместима с характеристикой: '
                            f'в КТРУ ожидается {expected}. В спецификацию не добавлено.')
            ex.unit_display = unit.symbol
            ex.suggestions = uc.option_labels(limit=8)
            return

        for pid, pc in uc.by_position.items():
            numeric_options = [o for o in pc.options if o.kind in ('range', 'concrete')]
            quality_options = [o for o in pc.options if o.kind == 'quality']
            if not pc.options:
                accepted.add(pid)
                continue
            no_constraints = False
            ok = False
            for option in numeric_options:
                if option.unit and unit and option.unit.dimension != unit.dimension:
                    continue
                unit_ok = True
                if ex.value_kind == 'number':
                    v = self._convert_for(option, ex.number, unit)
                    if v is not None and option.contains(v):
                        ok = True
                        matched.setdefault(option.label, option)
                elif ex.value_kind == 'interval' and ex.interval:
                    lo = self._convert_for(option, ex.interval[0], unit) if ex.interval[0] is not None else None
                    hi = self._convert_for(option, ex.interval[1], unit) if ex.interval[1] is not None else None
                    if option.contains_interval(lo, hi):
                        ok = True
                        matched.setdefault(option.label, option)
            if not ok and quality_options:
                # числовые значения, записанные в КТРУ текстом: размеры "48", "44-46"
                candidates = {ex.normalized.replace(',', '.'), ex.value_text.strip().lower()}
                if ex.value_kind == 'number' and ex.number is not None:
                    candidates.add(format_number(ex.number).replace(',', '.'))
                if ex.value_kind == 'interval' and ex.interval and None not in ex.interval:
                    candidates.add(f'{format_number(ex.interval[0])}-{format_number(ex.interval[1])}')
                for option in quality_options:
                    if option.norm.replace(',', '.').replace(' ', '') in {c.replace(' ', '') for c in candidates}:
                        ok = True
                        unit_ok = True
                        matched.setdefault(option.label, option)
            if ok:
                accepted.add(pid)

        if target_unit is not None and unit is None:
            ex.unit_assumed = True
            ex.notes.append(f'Единица не указана — принята единица КТРУ «{target_unit.symbol}».')
        # нормализованное представление в единице КТРУ
        if target_unit is not None and unit is not None and unit.key != target_unit.key:
            if ex.value_kind == 'number':
                converted = convert(ex.number, unit, target_unit)
                if converted is not None:
                    ex.normalized = format_number(converted)
                    ex.notes.append(f'Пересчитано: {ex.value_text} = {format_number(converted)} {target_unit.symbol}.')
            elif ex.interval:
                lo = convert(ex.interval[0], unit, target_unit) if ex.interval[0] is not None else None
                hi = convert(ex.interval[1], unit, target_unit) if ex.interval[1] is not None else None
                ex.normalized = _interval_text(lo, hi)
        if target_unit is not None:
            ex.unit_display = target_unit.symbol

        ex.accepted_positions = accepted
        if no_constraints:
            ex.status = STATUS_NO_CONSTRAINTS
            ex.notes.append('В справочнике КТРУ для этой характеристики нет перечня или диапазона значений.')
        elif accepted:
            ex.status = STATUS_OK
            if matched:
                ex.matched_option = _most_specific(list(matched.values())).label
        else:
            ex.status = STATUS_INVALID
            allowed = uc.option_labels(limit=12)
            ex.notes.append(
                f'Значение не попадает ни в один допустимый диапазон КТРУ'
                + (f': {"; ".join(allowed)}' if allowed else '') + '. В спецификацию не добавлено.'
            )
            ex.suggestions = allowed[:8]
            if not unit_ok and unit is not None:
                ex.status = STATUS_UNIT_MISMATCH

    def _validate_label(self, uc: UnifiedChar, ex: Extracted) -> None:
        ex.positions_with_char = set(uc.by_position)
        accepted: set[str] = set()
        no_constraints = True
        for pid, pc in uc.by_position.items():
            if not pc.options:
                accepted.add(pid)
                continue
            no_constraints = False
            if any(o.kind == 'quality' and o.norm == normalize_phrase(ex.label or '') for o in pc.options):
                accepted.add(pid)
        ex.accepted_positions = accepted
        if no_constraints:
            ex.status = STATUS_NO_CONSTRAINTS
            ex.notes.append('В справочнике КТРУ для этой характеристики нет перечня значений.')
        elif accepted:
            ex.status = STATUS_OK
            ex.matched_option = ex.label
        else:
            ex.status = STATUS_INVALID
            ex.notes.append('Значение не входит в перечень допустимых значений КТРУ.')
            ex.suggestions = uc.option_labels(limit=12)[:8]

    def resolve_quality_text(self, uc: UnifiedChar, value_text: str) -> tuple[str | None, float, list[str]]:
        """Сопоставляет произвольный текст значения с перечнем КТРУ.

        -> (подпись значения или None, сходство 0..100, подсказки)
        """
        norm = normalize_phrase(value_text)
        if not norm:
            return None, 0.0, []
        if norm in uc.labels:
            return uc.labels[norm].label, 100.0, []
        value_stems = [t.stem for t in tokenize(norm) if t.kind in ('word', 'number') and t.norm not in STOPWORDS]
        for ql in uc.labels.values():
            label_stems = [s for s in ql.stems if s not in STOPWORDS]
            if label_stems and len(label_stems) == len(value_stems) and all(
                any(stem_similarity(a, b) > 0 for b in value_stems) for a in label_stems
            ):
                return ql.label, 95.0, []
        labels = [ql.label for ql in uc.labels.values()]
        if not labels:
            return None, 0.0, []
        matches = process.extract(norm, labels, scorer=fuzz.WRatio, processor=normalize_phrase, limit=5)
        suggestions = [m[0] for m in matches if m[1] >= 60]
        if matches and matches[0][1] >= 88 and (len(matches) == 1 or matches[0][1] - matches[1][1] >= 5):
            return matches[0][0], float(matches[0][1]), suggestions
        return None, float(matches[0][1]) if matches else 0.0, suggestions

    # ----------------------------------------------------------------- build
    def _allows(self, key: str, value: str | None = None) -> bool:
        """Можно ли извлечь ещё одно значение характеристики: повтор допустим только
        для характеристик с выбором нескольких значений (choiceType=2)."""
        if key not in self.assigned:
            return True
        uc = self.schema.chars[key]
        multi = all(pc.choice_type == 2 for pc in uc.by_position.values())
        return multi and value is not None and value not in self.assigned[key]

    def _remember(self, ex: Extracted) -> None:
        if ex.key:
            self.assigned.setdefault(ex.key, set()).add(normalize_phrase(ex.normalized))

    def _make(self, uc: UnifiedChar, source: str, tokens: set[int], value_text: str) -> Extracted:
        start = min(self.tokens[i].start for i in tokens) if tokens else None
        end = max(self.tokens[i].end for i in tokens) if tokens else None
        return Extracted(
            key=uc.key, name=uc.name, source=source,
            original=self.text[start:end] if start is not None else '',
            start=start, end=end, value_text=value_text, token_indices=set(tokens),
        )

    def _add_number(self, uc: UnifiedChar, num: NumberExpr, mention: Mention | None, confidence: float,
                    dim_index: int | None = None) -> Extracted:
        tokens = set(range(num.start_tok, num.end_tok + 1))
        if mention:
            tokens |= mention.tokens
        ex = self._make(uc, 'text', tokens, num.text)
        if mention is None and dim_index is None:
            ex.original = num.text
        ex.confidence = confidence
        unit = num.unit.unit if num.unit else None
        if num.unit and num.unit.weak and not any(u.dimension == unit.dimension for u in uc.units.values()):
            unit = None  # "в", "с", "м" — не единица для этой характеристики
        ex.user_unit = unit
        if num.kind == 'dims' and dim_index is not None:
            ex.value_kind, ex.number = 'number', num.dims[dim_index]
            ex.value_text = f'{format_number(num.dims[dim_index])}{" " + num.unit.text if num.unit else ""}'
            ex.notes.append(f'Определено по записи габаритов «{num.text}».')
        elif num.kind == 'interval':
            ex.value_kind, ex.interval = 'interval', (num.lo, num.hi)
        else:
            ex.value_kind, ex.number = 'number', num.value
        if ex.value_kind == 'number':
            ex.normalized = format_number(ex.number)
        else:
            ex.normalized = _interval_text(*ex.interval)
        ex.unit_display = unit.symbol if unit else ''
        self._validate_number(uc, ex)
        self.consumed |= tokens
        self.results.append(ex)
        self._remember(ex)
        return ex

    def _add_label(self, uc: UnifiedChar, label: str, tokens: set[int], confidence: float,
                   value_text: str | None = None, alternatives: list[str] | None = None) -> Extracted:
        ex = self._make(uc, 'text', tokens, value_text or label)
        ex.value_kind = 'boolean' if uc.is_boolean else 'quality'
        ex.label = label
        ex.normalized = label
        ex.confidence = confidence
        ex.alternatives = alternatives or []
        self._validate_label(uc, ex)
        self.consumed |= tokens
        self.results.append(ex)
        self._remember(ex)
        return ex

    def _unknown_phrase(self, phrase: str, tokens: set[int], value_text: str) -> None:
        """Значение без характеристики КТРУ, классифицируемое по названию phrase."""
        stems = [t.stem for t in tokenize(phrase) if t.is_word]
        key, entry, source = self.index.find_phrase(stems)
        start = min(self.tokens[i].start for i in tokens)
        end = max(self.tokens[i].end for i in tokens)
        ex = Extracted(key=None, name=entry.name if entry else phrase.capitalize(), source='unknown',
                       original=self.text[start:end], start=start, end=end, value_text=value_text,
                       normalized=value_text, value_kind='none', token_indices=set(tokens), confidence=0.5)
        if source == 'ste':
            ex.source, ex.status = 'ste', STATUS_STE
            ex.notes.append(self._ste_note(key))
        else:
            ex.status = STATUS_OTHER_KTRU if source == 'ktru' else STATUS_UNRECOGNIZED
            ex.notes.append('Для найденных позиций КТРУ эта характеристика не задана — на выбор кода не влияет.')
        self.consumed |= set(tokens)
        self.results.append(ex)

    def _ste_note(self, key: str | None) -> str:
        category = self.ste_category
        if category and key and key in self.index.ste_category_chars.get(category, set()):
            where = f'в выгрузке портала поставщиков для категории «{category}»'
        else:
            where = 'в выгрузке портала поставщиков'
        return (f'Характеристика есть {where}, но не задана в КТРУ для найденных позиций — '
                'добавлена как дополнительная, на выбор кода не влияет.')

    def _leftover_pairs(self, seg: tuple[int, int]) -> None:
        """Нераспознанные "цвет синий", "материал обивки экокожа": если начало
        фрагмента — известное название характеристики КТРУ или СТЕ, классифицируем."""
        lo, hi = seg
        run: list[int] = []
        runs: list[list[int]] = []
        for i in range(lo, hi + 1):
            t = self.tokens[i]
            if i in self.consumed or t.kind == 'sym':
                if run:
                    runs.append(run)
                    run = []
                continue
            if t.is_word or t.is_number:
                run.append(i)
        if run:
            runs.append(run)
        for run in runs:
            words = [i for i in run if self.tokens[i].is_word and not self.tokens[i].is_stopword]
            if not words:
                continue
            for size in (3, 2, 1):
                head = words[:size]
                if len(head) < size:
                    continue
                rest = [i for i in run if i > head[-1]]
                head_stems = {self.tokens[i].stem for i in head}
                key, entry, source = self.index.find_phrase(list(head_stems))
                if entry is None:
                    continue
                if not set(entry.stems) <= head_stems:
                    continue  # фраза пользователя покрывает название лишь частично
                value = [i for i in rest if self.tokens[i].is_number or 'а' <= self.tokens[i].norm[0] <= 'я']
                if not (source == 'ste' and entry.is_flag) and (not value or len(rest) > 4):
                    continue  # значение — бренд/артикул латиницей или слишком длинный хвост
                if source == 'ste' and entry.is_flag:
                    self._unknown(head, [], '')   # "трехместный" — признак "Да"
                else:
                    self._unknown(head, rest, self._span_text(set(rest)))
                break

    def _unknown(self, phrase_tokens: list[int], value_tokens: list[int], value_text: str) -> None:
        stems = [self.tokens[i].stem for i in phrase_tokens if self.tokens[i].is_word]
        if not stems:
            return
        phrase = self.text[self.tokens[phrase_tokens[0]].start:self.tokens[phrase_tokens[-1]].end]
        key, entry, source = self.index.find_phrase(stems)
        if source == 'ste' and entry is not None and entry.is_flag and not any(
                self.tokens[i].is_number for i in value_tokens):
            value_tokens = []
        tokens = set(phrase_tokens) | set(value_tokens)
        start = min(self.tokens[i].start for i in tokens)
        end = max(self.tokens[i].end for i in tokens)
        ex = Extracted(key=None, name=entry.name if entry else phrase, source='unknown',
                       original=self.text[start:end], start=start, end=end,
                       value_text=value_text, normalized=value_text, value_kind='none',
                       token_indices=tokens)
        if source == 'ste':
            ex.source = 'ste'
            ex.status = STATUS_STE
            ex.notes.append(self._ste_note(key))
            if entry.is_flag and not any(self.tokens[i].is_number for i in value_tokens):
                ex.normalized = 'Да'
                ex.value_text = ''
                ex.original = phrase
        elif source == 'ktru':
            ex.status = STATUS_OTHER_KTRU
            ex.notes.append(
                'Такая характеристика есть в справочнике КТРУ, но не у позиций с этим наименованием — '
                'на выбор кода не влияет.'
            )
        else:
            ex.status = STATUS_UNRECOGNIZED
            ex.notes.append(
                f'Характеристика «{phrase}» не распознана: её нет ни в справочнике КТРУ, '
                'ни в выгрузке портала поставщиков.'
            )
        ex.confidence = 0.5
        self.consumed |= tokens
        self.results.append(ex)

    # ---------------------------------------------------------- main routine
    def extract(self) -> list[Extracted]:
        for seg in self._segments():
            self._process_segment(seg)
        self._collect_unrecognized()
        return self.results

    def _process_segment(self, seg: tuple[int, int]) -> None:
        lo, hi = seg
        mentions = [
            m for m in self._find_mentions(seg)
            if not (m.tokens <= self.name_tokens) and self._allows(m.key, '\0')
        ]
        numbers = self._find_numbers(seg)
        labels = self._find_labels(seg)
        number_tokens = {i for n in numbers for i in range(n.start_tok, n.end_tok + 1)}
        used_mentions: set[int] = set()
        assigned_keys: set[str] = set()

        # 1) числа: ближайшее упоминание характеристики слева (без чисел между ними)
        for num in numbers:
            mention_idx = None
            for idx in range(len(mentions) - 1, -1, -1):
                m = mentions[idx]
                if m.end_tok < num.start_tok and idx not in used_mentions:
                    between = range(m.end_tok + 1, num.start_tok)
                    if any(self.tokens[j].is_number for j in between):
                        break
                    uc = self.schema.chars[m.key]
                    if uc.is_numeric or any(_looks_numeric(l) for l in uc.labels):
                        mention_idx = idx
                    break
            if mention_idx is None:
                for idx, m in enumerate(mentions):
                    if idx not in used_mentions and 0 <= m.start_tok - num.end_tok <= 2:
                        uc = self.schema.chars[m.key]
                        if uc.is_numeric:
                            mention_idx = idx
                        break
            if mention_idx is not None:
                used_mentions.add(mention_idx)
                m = mentions[mention_idx]
                uc = self.schema.chars[m.key]
                if num.kind == 'dims':
                    num = NumberExpr(num.start_tok, num.end_tok, num.start, num.end, 'number',
                                     value=num.dims[0], unit=num.unit, text=num.text)
                self._add_number(uc, num, m, 0.95)
                assigned_keys.add(uc.key)
                continue
            self._assign_number_by_unit(num, assigned_keys, seg)

        # 2) качественные значения
        by_span: dict[tuple[int, int], list[LabelHit]] = defaultdict(list)
        for hit in labels:
            if hit.tokens & self.consumed:
                continue
            by_span[(hit.start_tok, hit.end_tok)].append(hit)
        # длинные совпадения важнее коротких
        for span in sorted(by_span, key=lambda s: (-(s[1] - s[0]), s[0])):
            hits = [h for h in by_span[span] if not (h.tokens & self.consumed)
                    and self._allows(h.key, h.label_norm)]
            if not hits:
                continue
            hits = [h for h in hits if h.key not in assigned_keys] or hits
            # числовые подписи ("1", "48") и "Да"/"Нет" — только рядом с названием характеристики
            mentioned = {mentions[i].key: i for i in range(len(mentions)) if i not in used_mentions}
            strong = [h for h in hits if h.key in mentioned]
            weak_allowed = [
                h for h in hits
                if not _looks_numeric(h.label_norm) and h.label_norm not in BOOLEAN_LABELS and h.key not in mentioned
            ]
            if strong:
                hit = max(strong, key=lambda h: h.similarity)
                m_idx = mentioned[hit.key]
                used_mentions.add(m_idx)
                tokens = hit.tokens | mentions[m_idx].tokens
                confidence = 0.95 * hit.similarity
                alternatives = []
            elif weak_allowed:
                shared = self._shared_context(weak_allowed, lo)
                if shared:
                    word_idx, group_hits = shared
                    for h in group_hits:
                        uc_h = self.schema.chars[h.key]
                        ex = self._add_label(uc_h, uc_h.labels[h.label_norm].label, h.tokens | {word_idx},
                                             0.8 * h.similarity, value_text=self._span_text(h.tokens | {word_idx}))
                        ex.notes.append(f'Значение отнесено ко всем характеристикам со словом '
                                        f'«{self.tokens[word_idx].text}».')
                        assigned_keys.add(uc_h.key)
                    continue
                hit = max(weak_allowed, key=lambda h: (h.similarity, self._discrimination(h.key)))
                tokens = hit.tokens
                confidence = 0.8 * hit.similarity
                alternatives = sorted({self.schema.chars[h.key].name for h in weak_allowed if h.key != hit.key})
            else:
                continue
            uc = self.schema.chars[hit.key]
            ex = self._add_label(uc, uc.labels[hit.label_norm].label, tokens, confidence,
                                 value_text=self._span_text(hit.tokens), alternatives=alternatives)
            if alternatives:
                ex.notes.append('Значение встречается и у характеристик: ' + ', '.join(alternatives[:4]) + '.')
            assigned_keys.add(uc.key)

        # 3) упоминания без значения: "с регулировкой высоты", "без подлокотников",
        #    "цвет: салатовый"
        for idx, m in enumerate(mentions):
            if idx in used_mentions or m.tokens & self.consumed:
                continue
            uc = self.schema.chars[m.key]
            if uc.is_boolean:
                label = 'Нет' if m.negated else 'Да'
                if normalize_phrase(label) in uc.labels:
                    tokens = set(m.tokens)
                    if m.negated:
                        tokens |= {j for j in range(max(lo, m.start_tok - 2), m.start_tok)
                                   if self.tokens[j].norm in NEGATIONS}
                    self._add_label(uc, uc.labels[normalize_phrase(label)].label, tokens, 0.85,
                                    value_text=self._span_text(tokens))
                    used_mentions.add(idx)
                    continue
            # значение после двоеточия / до конца сегмента
            value_tokens = [
                j for j in range(m.end_tok + 1, hi + 1)
                if j not in self.consumed and self.tokens[j].kind in ('word', 'number')
            ]
            next_mentions = [mm.start_tok for mm in mentions if mm.start_tok > m.end_tok]
            if next_mentions:
                value_tokens = [j for j in value_tokens if j < min(next_mentions)]
            value_text = self._span_text(set(value_tokens)) if value_tokens else ''
            ex = self._make(uc, 'text', set(m.tokens) | set(value_tokens), value_text)
            ex.positions_with_char = set(uc.by_position)
            if value_text and uc.labels:
                label, score, suggestions = self.resolve_quality_text(uc, value_text)
                if label is not None:
                    ex.value_kind = 'quality'
                    ex.label = label
                    ex.normalized = label
                    ex.confidence = 0.75
                    if score < 100:
                        ex.notes.append(f'Значение «{value_text}» сопоставлено со значением КТРУ «{label}».')
                    self._validate_label(uc, ex)
                else:
                    ex.value_kind = 'quality'
                    ex.status = STATUS_INVALID
                    ex.normalized = value_text
                    ex.suggestions = suggestions or uc.option_labels(limit=8)
                    ex.notes.append(f'Значение «{value_text}» не найдено в перечне значений КТРУ.')
            elif value_text and not uc.labels and not uc.is_numeric:
                ex.value_kind = 'quality'
                ex.normalized = value_text
                ex.status = STATUS_NO_CONSTRAINTS
                ex.notes.append('В справочнике КТРУ для этой характеристики нет перечня значений.')
            else:
                ex.value_kind = 'none'
                ex.status = STATUS_NO_VALUE
                ex.notes.append('Характеристика названа, но значение не указано.')
                ex.suggestions = uc.option_labels(limit=8)
            self.consumed |= ex.token_indices
            self.results.append(ex)
            self._remember(ex)
            used_mentions.add(idx)

        # 4) "X: Y" и "X 25 ед." с неизвестным названием X
        self._unknown_pairs(seg, numbers)
        # 5) "цвет синий" — название характеристики без двоеточия
        self._leftover_pairs(seg)

    def _assign_number_by_unit(self, num: NumberExpr, assigned: set[str], seg: tuple[int, int]) -> None:
        if num.unit is None:
            return
        unit = num.unit.unit
        compatible = [
            uc for uc in self.schema.chars.values()
            if uc.is_numeric and any(u.dimension == unit.dimension for u in uc.units.values())
            and uc.key not in assigned
        ]
        if num.kind == 'dims':
            order = [('длин',), ('ширин',), ('высот',), ('глубин',)]
            by_dim = {}
            for uc in compatible:
                for (stem_,) in order:
                    if uc.stems and uc.stems[0] == stem_ and len(uc.stems) == 1:
                        by_dim[stem_] = uc
            sequence = [by_dim[s] for (s,) in order if s in by_dim]
            if len(sequence) >= len(num.dims):
                if 'глубин' in by_dim and 'длин' not in by_dim and len(num.dims) == 3:
                    sequence = [by_dim.get('ширин'), by_dim.get('глубин'), by_dim.get('высот')]
                if all(sequence[:len(num.dims)]):
                    for k, uc in enumerate(sequence[:len(num.dims)]):
                        self._add_number(uc, num, None, 0.6, dim_index=k)
                        assigned.add(uc.key)
                    return
            # в КТРУ у этих позиций нет длины/ширины/высоты: это габариты товара
            tokens = set(range(num.start_tok, num.end_tok + 1))
            self._unknown_phrase('габаритные размеры', tokens, num.text)
            return
        if num.unit.weak:
            compatible = [uc for uc in compatible if uc.units]
        if len(compatible) == 1 and num.kind != 'dims':
            ex = self._add_number(compatible[0], num, None, 0.6)
            ex.notes.append('Характеристика определена по единице измерения.')
            assigned.add(compatible[0].key)
            return
        if len(compatible) > 1 and num.kind == 'number':
            fitting = [uc for uc in compatible if self._accepts_value(uc, num.value, unit)]
            if len(fitting) == 1:
                ex = self._add_number(fitting[0], num, None, 0.5)
                ex.notes.append('Характеристика определена по единице измерения и допустимым диапазонам КТРУ '
                                f'(другие характеристики с этой единицей не допускают {num.text}).')
                assigned.add(fitting[0].key)
                return
            if fitting:
                compatible = fitting
        if len(compatible) > 1 and not num.unit.weak:
            # неоднозначно: показываем пользователю, к чему может относиться число
            tokens = set(range(num.start_tok, num.end_tok + 1))
            ex = Extracted(key=None, name=f'Значение {num.text}', source='text', original=num.text,
                           start=num.start, end=num.end, value_text=num.text, normalized=num.text,
                           value_kind='number', status=STATUS_AMBIGUOUS, token_indices=tokens,
                           confidence=0.3)
            names = sorted(uc.name for uc in compatible)
            ex.alternatives = names[:10]
            ex.notes.append('Не удалось определить, к какой характеристике относится значение. '
                            'Возможные характеристики: ' + ', '.join(names[:6]) + '.')
            self.consumed |= tokens
            self.results.append(ex)

    def _accepts_value(self, uc: UnifiedChar, value: float, unit: Unit | None) -> bool:
        for pc in uc.by_position.values():
            for option in pc.options:
                if option.kind in ('range', 'concrete'):
                    v = self._convert_for(option, value, unit)
                    if v is not None and option.contains(v):
                        return True
        return False

    def _unknown_pairs(self, seg: tuple[int, int], numbers: list[NumberExpr]) -> None:
        lo, hi = seg
        toks = self.tokens
        # "X: Y"
        for i in range(lo, hi + 1):
            if toks[i].norm != ':':
                continue
            left = []
            j = i - 1
            while j >= lo and toks[j].is_word and j not in self.consumed and len(left) < 5:
                left.insert(0, j)
                j -= 1
            right = [k for k in range(i + 1, hi + 1) if k not in self.consumed and toks[k].kind in ('word', 'number')]
            if left and right:
                self._unknown(left, right, self._span_text(set(right)))
        # "X 25 ед." — число с единицей, которое не удалось связать с характеристикой
        for num in numbers:
            tokens = set(range(num.start_tok, num.end_tok + 1))
            if tokens & self.consumed:
                continue
            left = []
            j = num.start_tok - 1
            while j >= lo and toks[j].is_word and j not in self.consumed and len(left) < 4:
                if toks[j].is_stopword and not left:
                    j -= 1
                    continue
                left.insert(0, j)
                j -= 1
            left = [k for k in left if not toks[k].is_stopword] or left
            if left and any('а' <= toks[k].norm[0] <= 'я' for k in left):
                self._unknown(left, sorted(tokens), num.text)

    def _collect_unrecognized(self) -> None:
        current: list[int] = []
        groups: list[list[int]] = []
        for i, t in enumerate(self.tokens):
            if i in self.consumed or t.kind == 'sym' or t.is_stopword or (t.is_word and len(t.norm) < 2):
                if current:
                    groups.append(current)
                    current = []
                continue
            current.append(i)
        if current:
            groups.append(current)
        for g in groups:
            start, end = self.tokens[g[0]].start, self.tokens[g[-1]].end
            words = [self.tokens[i] for i in g]
            latin = all(t.is_number or not ('а' <= t.norm[0] <= 'я') for t in words)
            self.unrecognized_fragments.append({
                'text': self.text[start:end], 'start': start, 'end': end,
                'kind': 'model_or_brand' if latin else 'unknown',
            })

    # --------------------------------------------------------------- helpers
    def _span_text(self, tokens: set[int]) -> str:
        if not tokens:
            return ''
        start = min(self.tokens[i].start for i in tokens)
        end = max(self.tokens[i].end for i in tokens)
        return self.text[start:end]

    def _shared_context(self, hits: list[LabelHit], seg_lo: int) -> tuple[int, list[LabelHit]] | None:
        """Слово перед значением, общее для названий нескольких характеристик:
        "обивка экокожа" -> "Вид материала обивки спинки" и "... обивки сиденья"."""
        if len(hits) < 2:
            return None
        first = min(h.start_tok for h in hits)
        for j in range(first - 1, max(seg_lo, first - 3) - 1, -1):
            t = self.tokens[j]
            if j in self.consumed or not t.is_word or t.is_stopword or t.stem in GENERIC_CHAR_STEMS:
                continue
            group = [h for h in hits if any(stem_similarity(s, t.stem) > 0 for s in self.schema.chars[h.key].stems)]
            if len(group) >= 2:
                return j, group
            break
        return None

    def _discrimination(self, key: str) -> float:
        uc = self.schema.chars[key]
        signatures = {frozenset(o.norm for o in pc.options) for pc in uc.by_position.values()}
        bonus = 1.0 if uc.kind == 1 else 0.0
        return len(signatures) + bonus + (0.5 if uc.required else 0.0)


_CHUNK_RE = re.compile(r'\S+')


def _inside_code(text: str, start: int, end: int) -> bool:
    """Число — часть артикула/модели, если "слово" без пробелов содержит
    латинские буквы или несколько дефисов: "SKDB-UT6-883", "PH2", "i5-12500H"."""
    left = start
    while left > 0 and not text[left - 1].isspace():
        left -= 1
    right = end
    while right < len(text) and not text[right].isspace():
        right += 1
    chunk = text[left:right].strip('.,;:()"\'')
    unit = match_unit_at(text, end)
    if unit is not None and unit.end >= right:
        chunk = text[left:end]  # "15мм", "220В": число + единица
    letters = re.sub(r'[\d.,\-–/x×хХ*+%°"\s]', '', chunk)
    if re.search(r'[a-zA-Z]', letters):
        return True
    if letters and not unit:
        return True
    return chunk.count('-') >= 2


def _most_specific(options: list[ValueOption]) -> ValueOption:
    """Самое узкое из подходящих значений: точное число, затем диапазон
    наименьшей ширины ("≥ 3 шт" точнее, чем "≥ 1 шт")."""
    def width(o: ValueOption) -> tuple[int, float, float]:
        if o.kind in ('concrete', 'quality'):
            return (0, 0.0, 0.0)
        lower = o.lower if o.lower is not None else float('-inf')
        upper = o.upper if o.upper is not None else float('inf')
        return (1, upper - lower, -lower)
    return min(options, key=width)


def _is_negative_label(label_norm: str) -> bool:
    words = label_norm.split()
    return bool(words) and words[0] in ('без', 'нет', 'отсутствует', 'отсутствуют')


def _looks_numeric(label_norm: str) -> bool:
    return bool(re.fullmatch(r'[\d.,\s\-–/x]+', label_norm or ''))


def _interval_text(lo: float | None, hi: float | None) -> str:
    if lo is not None and hi is not None:
        return f'{format_number(lo)}–{format_number(hi)}'
    if lo is not None:
        return f'≥ {format_number(lo)}'
    if hi is not None:
        return f'≤ {format_number(hi)}'
    return ''


def parse_user_value(extractor: CharacteristicExtractor, uc: UnifiedChar, value_text: str) -> Extracted:
    """Значение, введённое/подтверждённое пользователем в интерфейсе."""
    ex = Extracted(key=uc.key, name=uc.name, source='user', original=value_text, value_text=value_text,
                   confidence=1.0)
    tokens = tokenize(value_text)
    sub = CharacteristicExtractor(value_text, tokens, extractor.schema, extractor.index, set(), set())
    numbers = sub._find_numbers((0, len(tokens) - 1)) if tokens else []
    if numbers and uc.is_numeric:
        num = numbers[0]
        unit = num.unit.unit if num.unit else None
        ex.user_unit = unit
        if num.kind == 'interval':
            ex.value_kind, ex.interval = 'interval', (num.lo, num.hi)
            ex.normalized = _interval_text(num.lo, num.hi)
        else:
            value = num.value if num.kind == 'number' else num.dims[0]
            ex.value_kind, ex.number = 'number', value
            ex.normalized = format_number(value)
        ex.unit_display = unit.symbol if unit else ''
        extractor._validate_number(uc, ex)
        return ex
    label, score, suggestions = extractor.resolve_quality_text(uc, value_text)
    ex.value_kind = 'boolean' if uc.is_boolean else 'quality'
    if label is None:
        if not uc.labels and not uc.is_numeric:
            ex.normalized = value_text
            ex.status = STATUS_NO_CONSTRAINTS
            ex.accepted_positions = set(uc.by_position)
            ex.positions_with_char = set(uc.by_position)
            ex.notes.append('В справочнике КТРУ для этой характеристики нет перечня значений.')
            return ex
        ex.normalized = value_text
        ex.status = STATUS_INVALID
        ex.positions_with_char = set(uc.by_position)
        ex.suggestions = suggestions or uc.option_labels(limit=8)
        ex.notes.append(f'Значение «{value_text}» не найдено в перечне значений КТРУ.')
        return ex
    ex.label = label
    ex.normalized = label
    if score < 100:
        ex.notes.append(f'Значение «{value_text}» сопоставлено со значением КТРУ «{label}».')
    extractor._validate_label(uc, ex)
    return ex
