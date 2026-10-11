'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { AnalyzeForm } from '@/features/analyze-text/ui/analyze-form';
import { CharacteristicModal } from '@/features/update-characteristic/ui/CharacteristicModal';
import { TextCorrectionToaster } from '@/features/suggest-text-correction/ui/TextCorrectionToaster';
import type { Characteristic } from '@/entities/characteristic/ui/characteristic-row';
import { useAnalysisStore } from '@/entities/product/model/use-analysis-store';
import type { CharacteristicRowDto, ParseResponse } from '@/entities/product/model/types';
import { useAnalyzeStore } from '@/shared/model/use-analyze-store';
import { KtruTableWidget } from '@/widgets/ktru-analysis/ui/ktru-table-widget';
import { QualityCheckCard } from '@/widgets/ktru-analysis/ui/quality-check-card';
import { KtruSelectionCard } from '@/widgets/ktru-analysis/ui/ktru-selection-card';
import type { TextHighlight } from '@/widgets/ktru-analysis/ui/highlighted-text';

interface ModalState {
  title: string;
  description: string;
  characteristicName?: string;
  characteristicNames?: string[];
  options: string[];
  unit?: string;
  initialValue: string;
}

interface Props {
  onUploadFiles?: (files: File[]) => Promise<void> | void;
  formTitle?: string;
}

function toCharacteristic(row: CharacteristicRowDto): Characteristic {
  return {
    id: row.id,
    name: row.name,
    description: row.original,
    normalized: row.normalized,
    unit: row.unit,
    confidence: row.status === 'missing' ? '' : `${Math.round(row.confidence * 100)}%`,
    isRequired: row.required,
    status: row.status,
    source: row.source,
    matchedRange: row.matched_range,
    notes: row.notes,
    suggestions: row.status === 'invalid' || row.status === 'unit_mismatch' || row.status === 'no_value' ? row.suggestions : [],
    options: row.options,
    inSpecification: row.in_specification,
  };
}

function buildHighlights(result: ParseResponse | null): TextHighlight[] {
  if (!result) return [];
  const highlights: TextHighlight[] = [];
  for (const row of result.characteristics) {
    if (row.start === null || row.end === null || row.source === 'reference') continue;
    const bad = row.status === 'unrecognized' || row.status === 'invalid' || row.status === 'unit_mismatch';
    highlights.push({ start: row.start, end: row.end, kind: bad ? 'unrecognized' : 'characteristic', title: `${row.name}: ${row.normalized}` });
  }
  for (const f of result.unrecognized) {
    highlights.push({ start: f.start, end: f.end, kind: 'unrecognized', title: 'Не распознано' });
  }
  if (result.product?.matched_text) {
    const at = result.query.toLowerCase().indexOf(result.product.matched_text.toLowerCase());
    if (at >= 0) {
      highlights.push({ start: at, end: at + result.product.matched_text.length, kind: 'name', title: `Наименование: ${result.product.name}` });
    }
  }
  for (const s of result.spelling) {
    highlights.push({ start: s.start, end: s.end, kind: 'typo', title: `Возможно: ${s.suggestion}` });
  }
  return highlights;
}

const CONFIDENCE_LABEL: Record<string, string> = { high: 'высокая', medium: 'средняя', low: 'низкая' };

export const AnalysisWorkspace: React.FC<Props> = ({ onUploadFiles, formTitle }) => {
  const { text, setText } = useAnalyzeStore();
  const {
    result, isLoading, error, analyzedText, selectedCode,
    analyze, refresh, setOverride, removeCharacteristic, selectCandidate,
  } = useAnalysisStore();
  const [modal, setModal] = useState<ModalState | null>(null);
  const [suggest, setSuggest] = useState('');

  // предложение исправить опечатки показываем для каждого нового результата
  useEffect(() => {
    setSuggest(result?.corrected_query && result.corrected_query !== result.query ? result.corrected_query : '');
  }, [result]);

  const items = useMemo(() => (result?.characteristics ?? []).map(toCharacteristic), [result]);
  const highlights = useMemo(() => buildHighlights(result), [result]);
  const rowById = (id: string) => result?.characteristics.find((r) => r.id === id);

  const handleEdit = (id: string) => {
    const row = rowById(id);
    if (!row) return;
    if (row.status === 'ambiguous') {
      setModal({
        title: 'К какой характеристике относится значение?',
        description: `В описании указано «${row.original}». Выберите характеристику КТРУ.`,
        characteristicNames: row.alternatives,
        options: [],
        initialValue: row.original,
      });
      return;
    }
    setModal({
      title: row.status === 'missing' ? 'Укажите характеристику' : 'Изменить значение',
      description: row.options.length
        ? 'Выберите значение из справочника КТРУ или введите своё — оно будет проверено.'
        : 'Введите значение — оно будет проверено по справочнику КТРУ.',
      characteristicName: row.name,
      options: row.options,
      unit: row.unit || undefined,
      initialValue: row.status === 'missing' || row.status === 'no_value' ? '' : row.normalized,
    });
  };

  const handleAdd = () => {
    const names = new Set<string>();
    result?.suggestions.forEach((s) => names.add(s.name));
    result?.characteristics.filter((r) => r.source === 'reference').forEach((r) => names.add(r.name));
    setModal({
      title: 'Добавить характеристику',
      description: 'Название и значение будут сопоставлены со справочником КТРУ и выгрузкой СТЕ.',
      characteristicNames: [...names],
      options: [],
      initialValue: '',
    });
  };

  const handleUseName = (name: string) => {
    const base = analyzedText || text;
    const matched = result?.product?.matched_text ?? '';
    let next = `${name}, ${base}`;
    if (matched) {
      const at = base.toLowerCase().indexOf(matched.toLowerCase());
      if (at >= 0) next = base.slice(0, at) + name + base.slice(at + matched.length);
    } else if (result?.status === 'name_not_found') {
      next = name;
    }
    setText(next);
    void analyze(next);
  };

  const modalOptions = modal?.characteristicName
    ? modal.options
    : [];

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Левая колонка: Форма ввода + Блок КТРУ */}
        <div className="lg:col-span-5 space-y-5">
          <AnalyzeForm
            sendProductString={(value) => void analyze(value)}
            isLoading={isLoading}
            onUploadFiles={onUploadFiles}
            title={formTitle}
          />

          {/* Блок проверки качества и КТРУ */}
          <div className="space-y-6">
            <QualityCheckCard result={result} isLoading={isLoading} />
            <KtruSelectionCard
              result={result}
              isLoading={isLoading}
              error={error}
              selectedCode={selectedCode}
              onSpecify={(s) =>
                setModal({
                  title: 'Уточните характеристику',
                  description: `${s.reason[0].toUpperCase()}${s.reason.slice(1)}. Значение сузит список позиций КТРУ.`,
                  characteristicName: s.name,
                  options: s.options.map((o) => o.value),
                  initialValue: '',
                })
              }
              onSelectCandidate={(code) => void selectCandidate(code)}
              onUseName={handleUseName}
            />
          </div>
        </div>

        {/* Правая колонка: Таблица итоговых характеристик */}
        <div className="lg:col-span-7">
          <div className="mb-5">
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100">Итоговые Характеристики</h2>
            {result?.product ? (
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Наименование КТРУ: <span className="font-semibold text-slate-700 dark:text-slate-200">{result.product.name}</span>
                {' '}· уверенность {CONFIDENCE_LABEL[result.product.confidence] ?? result.product.confidence}
                {result.ktru_code ? <> · код <span className="font-semibold text-slate-700 dark:text-slate-200">{result.ktru_code}</span></> : null}
              </p>
            ) : null}
          </div>
          <KtruTableWidget
            items={items}
            text={result?.query ?? (text || undefined)}
            highlights={highlights}
            isLoading={isLoading}
            onEdit={result ? handleEdit : undefined}
            onDelete={result ? (id) => {
              const row = rowById(id);
              if (row) void removeCharacteristic(row.name);
            } : undefined}
            onApplySuggestion={(id, value) => {
              const row = rowById(id);
              if (row) void setOverride(row.name, value);
            }}
            onAdd={result && result.status !== 'name_not_found' ? handleAdd : undefined}
            onRefresh={analyzedText ? () => void refresh() : undefined}
          />
        </div>
      </div>

      {/* {Модалка} */}
      {modal ? (
        <CharacteristicModal
          isOpen
          title={modal.title}
          description={modal.description}
          characteristicName={modal.characteristicName}
          characteristicNames={modal.characteristicNames}
          options={modalOptions}
          unit={modal.unit}
          initialValue={modal.initialValue}
          onSubmit={(value, name) => void setOverride(name, value)}
          onClose={() => setModal(null)}
        />
      ) : null}

      {suggest !== '' ? (
        <TextCorrectionToaster replacetext={suggest} setSuggest={setSuggest} onApply={(fixed) => void analyze(fixed)} />
      ) : null}
    </>
  );
};
