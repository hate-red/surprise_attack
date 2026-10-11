'use client';

import React, { useState, Dispatch, SetStateAction } from 'react';
import { useAnalyzeStore } from '@/shared/model/use-analyze-store';

interface TextCorrectionToasterProps {
  replacetext: string;
  setSuggest: Dispatch<SetStateAction<string>>;
  /** Вызывается после замены текста (повторный анализ исправленного описания) */
  onApply?: (text: string) => void;
}

export const TextCorrectionToaster = ({ replacetext, setSuggest, onApply }: TextCorrectionToasterProps) => {
  const [isVisible, setIsVisible] = useState(true);
  const { setText } = useAnalyzeStore();

  if (!isVisible) return null;

  const handleApply = () => {
    setText(replacetext);
    setIsVisible(false);
    setSuggest('');
    onApply?.(replacetext);
  };

  const handleDismiss = () => {
    setIsVisible(false);
    setSuggest('');
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 w-full max-w-md rounded-2xl border border-slate-800 bg-[#131b2e]/95 p-4 shadow-2xl backdrop-blur-md transition-all duration-300">
      <div className="flex items-start gap-3">
        {/* Иконка уведомления в стиле темы */}
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-red-500/10 text-red-500">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        {/* Контент */}
        <div className="flex-1 text-sm">
          <h4 className="font-semibold text-slate-100">
            Найдена опечатка или исправление
          </h4>
          <p className="mt-1 text-xs text-slate-400">
            Предлагаем заменить исходное описание на следующее:
          </p>

          <div className="mt-2.5 rounded-xl border border-slate-800 bg-[#0b0f19] p-2.5 font-mono text-xs text-slate-200">
            {replacetext}
          </div>

          {/* Кнопки действий */}
          <div className="mt-3.5 flex items-center gap-2">
            <button
              type="button"
              onClick={handleApply}
              className="rounded-xl bg-red-600 px-3.5 py-1.5 text-xs font-medium text-white transition hover:bg-red-700 active:scale-95 focus:outline-none focus:ring-2 focus:ring-red-500/50"
            >
              Применить
            </button>
            <button
              type="button"
              onClick={handleDismiss}
              className="rounded-xl border border-slate-800 bg-slate-800/40 px-3.5 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white active:scale-95"
            >
              Отклонить
            </button>
          </div>
        </div>

        {/* Кнопка закрытия (крестик) */}
        <button
          type="button"
          onClick={handleDismiss}
          className="flex h-6 w-6 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-800 hover:text-slate-300"
          aria-label="Закрыть"
        >
          ✕
        </button>
      </div>
    </div>
  );
};