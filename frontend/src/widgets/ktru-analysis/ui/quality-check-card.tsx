import React from 'react';
import { AlertTriangle, CheckCircle2, CircleX } from 'lucide-react';
import { Card } from '@/shared/ui/card/card';
import type { ParseResponse } from '@/entities/product/model/types';

interface Props {
  result: ParseResponse | null;
  isLoading?: boolean;
}

function plural(n: number, one: string, few: string, many: string) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
}

export const QualityCheckCard: React.FC<Props> = ({ result, isLoading }) => {
  const q = result?.quality ?? {};
  const total = q.required_total ?? 0;
  const filled = q.required_filled ?? 0;
  const errors = q.errors ?? 0;
  const typos = q.typos ?? 0;
  const unrecognized = (q.unrecognized ?? 0) + (q.ambiguous ?? 0);
  const percent = total > 0 ? Math.round((filled / total) * 100) : 0;

  return (
    <Card>
      <div className="flex justify-between items-center mb-3">
        <span className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Проверка качества</span>
        <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          {result ? (total > 0 ? `обязательных: ${filled} из ${total}` : 'обязательных нет') : '—'}
        </span>
      </div>
      <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden mb-3">
        <div
          className={`h-full rounded-full transition-all ${errors > 0 ? 'bg-amber-500' : 'bg-emerald-500'} ${isLoading ? 'animate-pulse' : ''}`}
          style={{ width: `${result ? percent : 0}%` }}
        />
      </div>
      {result ? (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
          {errors === 0 ? (
            <span className="flex items-center text-emerald-600 dark:text-emerald-400"><CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Ошибок нет</span>
          ) : (
            <span className="flex items-center text-red-600 dark:text-red-400"><CircleX className="w-3.5 h-3.5 mr-1" /> {errors} {plural(errors, 'ошибка', 'ошибки', 'ошибок')} в значениях</span>
          )}
          {typos === 0 ? (
            <span className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 mr-1.5"></span> Опечаток нет</span>
          ) : (
            <span className="flex items-center text-red-600 dark:text-red-400"><span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-1.5"></span> {typos} {plural(typos, 'опечатка', 'опечатки', 'опечаток')}</span>
          )}
          {unrecognized > 0 ? (
            <span className="flex items-center text-amber-600 dark:text-amber-400"><AlertTriangle className="w-3.5 h-3.5 mr-1" /> {unrecognized} не {plural(unrecognized, 'распознана', 'распознаны', 'распознано')}</span>
          ) : null}
          <span>Распознано характеристик: {q.recognized ?? 0}</span>
        </div>
      ) : (
        <div className="text-xs text-slate-400 dark:text-slate-500">
          {isLoading ? 'Идёт проверка…' : 'Результат появится после анализа описания.'}
        </div>
      )}
    </Card>
  );
};
