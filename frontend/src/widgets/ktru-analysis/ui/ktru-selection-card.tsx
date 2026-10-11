
import { forwardRef, useState, type ReactNode } from 'react';
import {
  AlertTriangle,
  CircleCheck,
  ChevronDown,
  ChevronUp,
  CircleX,
  Info,
} from 'lucide-react';
import { Card } from '@/shared/ui/card/card';
import { Badge } from '@/shared/ui/badge/badge';
import type {
  MessageDto,
  ParseResponse,
  SuggestionDto,
} from '@/entities/product/model/types';
import { KtruFunnel } from '@/widgets/analysis-workspace/ui/ktru-funnel';

interface Props {
  result: ParseResponse | null;
  isLoading?: boolean;
  error?: string | null;
  onSpecify?: (suggestion: SuggestionDto) => void;
  onSelectCandidate?: (code: string | null) => void;
  onUseName?: (name: string) => void;
  selectedCode?: string | null;
}

const STATUS_BADGE: Record<
  ParseResponse['status'],
  {
    label: string;
    variant: 'success' | 'warning' | 'info' | 'dark';
  }
> = {
  resolved: {
    label: 'КОД ОПРЕДЕЛЁН',
    variant: 'success',
  },
  need_more_info: {
    label: 'НУЖНЫ УТОЧНЕНИЯ',
    variant: 'warning',
  },
  low_confidence: {
    label: 'ПРОВЕРЬТЕ НАИМЕНОВАНИЕ',
    variant: 'warning',
  },
  name_not_found: {
    label: 'НАИМЕНОВАНИЕ НЕ НАЙДЕНО',
    variant: 'dark',
  },
};

// Сообщения, относящиеся к списку позиций КТРУ.
const CARD_MESSAGES = new Set([
  'validity',
  'truncated',
  'name_low_confidence',
]);

const VISIBLE = 5;

const MESSAGE_STYLE: Record<
  MessageDto['level'],
  {
    icon: ReactNode;
    className: string;
  }
> = {
  success: {
    icon: (
      <CircleCheck className="w-3.5 h-3.5 shrink-0 mt-0.5 text-emerald-500" />
    ),
    className: 'text-emerald-800 dark:text-emerald-300',
  },
  info: {
    icon: (
      <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-blue-500" />
    ),
    className: 'text-slate-600 dark:text-slate-300',
  },
  warning: {
    icon: (
      <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-500" />
    ),
    className: 'text-amber-800 dark:text-amber-300',
  },
  error: {
    icon: (
      <CircleX className="w-3.5 h-3.5 shrink-0 mt-0.5 text-red-500" />
    ),
    className: 'text-red-700 dark:text-red-400',
  },
};

export const KtruSelectionCard = forwardRef<HTMLDivElement, Props>(
  function KtruSelectionCard(
    {
      result,
      isLoading,
      error,
      onSpecify,
      onSelectCandidate,
      onUseName,
      selectedCode,
    },
    ref,
  ) {
    const [showAll, setShowAll] = useState(false);

    const badge = isLoading
      ? { label: 'АНАЛИЗ…', variant: 'info' as const }
      : result
        ? STATUS_BADGE[result.status]
        : { label: 'ОЖИДАНИЕ', variant: 'info' as const };

    const messages = result?.messages ?? [];

    // Основное уведомление показывается после воронки и списка позиций.
    const mainMessage = messages.find(
      (message) => !CARD_MESSAGES.has(message.code),
    );

    // Служебные уведомления показываются рядом со списком позиций.
    const notes = messages.filter((message) =>
      CARD_MESSAGES.has(message.code),
    );

    // Остальные сообщения показываются в конце.
    const otherMessages = messages.filter(
      (message) =>
        !CARD_MESSAGES.has(message.code) &&
        message !== mainMessage,
    );

    const final =
      result?.status === 'resolved'
        ? result.final_position
        : null;

    const candidates = result?.candidates ?? [];

    const visible = showAll
      ? candidates
      : candidates.slice(0, VISIBLE);

    const alternatives =
      result?.status === 'name_not_found'
        ? result.name_alternatives
        : [];

    return (
      <div ref={ref}>
        <Card>
          {/* Заголовок */}
          <div className="flex justify-between items-center mb-4">
            <span className="font-semibold text-slate-800 dark:text-slate-200 text-sm">
              Подбор КТРУ
            </span>

            <Badge variant={badge.variant}>
              {badge.label}
            </Badge>
          </div>

          {/* Ошибка запроса */}
          {error ? (
            <div className="bg-red-50 dark:bg-red-950/30 border border-red-200/60 dark:border-red-900/50 rounded-lg p-3.5 mb-4 flex items-start space-x-3">
              <CircleX className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />

              <p className="text-xs text-red-800 dark:text-red-300 leading-relaxed">
                {error}
              </p>
            </div>
          ) : null}

          {/* Начальное состояние */}
          {!result && !isLoading && !error ? (
            <p className="text-xs text-slate-400 dark:text-slate-500">
              Введите описание товара — система найдёт наименование
              в справочнике КТРУ и поэтапно сузит список позиций.
            </p>
          ) : null}

          {result ? (
            <div
              className={
                isLoading
                  ? 'opacity-50 transition-opacity'
                  : ''
              }
            >
              {/* 1. Воронка и список кодов КТРУ */}
              <div className="grid grid-cols-[minmax(0,8.5rem)_minmax(0,1fr)] gap-4">
                {/* Воронка слева */}
                <KtruFunnel
                  stages={result.stages}
                  resolved={Boolean(final)}
                />

                {/* Коды и наименования справа */}
                <div className="min-w-0">
                  {/* Итоговая позиция, если код определён */}
                  {final ? (
                    <div className="rounded-lg border-2 border-emerald-500/70 bg-emerald-50/40 dark:bg-emerald-950/20 p-3.5">
                      <span className="flex items-center gap-1 text-[10px] uppercase font-bold tracking-wider text-emerald-700 dark:text-emerald-400 mb-1">
                        <CircleCheck className="w-3.5 h-3.5" />
                        Итоговый код КТРУ
                      </span>

                      <div className="font-bold text-slate-900 dark:text-slate-100 text-base tabular-nums">
                        {final.code}
                      </div>

                      <p className="text-xs text-slate-700 dark:text-slate-300 mt-0.5">
                        {final.name}
                      </p>

                      {final.okpd2_name ? (
                        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                          ОКПД2 {final.okpd2_code}: {final.okpd2_name}
                        </p>
                      ) : null}

                      <div className="flex justify-between items-center text-[11px] mt-2 pt-2 border-t border-emerald-200/70 dark:border-emerald-900/50">
                        <span className="text-slate-500 dark:text-slate-400">
                          Подтверждено характеристиками
                        </span>

                        <span className="font-bold text-emerald-700 dark:text-emerald-400">
                          {final.matched}
                        </span>
                      </div>

                      {selectedCode && onSelectCandidate ? (
                        <button
                          type="button"
                          onClick={() => onSelectCandidate(null)}
                          className="mt-2 text-[11px] text-slate-500 hover:text-red-600 hover:underline cursor-pointer"
                        >
                          Отменить ручной выбор позиции
                        </button>
                      ) : null}
                    </div>
                  ) : (
                    <>
                      {/* Список возможных позиций КТРУ */}
                      {candidates.length > 0 ? (
                        <div>
                          <div className="flex justify-between items-baseline mb-1.5">
                            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 dark:text-slate-400">
                              Возможные коды КТРУ
                            </span>

                            <span className="text-[11px] text-slate-500 dark:text-slate-400">
                              осталось {result.candidates_total}
                            </span>
                          </div>

                          <ul className="divide-y divide-slate-100 dark:divide-slate-800 rounded-lg border border-slate-200 dark:border-slate-800">
                            {visible.map((candidate) => (
                              <li
                                key={candidate.code}
                                className="px-3 py-2 flex items-start justify-between gap-2 hover:bg-slate-50 dark:hover:bg-slate-800/40"
                              >
                                <div className="min-w-0">
                                  <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 tabular-nums">
                                    {candidate.code}

                                    {candidate.is_template ? (
                                      <span className="ml-1.5 text-[10px] font-normal text-slate-400">
                                        шаблон
                                      </span>
                                    ) : null}
                                  </div>

                                  <div
                                    className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2"
                                    title={candidate.name}
                                  >
                                    {candidate.name}
                                  </div>

                                  {candidate.validity_note ? (
                                    <div className="text-[10px] text-slate-400">
                                      {candidate.validity_note}
                                    </div>
                                  ) : null}
                                </div>

                                {onSelectCandidate ? (
                                  <button
                                    type="button"
                                    onClick={() =>
                                      onSelectCandidate(candidate.code)
                                    }
                                    className="shrink-0 text-[11px] font-semibold text-red-600 dark:text-red-400 hover:underline cursor-pointer"
                                    title="Выбрать эту позицию вручную"
                                  >
                                    Выбрать
                                  </button>
                                ) : null}
                              </li>
                            ))}
                          </ul>

                          {/* Разворачивание списка */}
                          {candidates.length > VISIBLE ? (
                            <button
                              type="button"
                              onClick={() =>
                                setShowAll((value) => !value)
                              }
                              className="w-full pt-2 text-[11px] text-slate-500 dark:text-slate-400 hover:text-red-600 flex items-center justify-center gap-1 cursor-pointer"
                            >
                              {showAll ? (
                                <>
                                  Свернуть
                                  <ChevronUp className="w-3 h-3" />
                                </>
                              ) : (
                                <>
                                  Показать все ({candidates.length}
                                  {result.candidates_total > candidates.length
                                    ? ` из ${result.candidates_total}`
                                    : ''}
                                  )
                                  <ChevronDown className="w-3 h-3" />
                                </>
                              )}
                            </button>
                          ) : null}
                        </div>
                      ) : (
                        <div className="rounded-lg border border-slate-200 dark:border-slate-800 p-3 text-xs text-slate-500 dark:text-slate-400">
                          Подходящие позиции КТРУ не найдены.
                        </div>
                      )}
                    </>
                  )}

                  {/* Уведомления о валидности позиций и уверенности */}
                  {notes.length > 0 ? (
                    <ul className="mt-3 space-y-1">
                      {notes.map((message, index) => (
                        <li
                          key={`${message.code}-${index}`}
                          className="flex items-start gap-1.5 text-[11px] leading-relaxed text-slate-500 dark:text-slate-400"
                        >
                          <Info className="w-3.5 h-3.5 shrink-0 mt-px text-blue-500" />
                          <span>{message.text}</span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </div>

              {/* 2. Основное уведомление — после воронки и списка */}
              {mainMessage ? (
                <div
                  className={`rounded-lg p-3.5 mt-4 flex items-start gap-3 border ${
                    result.status === 'resolved'
                      ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200/60 dark:border-emerald-900/50'
                      : result.status === 'name_not_found'
                        ? 'bg-red-50 dark:bg-red-950/30 border-red-200/60 dark:border-red-900/50'
                        : 'bg-amber-50 dark:bg-amber-950/30 border-amber-200/60 dark:border-amber-900/50'
                  }`}
                >
                  {result.status === 'resolved' ? (
                    <CircleCheck className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                  ) : result.status === 'name_not_found' ? (
                    <CircleX className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                  )}

                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] text-slate-800 dark:text-slate-200 leading-relaxed mb-2">
                      {mainMessage.text}
                    </p>

                    {/* Предложение уточнить характеристики */}
                    {result.suggestions.length > 0 && onSpecify ? (
                      <div className="flex flex-col items-start gap-1">
                        {result.suggestions.map((suggestion) => (
                          <button
                            key={suggestion.id}
                            type="button"
                            onClick={() => onSpecify(suggestion)}
                            className="text-xs font-semibold text-amber-900 dark:text-amber-400 hover:underline cursor-pointer text-left"
                          >
                            Указать: {suggestion.name}
                            {suggestion.required ? ' *' : ''} →
                          </button>
                        ))}
                      </div>
                    ) : null}

                    {/* Предложения уточнить наименование */}
                    {result.name_refinements.length > 0 && onUseName ? (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {result.name_refinements.map((item) => (
                          <button
                            key={item.name}
                            type="button"
                            onClick={() => onUseName(item.name)}
                            className="rounded-md border border-amber-300/70 dark:border-amber-800 px-2 py-0.5 text-[10px] text-amber-900 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/40 cursor-pointer"
                            title="Подставить наименование в описание"
                          >
                            {item.name} ({item.count})
                          </button>
                        ))}
                      </div>
                    ) : null}

                    {/* Альтернативные наименования, если исходное не найдено */}
                    {result.status === 'name_not_found' &&
                    alternatives.length > 0 ? (
                      <div className="mt-3">
                        <div className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                          Похожие наименования КТРУ
                        </div>

                        <div className="flex flex-wrap gap-1">
                          {alternatives.map((name) =>
                            onUseName ? (
                              <button
                                key={name}
                                type="button"
                                onClick={() => onUseName(name)}
                                className="rounded-md border border-slate-300 dark:border-slate-700 px-2 py-1 text-[10px] text-slate-700 dark:text-slate-300 hover:border-red-400 cursor-pointer text-left"
                                title="Подставить наименование в описание"
                              >
                                {name}
                              </button>
                            ) : (
                              <span
                                key={name}
                                className="rounded-md border border-slate-300 dark:border-slate-700 px-2 py-1 text-[10px] text-slate-700 dark:text-slate-300"
                              >
                                {name}
                              </span>
                            ),
                          )}
                        </div>
                      </div>
                    ) : null}

                    {result.status === 'name_not_found' &&
                    alternatives.length === 0 ? (
                      <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
                        Измените наименование товара в описании.
                      </p>
                    ) : null}
                  </div>
                </div>
              ) : null}

              {/* 3. Остальные сообщения */}
              {otherMessages.length > 0 ? (
                <ul className="mt-3 space-y-1.5">
                  {otherMessages.map((message, index) => {
                    const style = MESSAGE_STYLE[message.level];

                    return (
                      <li
                        key={`${message.code}-${index}`}
                        className={`flex items-start gap-2 text-[11px] leading-relaxed ${style.className}`}
                      >
                        {style.icon}
                        <span>{message.text}</span>
                      </li>
                    );
                  })}
                </ul>
              ) : null}
            </div>
          ) : null}
        </Card>
      </div>
    );
  },
);
