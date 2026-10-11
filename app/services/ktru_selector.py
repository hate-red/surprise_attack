"""
Выбор позиции КТРУ: поиск наименования и поэтапное сужение кандидатов.

Этапы фиксируют реально выполненные операции (сколько позиций было и
сколько осталось), поэтому интерфейс показывает настоящее сужение, а не
анимацию.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from rapidfuzz import fuzz, process

from app.services.characteristic_extractor import (
    STATUS_CONFLICT,
    CandidateSchema,
    Extracted,
)
from app.services.ktru_index import KtruIndex
from app.services.nlp.matching import stem_similarity
from app.services.nlp.text import STOPWORDS, Token, normalize_phrase, tokenize

MIN_NAME_SCORE = 4.0
MIN_NAME_COVERAGE = 0.3
MAX_CANDIDATE_GROUPS = 40
SHORTLIST_SIZE = 12
POSITION_WEIGHTS = (1.6, 1.3, 1.15)
UNMATCHED_PENALTY = 0.45
HEAD_BONUS = 1.0
HEAD_MISS_PENALTY = 0.5
EVIDENCE_WORD = 3.0
EVIDENCE_NUMBER = 2.0


# ======================================================= наименование
@dataclass
class GroupScore:
    group: int
    score: float
    coverage: float
    evidence: frozenset[int]
    head_matched: bool
    exact: bool                      # все слова наименования найдены точно
    fuzzy: bool                      # использованы исправленные опечатки
    evidence_score: float = 0.0      # подтверждение характеристиками и значениями КТРУ
    complete: bool = False           # все слова наименования найдены (в т.ч. по исправленным опечаткам)

    @property
    def total(self) -> float:
        return self.score + self.evidence_score


@dataclass
class NameMatch:
    found: bool
    groups: list[int] = field(default_factory=list)
    best: GroupScore | None = None
    token_indices: set[int] = field(default_factory=set)
    stems: set[str] = field(default_factory=set)
    confidence: str = 'none'         # high | medium | low | none
    alternatives: list[str] = field(default_factory=list)
    shortlist: list[GroupScore] = field(default_factory=list)
    scores: list[GroupScore] = field(default_factory=list)


def match_name(tokens: list[Token], corrected: dict[int, str], index: KtruIndex) -> NameMatch:
    """corrected: индекс токена -> основа исправленного слова (опечатки)."""
    content = [
        i for i, t in enumerate(tokens)
        if t.is_word and not t.is_stopword and len(t.norm) > 1
    ]
    weights = {i: (POSITION_WEIGHTS[k] if k < len(POSITION_WEIGHTS) else (1.0 if k < 8 else 0.8))
               for k, i in enumerate(content)}
    variants: dict[int, list[tuple[str, bool]]] = {
        i: [(tokens[i].stem, False)] + ([(corrected[i], True)] if i in corrected else []) for i in content
    }

    touched: set[int] = set()
    for i in content:
        for stem, _ in variants[i]:
            touched |= index.stem_to_groups.get(stem, set())
            for similar in _similar_stems(stem, index):
                touched |= index.stem_to_groups.get(similar, set())

    scores: list[GroupScore] = []
    for g in touched:
        group = index.groups[g]
        unique_stems = list(dict.fromkeys(group.stems))
        if not unique_stems:
            continue
        positive = unmatched = total = matched_weight = 0.0
        evidence: set[int] = set()
        used_tokens: set[int] = set()
        exact = True
        fuzzy = False
        head_matched = False
        for k, gs in enumerate(unique_stems):
            idf = index.idf(gs)
            total += idf
            best: tuple[float, int | None, bool] = (0.0, None, False)
            for i in content:
                if i in used_tokens:
                    continue
                for stem, is_fuzzy in variants[i]:
                    sim = stem_similarity(gs, stem) * (0.9 if is_fuzzy else 1.0)
                    if sim > best[0]:
                        best = (sim, i, is_fuzzy)
            if best[1] is None:
                unmatched += idf
                exact = False
                continue
            sim, i, is_fuzzy = best
            used_tokens.add(i)
            evidence.add(i)
            positive += idf * sim * weights[i]
            matched_weight += idf * sim
            exact = exact and sim >= 1.0 and not is_fuzzy
            fuzzy = fuzzy or is_fuzzy
            if k == 0:
                head_matched = True
        head_idf = index.idf(unique_stems[0])
        score = positive - UNMATCHED_PENALTY * unmatched + (
            HEAD_BONUS * head_idf if head_matched else -HEAD_MISS_PENALTY * head_idf)
        scores.append(GroupScore(g, score, matched_weight / total if total else 0.0,
                                 frozenset(evidence), head_matched, exact, fuzzy,
                                 complete=unmatched == 0))

    if not scores:
        return NameMatch(found=False, alternatives=_fuzzy_alternatives(tokens, index))

    scores.sort(key=lambda s: (-s.score, -s.coverage, len(index.groups[s.group].stems)))
    best = scores[0]
    if best.score < MIN_NAME_SCORE or best.coverage < MIN_NAME_COVERAGE:
        alternatives = [index.groups[s.group].name for s in scores[:5] if s.score > 0]
        return NameMatch(found=False, best=best,
                         alternatives=alternatives or _fuzzy_alternatives(tokens, index))

    shortlist = [x for x in scores if x.score >= 0.4 * best.score][:SHORTLIST_SIZE]
    match = NameMatch(found=True, best=best, shortlist=shortlist, scores=scores)
    choose_groups(match, index)
    return match


def choose_groups(match: NameMatch, index: KtruIndex) -> None:
    """Выбор групп наименований после (повторного) ранжирования shortlist."""
    ranked = sorted(match.shortlist or match.scores,
                    key=lambda s: (-s.total, -s.coverage, len(index.groups[s.group].stems)))
    best = ranked[0]
    pool = match.scores
    same_evidence = [
        s for s in pool
        if s.evidence == best.evidence and (s.head_matched or not best.head_matched)
    ]
    exact_full = [s for s in same_evidence if s.complete]
    chosen = (exact_full or same_evidence)[:MAX_CANDIDATE_GROUPS]
    if best not in chosen:
        chosen = [best] + chosen[:MAX_CANDIDATE_GROUPS - 1]

    if best.complete and not best.fuzzy:
        confidence = 'high'
    elif best.complete or best.coverage >= 0.5:
        confidence = 'medium'
    else:
        confidence = 'low'

    stems: set[str] = set()
    for s in chosen:
        stems |= set(index.groups[s.group].stems)
    chosen_ids = {c.group for c in chosen}
    match.best = best
    match.groups = [s.group for s in chosen]
    match.token_indices = set(best.evidence)
    match.stems = stems
    match.confidence = confidence
    match.alternatives = [index.groups[s.group].name for s in ranked[:8] if s.group not in chosen_ids][:5]


def rerank_with_characteristics(match: NameMatch, schema: CandidateSchema, tokens: list[Token],
                                text: str, index: KtruIndex) -> None:
    """Второй проход: подтверждение наименования характеристиками КТРУ.

    Для каждой группы из shortlist считается, сколько слов и чисел описания,
    не вошедших в наименование, объясняются названиями характеристик,
    допустимыми значениями и единицами измерения позиций этой группы.
    """
    from app.services.nlp.units import match_unit_at

    if len(match.shortlist) < 2:
        return
    number_units = []
    for t in tokens:
        if t.is_number:
            unit_match = match_unit_at(text, t.end)
            if unit_match is not None:
                number_units.append(unit_match.unit)
    for gs in match.shortlist:
        group = index.groups[gs.group]
        char_keys: set[str] = set()
        for pid in group.position_ids:
            char_keys |= set(schema.position_chars.get(pid, {}).keys())
        if not char_keys:
            gs.evidence_score = 0.0
            continue
        explain: set[str] = set()
        dimensions: set[str] = set()
        for key in char_keys:
            uc = schema.chars[key]
            explain.update(uc.stems)
            for ql in uc.labels.values():
                explain.update(ql.stems)
            for unit in uc.units.values():
                dimensions.add(unit.dimension)
        score = 0.0
        for i, t in enumerate(tokens):
            if i in gs.evidence or not t.is_word or t.is_stopword or len(t.norm) < 3:
                continue
            if any(e and e[0] == t.stem[0] and stem_similarity(e, t.stem) > 0 for e in explain):
                score += EVIDENCE_WORD
        score += EVIDENCE_NUMBER * sum(1 for u in number_units if u.dimension in dimensions)
        gs.evidence_score = score
    choose_groups(match, index)


def _similar_stems(stem: str, index: KtruIndex) -> set[str]:
    from app.services.nlp.matching import root

    r = root(stem)
    found = set(index.root_to_stems.get(stem, set())) | set(index.root_to_stems.get(r, set()))
    if r in index.stem_to_groups:
        found.add(r)
    return {s for s in found if s != stem and stem_similarity(s, stem) > 0}


def _fuzzy_alternatives(tokens: list[Token], index: KtruIndex) -> list[str]:
    words = [t.norm for t in tokens if t.is_word and not t.is_stopword][:4]
    if not words or not index.groups:
        return []
    query = ' '.join(words)
    names = [g.norm for g in index.groups]
    matches = process.extract(query, names, scorer=fuzz.WRatio, limit=5, score_cutoff=70)
    return [index.groups[m[2]].name for m in matches]


# ======================================================= сужение
@dataclass
class Stage:
    title: str
    detail: str
    count_before: int | None
    count_after: int
    applied: bool = True
    kind: str = 'filter'             # catalog | name | characteristic | okpd2 | user | final
    note: str | None = None


@dataclass
class Narrowing:
    stages: list[Stage]
    remaining: list[str]
    final_code: str | None
    templates_dropped: list[str] = field(default_factory=list)


def narrow(
    index: KtruIndex,
    name: NameMatch,
    candidates: list[str],
    extracted: list[Extracted],
    tokens: list[Token],
    consumed: set[int],
    selected_code: str | None,
) -> Narrowing:
    total = len(index.positions)
    stages = [Stage('Справочник КТРУ', 'актуальные позиции (статус ACTIVE)', None, total, kind='catalog')]
    group_names = [index.groups[g].name for g in name.groups]
    detail = f'«{group_names[0]}»' if len(group_names) == 1 else (
        f'{len(group_names)} наименований: ' + '; '.join(f'«{n}»' for n in group_names[:4])
        + (' …' if len(group_names) > 4 else '')
    )
    stages.append(Stage('Наименование товара', detail, total, len(candidates), kind='name'))
    remaining = list(candidates)

    for ex in extracted:
        if not ex.usable:
            continue
        current = set(remaining)
        has = current & ex.positions_with_char
        accepted = current & ex.accepted_positions
        title = ex.name
        value = ex.normalized + (f' {ex.unit_display}' if ex.unit_display and ex.value_kind in ('number', 'interval') else '')
        if ex.matched_option and ex.value_kind in ('number', 'interval') and \
                normalize_phrase(ex.matched_option) != normalize_phrase(value):
            value += f' → {ex.matched_option}'
        if not has:
            stages.append(Stage(title, value, len(current), len(current), applied=False, kind='characteristic',
                                note='Характеристики нет у оставшихся позиций — фильтр не применён.'))
            continue
        if not accepted:
            ex.status = STATUS_CONFLICT
            ex.notes.append('Значение допустимо для других позиций с этим наименованием, '
                            'но противоречит ранее указанным характеристикам — фильтр не применён.')
            stages.append(Stage(title, value, len(current), len(current), applied=False, kind='characteristic',
                                note='Противоречит другим характеристикам — фильтр не применён.'))
            continue
        remaining = [p for p in remaining if p in accepted]
        stages.append(Stage(title, value, len(current), len(remaining), kind='characteristic'))

    # уточнение по названию группировки ОКПД2 ("трикотажные", "для мальчиков")
    if len(remaining) > 1:
        free_stems = {
            t.stem for i, t in enumerate(tokens)
            if i not in consumed and t.is_word and not t.is_stopword and len(t.norm) > 2
        } - name.stems
        if free_stems:
            overlap: dict[str, int] = {}
            for pid in remaining:
                info = index.positions[pid]
                okpd_stems = set(_okpd_stems(info.okpd2_name))
                overlap[pid] = sum(1 for s in free_stems if any(stem_similarity(s, o) > 0 for o in okpd_stems))
            best = max(overlap.values())
            if best > 0 and any(v < best for v in overlap.values()):
                before = len(remaining)
                remaining = [p for p in remaining if overlap[p] == best]
                okpd_names = sorted({index.positions[p].okpd2_name or '' for p in remaining})
                stages.append(Stage('Группировка ОКПД2', '; '.join(okpd_names[:2]), before, len(remaining), kind='okpd2'))

    if selected_code:
        before = len(remaining)
        if selected_code in index.positions:
            remaining = [selected_code]
            stages.append(Stage('Выбор пользователя', selected_code, before, 1, kind='user'))

    final_code = None
    templates_dropped: list[str] = []
    if len(remaining) == 1:
        final_code = remaining[0]
    else:
        concrete = [p for p in remaining if not index.positions[p].is_template]
        if len(concrete) == 1 and len(remaining) > 1:
            templates_dropped = [p for p in remaining if index.positions[p].is_template]
            stages.append(Stage(
                'Шаблонные позиции', 'предпочтена конкретная позиция вместо шаблона',
                len(remaining), 1, kind='final',
                note='Шаблонная позиция КТРУ допускает все значения; выбрана конкретная позиция.',
            ))
            final_code = concrete[0]
    return Narrowing(stages=stages, remaining=remaining, final_code=final_code, templates_dropped=templates_dropped)


def _okpd_stems(name: str | None) -> list[str]:
    if not name:
        return []
    return [t.stem for t in tokenize(normalize_phrase(name)) if t.is_word and t.norm not in STOPWORDS]


# ======================================================= что уточнить
@dataclass
class Suggestion:
    key: str
    name: str
    required: bool
    kind: int | None
    options: list[dict]               # [{'value': 'Деревянный', 'count': 2}]
    reason: str


def suggest_characteristics(
    schema: CandidateSchema,
    remaining: list[str],
    index: KtruIndex,
    already: set[str],
    limit: int = 5,
) -> list[Suggestion]:
    concrete = [p for p in remaining if not index.positions[p].is_template]
    pool = concrete if len(concrete) >= 2 else remaining
    if len(pool) < 2:
        return []
    result: list[tuple[float, Suggestion]] = []
    for key, uc in schema.chars.items():
        if key in already:
            continue
        signatures = []
        option_counts: Counter[str] = Counter()
        for pid in pool:
            pc = uc.by_position.get(pid)
            if pc is None:
                signatures.append(None)
                continue
            labels = tuple(sorted({o.label for o in pc.options}))
            signatures.append(labels)
            for label in labels:
                option_counts[label] += 1
        distinct = set(signatures)
        if len(distinct) < 2:
            continue
        present = sum(1 for s in signatures if s is not None)
        # характеристика различает позиции, если её значения отличаются
        score = len(distinct) + (2.0 if uc.kind == 1 else 0.0) + (1.0 if uc.required else 0.0) \
            + present / len(pool)
        if all(c == len(pool) for c in option_counts.values()) and None not in distinct:
            continue
        options = [{'value': label, 'count': count} for label, count in option_counts.most_common(15)]
        reason = 'значение различается у оставшихся позиций'
        if None in distinct:
            reason = f'задана только у {present} из {len(pool)} позиций'
        result.append((score, Suggestion(key, uc.name, uc.required, uc.kind, options, reason)))
    result.sort(key=lambda x: -x[0])
    return [s for _, s in result[:limit]]


def name_refinements(index: KtruIndex, remaining: list[str]) -> list[dict]:
    counts: Counter[int] = Counter(index.positions[p].group for p in remaining)
    if len(counts) < 2:
        return []
    return [{'name': index.groups[g].name, 'count': c} for g, c in counts.most_common(10)]


def okpd2_refinements(index: KtruIndex, remaining: list[str]) -> list[dict]:
    counts: Counter[tuple[str, str]] = Counter(
        (index.positions[p].okpd2_code or '', index.positions[p].okpd2_name or '') for p in remaining
    )
    if len(counts) < 2:
        return []
    return [{'code': code, 'name': name, 'count': c} for (code, name), c in counts.most_common(8)]


def validity_note(index: KtruIndex, code: str) -> str | None:
    info = index.positions.get(code)
    if info is None:
        return None
    now = datetime.now()
    if info.application_date_start and info.application_date_start > now:
        return f'Позиция применяется с {info.application_date_start:%d.%m.%Y}.'
    if info.application_date_end and info.application_date_end < now:
        return f'Срок применения позиции истёк {info.application_date_end:%d.%m.%Y}.'
    return None
