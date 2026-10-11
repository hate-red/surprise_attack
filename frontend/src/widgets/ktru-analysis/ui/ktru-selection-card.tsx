import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, Info, CircleX, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from '@/shared/ui/card/card';
import { Badge } from '@/shared/ui/badge/badge';
import type { MessageDto, ParseResponse, SuggestionDto } from '@/entities/product/model/types';

interface Props {
  result: ParseResponse | null;
  isLoading?: boolean;
  error?: string | null;
  onSpecify?: (suggestion: SuggestionDto) => void;
  onSelectCandidate?: (code: string | null) => void;
  onUseName?: (name: string) => void;
  selectedCode?: string | null;
}

const STATUS_BADGE: Record<ParseResponse['status'], { label: string; variant: 'success' | 'warning' | 'info' | 'dark' }> = {
  resolved: { label: 'КОД ОПРЕДЕЛЁН', variant: 'success' },
  need_more_info: { label: 'НУЖНЫ УТОЧНЕНИЯ', variant: 'warning' },
  low_confidence: { label: 'НЕУВЕРЕННО', variant: 'warning' },
  name_not_found: { label: 'НАИМЕНОВАНИЕ НЕ НАЙДЕНО', variant: 'dark' },
};

const MESSAGE_STYLE: Record<MessageDto['level'], { icon: React.ReactNode; className: string }> = {
  success: { icon: <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5 text-emerald-500" />, className: 'text-emerald-800 dark:text-emerald-300' },
  info: { icon: <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-blue-500" />, className: 'text-slate-600 dark:text-slate-300' },
  warning: { icon: <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-500" />, className: 'text-amber-800 dark:text-amber-300' },
  error: { icon: <CircleX className="w-3.5 h-3.5 shrink-0 mt-0.5 text-red-500" />, className: 'text-red-700 dark:text-red-400' },
};

export const KtruSelectionCard: React.FC<Props> = ({
  result,
  isLoading,
  error,
  onSpecify,
  onSelectCandidate,
  onUseName,
  selectedCode,
}) => {
  const [showAll, setShowAll] = useState(false);
  const badge = isLoading
    ? { label: 'АНАЛИЗ…', variant: 'info' as const }
    : result
      ? STATUS_BADGE[result.status]
      : { label: 'ОЖИДАНИЕ', variant: 'info' as const };

  const mainMessage = result?.messages[0];
  const otherMessages = result?.messages.slice(1) ?? [];
  const resolved = result?.status === 'resolved' && result.final_position;
  const candidates = result?.candidates ?? [];
  const visibleCandidates = showAll ? candidates : candidates.slice(0, 5);

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <span className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Подбор КТРУ</span>
        <Badge variant={badge.variant}>{badge.label}</Badge>
      </div>

      {error ? (
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200/60 dark:border-red-900/50 rounded-lg p-3.5 mb-4 flex items-start space-x-3">
          <CircleX className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-[11px] text-red-800 dark:text-red-300 leading-relaxed">{error}</p>
        </div>
      ) : null}

      {!result && !isLoading && !error ? (
        <p className="text-xs text-slate-400 dark:text-slate-500">
          Введите описание товара — система найдёт наименование в справочнике КТРУ и поэтапно сузит список позиций.
        </p>
      ) : null}

      {/* Этапы сужения — реальные операции и количество позиций после каждой */}
      {result ? (
        <ol className={`grid grid-cols-2 sm:grid-cols-3 gap-2 mb-4 ${isLoading ? 'opacity-50' : ''}`}>
          {result.stages.map((stage, index) => (
            <li
              key={`${stage.title}-${index}`}
              title={stage.note ?? undefined}
              className={`bg-slate-50 dark:bg-slate-900/60 p-3 rounded-lg border border-slate-100 dark:border-slate-800 ${
                stage.applied ? '' : 'opacity-60'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className={`w-5 h-5 ${stage.applied ? 'bg-red-600' : 'bg-slate-400'} text-white rounded-full flex items-center justify-center text-xs font-bold`}>
                  {index + 1}
                </div>
                <span className="text-xs font-bold text-slate-800 dark:text-slate-100">
                  {stage.count_before !== null && stage.count_before !== stage.count_after ? (
                    <span className="font-normal text-slate-400 dark:text-slate-500">{stage.count_before} → </span>
                  ) : null}
                  {stage.count_after}
                </span>
              </div>
              <div className="text-[11px] text-slate-700 dark:text-slate-300 font-medium leading-snug break-words">{stage.title}</div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 leading-snug break-words line-clamp-3">
                {stage.detail}
              </div>
              {!stage.applied && stage.note ? (
                <div className="text-[10px] text-amber-700 dark:text-amber-400 leading-snug mt-0.5">{stage.note}</div>
              ) : null}
            </li>
          ))}
        </ol>
      ) : null}

      {/* Главное уведомление и что уточнить */}
      {result && mainMessage ? (
        <div
          className={`rounded-lg p-3.5 mb-4 flex items-start space-x-3 border ${
            result.status === 'resolved'
              ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200/60 dark:border-emerald-900/50'
              : result.status === 'name_not_found'
                ? 'bg-red-50 dark:bg-red-950/30 border-red-200/60 dark:border-red-900/50'
                : 'bg-amber-50 dark:bg-amber-950/30 border-amber-200/60 dark:border-amber-900/50'
          }`}
        >
          {result.status === 'resolved' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
          ) : result.status === 'name_not_found' ? (
            <CircleX className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          )}
          <div className="min-w-0">
            <p className="text-[11px] text-slate-800 dark:text-slate-200 leading-relaxed mb-2">{mainMessage.text}</p>
            {result.suggestions.length > 0 && onSpecify ? (
              <div className="flex flex-col items-start gap-1">
                {result.suggestions.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => onSpecify(s)}
                    className="text-xs font-semibold text-amber-900 dark:text-amber-400 hover:underline cursor-pointer text-left"
                  >
                    Указать: {s.name}{s.required ? ' *' : ''} →
                  </button>
                ))}
              </div>
            ) : null}
            {result.name_refinements.length > 0 && onUseName ? (
              <div className="mt-2 flex flex-wrap gap-1">
                {result.name_refinements.map((r) => (
                  <button
                    key={r.name}
                    type="button"
                    onClick={() => onUseName(r.name)}
                    className="rounded-md border border-amber-300/70 dark:border-amber-800 px-2 py-0.5 text-[10px] text-amber-900 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/40 cursor-pointer"
                    title="Подставить наименование в описание"
                  >
                    {r.name} ({r.count})
                  </button>
                ))}
              </div>
            ) : null}
            {result.status === 'name_not_found' && result.name_alternatives.length > 0 && onUseName ? (
              <div className="mt-2">
                <div className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Похожие наименования КТРУ</div>
                <div className="flex flex-wrap gap-1">
                  {result.name_alternatives.map((name) => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => onUseName(name)}
                      className="rounded-md border border-slate-300 dark:border-slate-700 px-2 py-0.5 text-[10px] text-slate-700 dark:text-slate-300 hover:border-red-400 cursor-pointer"
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {/* Итоговый код или честное сообщение, что код не определён */}
      {result && resolved && result.final_position ? (
        <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-4 bg-white dark:bg-slate-900/50 mb-3">
          <span className="text-[10px] uppercase font-bold tracking-wider text-red-600 dark:text-red-500 block mb-1">Итоговый код КТРУ</span>
          <div className="font-bold text-slate-900 dark:text-slate-100 text-sm mb-1">{result.final_position.code}</div>
          <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">{result.final_position.name}</p>
          {result.final_position.okpd2_name ? (
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mb-3">ОКПД2 {result.final_position.okpd2_code}: {result.final_position.okpd2_name}</p>
          ) : null}
          <div className="flex justify-between items-center text-[11px] pt-2 border-t border-slate-100 dark:border-slate-800">
            <span className="text-slate-400 dark:text-slate-500">Подтверждено характеристиками</span>
            <span className="font-bold text-emerald-600 dark:text-emerald-400">{result.final_position.matched}</span>
          </div>
          {selectedCode && onSelectCandidate ? (
            <button type="button" onClick={() => onSelectCandidate(null)} className="mt-2 text-[11px] text-slate-500 hover:text-red-600 hover:underline cursor-pointer">
              Отменить ручной выбор позиции
            </button>
          ) : null}
        </div>
      ) : null}

      {result && !resolved && candidates.length > 0 ? (
        <div className="border border-slate-200 dark:border-slate-800 rounded-lg bg-white dark:bg-slate-900/50 mb-3">
          <div className="px-4 pt-3 pb-2 flex justify-between items-baseline">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 dark:text-slate-400">
              Код не определён · кандидаты
            </span>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">осталось {result.candidates_total}</span>
          </div>
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {visibleCandidates.map((c) => (
              <li key={c.code} className="px-4 py-2 flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                    {c.code}
                    {c.is_template ? <span className="ml-1.5 text-[10px] font-normal text-slate-400">шаблон</span> : null}
                  </div>
                  <div className="text-[11px] text-slate-600 dark:text-slate-400 truncate" title={c.name}>{c.name}</div>
                  {c.validity_note ? <div className="text-[10px] text-slate-400">{c.validity_note}</div> : null}
                </div>
                {onSelectCandidate ? (
                  <button
                    type="button"
                    onClick={() => onSelectCandidate(c.code)}
                    className="shrink-0 text-[11px] font-semibold text-red-600 dark:text-red-400 hover:underline cursor-pointer"
                    title="Выбрать эту позицию вручную"
                  >
                    Выбрать
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
          {candidates.length > 5 ? (
            <button
              type="button"
              onClick={() => setShowAll((v) => !v)}
              className="w-full px-4 py-2 text-[11px] text-slate-500 dark:text-slate-400 hover:text-red-600 flex items-center justify-center gap-1 cursor-pointer border-t border-slate-100 dark:border-slate-800"
            >
              {showAll ? <>Свернуть <ChevronUp className="w-3 h-3" /></> : <>Показать все ({candidates.length}{result.candidates_total > candidates.length ? ` из ${result.candidates_total}` : ''}) <ChevronDown className="w-3 h-3" /></>}
            </button>
          ) : null}
        </div>
      ) : null}

      {otherMessages.length > 0 ? (
        <ul className="space-y-1.5">
          {otherMessages.map((m, i) => (
            <li key={`${m.code}-${i}`} className={`flex items-start gap-2 text-[11px] leading-relaxed ${MESSAGE_STYLE[m.level].className}`}>
              {MESSAGE_STYLE[m.level].icon}
              <span>{m.text}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </Card>
  );
};
