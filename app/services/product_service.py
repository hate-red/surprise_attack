"""
Анализ описания товара: наименование -> характеристики -> код КТРУ.

Полностью детерминированный конвейер без внешних сервисов и LLM:
  1. нормализация текста и проверка опечаток по словарю КТРУ/СТЕ;
  2. поиск наименования товара в индексе КТРУ (основы слов + IDF);
  3. загрузка характеристик кандидатов из PostgreSQL;
  4. извлечение характеристик, нормализация единиц, проверка значений;
  5. поэтапное сужение множества позиций и выбор итогового кода.
"""
from __future__ import annotations

import time
from collections import Counter
from typing import Any

from rapidfuzz import fuzz, process

from app.repositories.positions import PositionRepository
from app.schemas.positions import (
    CandidateOut,
    CharacteristicRow,
    FragmentOut,
    Message,
    ParseRequest,
    ParseResponse,
    PositionResponse,
    ProductOut,
    SpellingIssueOut,
    StageOut,
    SuggestionOut,
)
from app.services.characteristic_extractor import (
    STATUS_AMBIGUOUS,
    STATUS_CONFLICT,
    STATUS_INVALID,
    STATUS_MISSING,
    STATUS_NO_CONSTRAINTS,
    STATUS_NO_VALUE,
    STATUS_OK,
    STATUS_OTHER_KTRU,
    STATUS_STE,
    STATUS_UNIT_MISMATCH,
    STATUS_UNRECOGNIZED,
    CandidateSchema,
    CharacteristicExtractor,
    Extracted,
    parse_user_value,
)
from app.services.ktru_index import KtruIndex, get_index, load_index
from app.services.ktru_selector import (
    Narrowing,
    match_name,
    rerank_with_characteristics,
    name_refinements,
    narrow,
    okpd2_refinements,
    suggest_characteristics,
    validity_note,
)
from app.services.nlp.spelling import SpellChecker, apply_corrections
from app.services.nlp.text import normalize_phrase, normalize_text, tokenize, word_stem

MAX_DETAILED_POSITIONS = 3000
MAX_CANDIDATES_IN_RESPONSE = 20
ERROR_STATUSES = {STATUS_INVALID, STATUS_UNIT_MISMATCH, STATUS_CONFLICT}


class ReferenceNotLoadedError(RuntimeError):
    """Справочник КТРУ ещё не загружен в БД."""


_spell_checkers: dict[int, SpellChecker] = {}


def _spell_checker(index: KtruIndex) -> SpellChecker:
    checker = _spell_checkers.get(id(index))
    if checker is None:
        _spell_checkers.clear()
        checker = SpellChecker(index.vocabulary, index.vocabulary_stems)
        _spell_checkers[id(index)] = checker
    return checker


def check_typos_in_text(text: str) -> dict[str, Any]:
    """Опечатки по словарю КТРУ/СТЕ (локально, без внешних сервисов).

    -> {"has_typo": bool, "suggestion": исправленный текст, "issues": [...]}
    Если индекс ещё не загружен, опечатки не проверяются.
    """
    if not text or not isinstance(text, str):
        return {'has_typo': False, 'suggestion': text, 'issues': []}
    index = get_index()
    if not index.loaded:
        return {'has_typo': False, 'suggestion': text, 'issues': []}
    issues = _spell_checker(index).check_tokens(tokenize(normalize_text(text)))
    return {
        'has_typo': bool(issues),
        'suggestion': apply_corrections(text, issues) if issues else text,
        'issues': [
            {'original': i.original, 'suggestion': i.suggestion, 'start': i.start, 'end': i.end}
            for i in issues
        ],
    }


def _char_type(uc) -> str:
    if uc is None:
        return 'unknown'
    return 'quantity' if uc.is_numeric else 'quality'


class ProductParsingService:
    def __init__(self, llm_client=None, ner_model=None):
        # LLM не используется: конвейер детерминированный (см. docstring модуля).
        self.llm = llm_client
        self.ner = ner_model

    async def get_validate(self, text: str, request: ParseRequest | None = None) -> ParseResponse:
        if len(text.strip()) < 3:
            raise ValueError('Слишком короткий текст, не похоже на запрос товара')
        request = request or ParseRequest()
        timings: dict[str, int] = {}
        started = time.perf_counter()

        index = await load_index()
        if not index.positions:
            raise ReferenceNotLoadedError(
                'Справочник КТРУ не загружен в базу данных. '
                'Выполните: python -m app.parser.ktru_importer'
            )
        timings['index'] = int((time.perf_counter() - started) * 1000)

        # 1. нормализация и опечатки
        normalized = normalize_text(text)
        tokens = tokenize(normalized)
        checker = _spell_checker(index)
        issues = checker.check_tokens(tokens)
        corrected: dict[int, str] = {}
        by_start = {t.start: i for i, t in enumerate(tokens)}
        for issue in issues:
            i = by_start.get(issue.start)
            if i is not None:
                corrected[i] = word_stem(issue.suggestion)
        corrected_query = apply_corrections(text, issues) if issues else None

        # 2. наименование
        t0 = time.perf_counter()
        name = match_name(tokens, corrected, index)
        timings['name'] = int((time.perf_counter() - t0) * 1000)

        # токены для сопоставления значений: исправленные опечатки
        match_tokens = [t for t in tokens]
        for i, stem in corrected.items():
            original = tokens[i]
            match_tokens[i] = type(original)(
                text=original.text, norm=original.norm, kind=original.kind,
                start=original.start, end=original.end, stem=stem,
            )

        if not name.found:
            return self._name_not_found(text, normalized, match_tokens, index, name, issues,
                                        corrected_query, timings, started)

        # 3. характеристики кандидатов из БД; второй проход ранжирования
        #    наименований по совпадению характеристик и значений
        t0 = time.perf_counter()
        shortlist_ids = self._limit_ids(index, [g.group for g in name.shortlist] + name.groups)
        rows = await PositionRepository.get_characteristic_rows(shortlist_ids)
        rerank_with_characteristics(name, CandidateSchema(rows), match_tokens, normalized, index)
        candidate_ids = self._limit_ids(index, name.groups)
        truncated = sum(len(index.groups[g].position_ids) for g in name.groups) > len(candidate_ids)
        wanted = set(candidate_ids)
        schema = CandidateSchema([r for r in rows if r[1] in wanted])
        missing = wanted - set(schema.position_chars) - {r[1] for r in rows}
        if missing and len(missing) == len(wanted):
            schema = CandidateSchema(await PositionRepository.get_characteristic_rows(candidate_ids))
        timings['db'] = int((time.perf_counter() - t0) * 1000)

        # 4. извлечение и проверка характеристик
        t0 = time.perf_counter()
        extractor = CharacteristicExtractor(normalized, match_tokens, schema, index,
                                            name.token_indices, name.stems)
        results = extractor.extract()
        results = self._apply_user_input(results, request, extractor, schema, index)
        timings['extract'] = int((time.perf_counter() - t0) * 1000)

        # 5. сужение
        t0 = time.perf_counter()
        narrowing = narrow(index, name, candidate_ids, results, match_tokens, extractor.consumed,
                           request.selected_code)
        timings['narrow'] = int((time.perf_counter() - t0) * 1000)

        name_confidence = self._final_confidence(index, name, narrowing)
        if name_confidence == 'low' and not any(r.usable for r in results):
            explained = set(name.token_indices)
            for r in results:
                if r.key is not None:  # подтверждение только характеристиками КТРУ
                    explained |= r.token_indices
            unexplained = [
                t for i, t in enumerate(match_tokens)
                if i not in explained and t.is_word and not t.is_stopword and len(t.norm) > 2
                and 'а' <= t.norm[0] <= 'я'
            ]
            if unexplained:
                # совпало лишь общее слово ("Отвертка" -> "Отвертка для лыжного спорта"),
                # а остальное описание справочником не подтверждается
                name.alternatives = [index.groups[g].name for g in name.groups][:5] + name.alternatives
                return self._name_not_found(text, normalized, match_tokens, index, name, issues,
                                            corrected_query, timings, started, partial=True)
        if narrowing.final_code and name_confidence != 'low':
            status = 'resolved'
        elif narrowing.final_code:
            status = 'low_confidence'
        else:
            status = 'need_more_info'

        used_keys = {r.key for r in results if r.key and r.usable}
        suggestions = [] if status == 'resolved' else suggest_characteristics(
            schema, narrowing.remaining, index, used_keys)
        refinements = [] if status == 'resolved' else name_refinements(index, narrowing.remaining)
        okpd_refinements = [] if status == 'resolved' or refinements else okpd2_refinements(index, narrowing.remaining)

        rows_out = self._rows(results, schema, index, narrowing, status)
        candidates = self._candidates(index, narrowing.remaining, results)
        final = None
        if narrowing.final_code:
            final = next((c for c in candidates if c.code == narrowing.final_code), None)

        messages = self._messages(status, narrowing, final, suggestions, refinements, okpd_refinements,
                                  results, issues, truncated, name_confidence, index)
        main = messages[0].text

        compat_codes = [narrowing.final_code] if status == 'resolved' else [c.code for c in candidates[:3]]
        positions = [
            PositionResponse.model_validate(p)
            for p in await PositionRepository.get_many_by_ids([c for c in compat_codes if c])
        ]

        product_names = [index.groups[g].name for g in name.groups]
        if narrowing.final_code:
            final_group = index.positions[narrowing.final_code].group
            product_names = [index.groups[final_group].name] + [
                n for n in product_names if n != index.groups[final_group].name]
        elif narrowing.remaining:
            counts = Counter(index.positions[p].group for p in narrowing.remaining)
            leading = [index.groups[g].name for g, _ in counts.most_common()]
            product_names = leading + [n for n in product_names if n not in leading]
        matched_text = ' '.join(tokens[i].text for i in sorted(name.token_indices))
        timings['total'] = int((time.perf_counter() - started) * 1000)
        return ParseResponse(
            status=status,
            message=main,
            query=text,
            corrected_query=corrected_query,
            product=ProductOut(name=product_names[0], names=product_names[:10],
                               confidence=name_confidence, matched_text=matched_text),
            ktru_code=narrowing.final_code if status == 'resolved' else None,
            ktru_name=index.positions[narrowing.final_code].name if status == 'resolved' else None,
            final_position=final if status == 'resolved' else None,
            characteristics=rows_out,
            stages=[StageOut(**s.__dict__) for s in narrowing.stages],
            candidates=candidates,
            candidates_total=len(narrowing.remaining),
            suggestions=[SuggestionOut(id=s.key, name=s.name, required=s.required, options=s.options,
                                       reason=s.reason) for s in suggestions],
            name_refinements=refinements,
            okpd2_refinements=okpd_refinements,
            name_alternatives=name.alternatives,
            spelling=[SpellingIssueOut(original=i.original, suggestion=i.suggestion, start=i.start, end=i.end)
                      for i in issues],
            unrecognized=[FragmentOut(**f) for f in extractor.unrecognized_fragments],
            messages=messages,
            quality=self._quality(results, rows_out, issues, extractor),
            positions=positions,
            timings_ms=timings,
        )

    # ------------------------------------------------------------------ parts
    @staticmethod
    def _final_confidence(index: KtruIndex, name, narrowing) -> str:
        """Уверенность в наименовании для группы, к которой пришло сужение."""
        groups = {index.positions[p].group for p in narrowing.remaining} if narrowing.remaining else set()
        if narrowing.final_code:
            groups = {index.positions[narrowing.final_code].group}
        scores = {s.group: s for s in name.scores}
        levels = []
        for g in groups or set(name.groups):
            gs = scores.get(g)
            if gs is None:
                continue
            filtered = any(st.kind == 'characteristic' and st.applied for st in narrowing.stages)
            if gs.complete and not gs.fuzzy:
                levels.append('high')
            elif gs.complete or gs.coverage >= 0.5 or (
                    gs.head_matched and (gs.evidence_score > 0 or filtered)):
                levels.append('medium')
            else:
                levels.append('low')
        if not levels:
            return name.confidence
        order = {'low': 0, 'medium': 1, 'high': 2}
        if narrowing.final_code:
            return min(levels, key=lambda lvl: order[lvl])
        return max(levels, key=lambda lvl: order[lvl])

    @staticmethod
    def _limit_ids(index: KtruIndex, groups: list[int]) -> list[str]:
        ids: list[str] = []
        seen: set[int] = set()
        for g in groups:
            if g in seen:
                continue
            seen.add(g)
            ids.extend(index.groups[g].position_ids)
        if len(ids) > MAX_DETAILED_POSITIONS:
            ids.sort(key=lambda p: (index.positions[p].is_template, p))
            ids = ids[:MAX_DETAILED_POSITIONS]
        return ids

    def _apply_user_input(self, results: list[Extracted], request: ParseRequest,
                          extractor: CharacteristicExtractor, schema: CandidateSchema,
                          index: KtruIndex) -> list[Extracted]:
        excluded = {normalize_phrase(n) for n in request.excluded}
        if excluded:
            results = [r for r in results
                       if normalize_phrase(r.key or r.name) not in excluded]
        for override in request.overrides:
            key = normalize_phrase(override.name)
            uc = schema.chars.get(key)
            if uc is None and schema.chars:
                names = {k: c.name for k, c in schema.chars.items()}
                match = process.extractOne(override.name, names, scorer=fuzz.WRatio,
                                           processor=normalize_phrase, score_cutoff=92)
                if match:
                    uc = schema.chars[match[2]]
            previous = next((r for r in results if r.key and uc and r.key == uc.key), None)
            if uc is not None:
                ex = parse_user_value(extractor, uc, override.value)
                if previous is not None:
                    ex.original = previous.original
                    ex.start, ex.end = previous.start, previous.end
                    ex.notes.insert(0, f'Изменено пользователем (в описании: «{previous.original}»).')
                    results = [r for r in results if r is not previous]
                else:
                    ex.notes.insert(0, 'Указано пользователем.')
                results.append(ex)
            else:
                stems = [t.stem for t in tokenize(normalize_text(override.name)) if t.is_word]
                _, entry, source = index.find_phrase(stems)
                ex = Extracted(key=None, name=entry.name if entry else override.name, source='user',
                               original=override.value, value_text=override.value,
                               normalized=override.value, value_kind='none')
                if source == 'ste':
                    ex.status = STATUS_STE
                    ex.notes.append('Характеристика есть только в выгрузке портала поставщиков — '
                                    'на выбор кода КТРУ не влияет.')
                elif source == 'ktru':
                    ex.status = STATUS_OTHER_KTRU
                    ex.notes.append('Характеристика есть в КТРУ, но не у позиций с этим наименованием.')
                else:
                    ex.status = STATUS_UNRECOGNIZED
                    ex.notes.append(f'Характеристика «{override.name}» не распознана: её нет ни в справочнике '
                                    'КТРУ, ни в выгрузке портала поставщиков.')
                results = [r for r in results if normalize_phrase(r.name) != normalize_phrase(ex.name)]
                results.append(ex)
        return results

    def _rows(self, results: list[Extracted], schema: CandidateSchema, index: KtruIndex,
              narrowing, status: str) -> list[CharacteristicRow]:
        rows: list[CharacteristicRow] = []
        seen: set[str] = set()
        remaining = set(narrowing.remaining)
        final = narrowing.final_code if status in ('resolved', 'low_confidence') else None
        scope = {final} if final else remaining
        for r in sorted(results, key=lambda r: (r.source == 'user', r.start if r.start is not None else 10**9)):
            uc = schema.chars.get(r.key) if r.key else None
            row_id = r.key or f'{r.source}:{normalize_phrase(r.name)}:{r.start}'
            if row_id in seen:
                row_id = f'{row_id}:{len(rows)}'
            seen.add(row_id)
            pc = uc.by_position.get(final) if (uc and final) else None
            rows.append(CharacteristicRow(
                id=row_id,
                name=r.name,
                source=r.source if r.source in ('text', 'user', 'ste', 'unknown') else 'text',
                original=r.original,
                normalized=r.normalized,
                unit=r.unit_display or '',
                status=r.status,
                required=bool(pc.required) if pc else (uc.required if uc else False),
                char_type=_char_type(uc),
                matched_range=r.matched_option if r.value_kind in ('number', 'interval') else None,
                notes=r.notes,
                suggestions=r.suggestions,
                options=uc.option_labels(scope) if uc else [],
                alternatives=r.alternatives,
                confidence=round(r.confidence, 2),
                start=r.start,
                end=r.end,
                in_specification=r.usable and r.status in (STATUS_OK, STATUS_NO_CONSTRAINTS) and (
                    final is None or not pc or final in r.accepted_positions),
            ))
        mentioned = {r.key for r in results if r.key}
        # характеристики, которые ещё нужно заполнить
        if final:
            for key, pc in schema.position_chars.get(final, {}).items():
                if key in mentioned:
                    continue
                uc = schema.chars[key]
                rows.append(self._missing_row(uc, pc.required, {final}))
        elif remaining:
            concrete = [p for p in remaining if not index.positions[p].is_template] or list(remaining)
            for key, uc in schema.chars.items():
                if key in mentioned:
                    continue
                if all(p in uc.by_position for p in concrete) and all(
                        uc.by_position[p].required for p in concrete):
                    rows.append(self._missing_row(uc, True, set(concrete)))
        return rows

    @staticmethod
    def _missing_row(uc, required: bool, scope: set[str]) -> CharacteristicRow:
        options = uc.option_labels(scope)
        notes = ['Обязательная характеристика КТРУ — укажите значение.' if required
                 else 'Необязательная характеристика КТРУ.']
        return CharacteristicRow(
            id=uc.key, name=uc.name, source='reference', status=STATUS_MISSING, required=required,
            char_type=_char_type(uc), unit=uc.unit_symbol() or '', notes=notes, options=options,
            confidence=0.0,
        )

    @staticmethod
    def _candidates(index: KtruIndex, remaining: list[str], results: list[Extracted]) -> list[CandidateOut]:
        def matched(pid: str) -> int:
            return sum(1 for r in results if r.usable and pid in r.accepted_positions)

        ordered = sorted(remaining, key=lambda p: (index.positions[p].is_template, -matched(p), p))
        out = []
        for pid in ordered[:MAX_CANDIDATES_IN_RESPONSE]:
            info = index.positions[pid]
            out.append(CandidateOut(
                code=pid, name=info.name, okpd2_code=info.okpd2_code, okpd2_name=info.okpd2_name,
                is_template=info.is_template, matched=matched(pid), validity_note=validity_note(index, pid),
            ))
        return out

    @staticmethod
    def _messages(status, narrowing, final, suggestions, refinements, okpd_refinements, results,
                  issues, truncated, name_confidence, index) -> list[Message]:
        messages: list[Message] = []
        if status == 'resolved':
            messages.append(Message(level='success', code='resolved', text=(
                f'Код КТРУ определён однозначно: {narrowing.final_code}. '
                'Информации в описании достаточно.')))
        elif status == 'low_confidence':
            messages.append(Message(level='warning', code='low_confidence', text=(
                'Наименование товара распознано неуверенно — код КТРУ не может быть определён '
                'с уверенностью. Проверьте наименование товара.')))
        else:
            if refinements:
                text = (f'Описание подходит к нескольким наименованиям КТРУ ({len(refinements)}). '
                        'Уточните наименование товара: '
                        + '; '.join(r['name'] for r in refinements[:4]) + '.')
                if suggestions:
                    text += ' Или укажите: ' + ', '.join(s.name for s in suggestions[:3]) + '.'
            elif suggestions:
                names = ', '.join(s.name for s in suggestions[:4])
                text = ('Описание не содержит достаточно информации для однозначного определения кода КТРУ. '
                        f'Попробуйте указать: {names}.')
            elif okpd_refinements:
                text = ('Позиции различаются только группировкой ОКПД2. Уточните вид товара: '
                        + '; '.join(r['name'] for r in okpd_refinements[:3]) + '.')
            else:
                text = ('Код КТРУ не может быть определён с уверенностью: оставшиеся позиции не различаются '
                        'характеристиками справочника. Выберите позицию из списка кандидатов.')
            messages.append(Message(level='warning', code='need_more_info', text=text))

        for r in results:
            if r.status == STATUS_UNRECOGNIZED:
                messages.append(Message(level='warning', code='unrecognized_characteristic', text=r.notes[-1]))
            elif r.status in (STATUS_INVALID, STATUS_UNIT_MISMATCH):
                value = r.normalized + (f' {r.unit_display}' if r.unit_display else '')
                messages.append(Message(level='error', code='invalid_value', text=(
                    f'«{r.name}»: значение «{value.strip()}» не допускается справочником КТРУ'
                    + (f'. Допустимо: {"; ".join(r.suggestions[:5])}' if r.suggestions else '') + '.')))
            elif r.status == STATUS_CONFLICT:
                messages.append(Message(level='warning', code='conflict', text=f'«{r.name}»: ' + r.notes[-1]))
            elif r.status == STATUS_AMBIGUOUS:
                messages.append(Message(level='warning', code='ambiguous_value', text=r.notes[-1]))
            elif r.status == STATUS_NO_VALUE:
                messages.append(Message(level='info', code='no_value', text=f'«{r.name}»: значение не указано.'))
        if issues:
            messages.append(Message(level='info', code='typos', text=(
                'Найдены возможные опечатки: ' + ', '.join(f'«{i.original}» → «{i.suggestion}»' for i in issues[:5])
                + '.')))
        if narrowing.final_code:
            note = validity_note(index, narrowing.final_code)
            if note:
                messages.append(Message(level='info', code='validity', text=note))
        if truncated:
            messages.append(Message(level='info', code='truncated', text=(
                f'Наименованию соответствует более {MAX_DETAILED_POSITIONS} позиций; характеристики '
                'проверены для первых из них. Уточните наименование.')))
        if name_confidence == 'low' and status != 'low_confidence':
            messages.append(Message(level='warning', code='name_low_confidence', text=(
                'Наименование товара совпало со справочником лишь частично.')))
        return messages

    @staticmethod
    def _quality(results: list[Extracted], rows: list[CharacteristicRow], issues, extractor) -> dict[str, int]:
        required = [r for r in rows if r.required]
        return {
            'recognized': sum(1 for r in results if r.usable),
            'errors': sum(1 for r in results if r.status in ERROR_STATUSES),
            'typos': len(issues),
            'unrecognized': sum(1 for r in results if r.status == STATUS_UNRECOGNIZED),
            'ambiguous': sum(1 for r in results if r.status == STATUS_AMBIGUOUS),
            'required_total': len(required),
            'required_filled': sum(1 for r in required if r.in_specification),
            'unrecognized_fragments': len(extractor.unrecognized_fragments),
        }

    def _name_not_found(self, text, normalized, tokens, index, name, issues, corrected_query,
                        timings, started, partial: bool = False) -> ParseResponse:
        extractor = CharacteristicExtractor(normalized, tokens, CandidateSchema([]), index, set(), set())
        results = extractor.extract()
        rows = self._rows(results, extractor.schema, index,
                          Narrowing(stages=[], remaining=[], final_code=None), 'name_not_found')
        messages = [Message(level='error', code='name_not_found', text=(
            'Не удалось сопоставить описание с наименованием товара из справочника КТРУ. '
            'Измените наименование товара.'))]
        if partial and name.alternatives:
            messages.append(Message(level='info', code='similar_names', text=(
                'В справочнике есть только похожие наименования: '
                + '; '.join(f'«{n}»' for n in name.alternatives[:3]) + '.')))
        for r in results:
            if r.status == STATUS_UNRECOGNIZED:
                messages.append(Message(level='warning', code='unrecognized_characteristic', text=r.notes[-1]))
        if issues:
            messages.append(Message(level='info', code='typos', text=(
                'Найдены возможные опечатки: ' + ', '.join(f'«{i.original}» → «{i.suggestion}»' for i in issues[:5])
                + '.')))
        timings['total'] = int((time.perf_counter() - started) * 1000)
        return ParseResponse(
            status='name_not_found',
            message=messages[0].text,
            query=text,
            corrected_query=corrected_query,
            characteristics=rows,
            stages=[
                StageOut(title='Справочник КТРУ', detail='актуальные позиции (статус ACTIVE)',
                         count_before=None, count_after=len(index.positions), applied=True, kind='catalog'),
                StageOut(title='Наименование товара',
                         detail='совпадает лишь частично' if partial else 'не найдено в справочнике',
                         count_before=len(index.positions), count_after=0, applied=True, kind='name'),
            ],
            name_alternatives=name.alternatives,
            spelling=[SpellingIssueOut(original=i.original, suggestion=i.suggestion, start=i.start, end=i.end)
                      for i in issues],
            unrecognized=[FragmentOut(**f) for f in extractor.unrecognized_fragments],
            messages=messages,
            quality=self._quality(results, rows, issues, extractor),
            timings_ms=timings,
        )


_service = ProductParsingService(llm_client=None, ner_model=None)


def get_parsing_service() -> ProductParsingService:
    return _service
