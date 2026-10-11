import React from 'react';
import { Edit2, Trash2, Plus } from 'lucide-react';
import type { RowSource, RowStatus } from '@/entities/product/model/types';

export interface Characteristic {
  id: string;
  name: string;
  /** фрагмент исходного описания */
  description: string;
  normalized: string;
  unit: string;
  confidence: string;
  isRequired: boolean;
  status?: RowStatus;
  source?: RowSource;
  matchedRange?: string | null;
  notes?: string[];
  suggestions?: string[];
  options?: string[];
  inSpecification?: boolean;
}

interface Props {
  data: Characteristic;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onApplySuggestion?: (id: string, value: string) => void;
}

const STATUS_LABELS: Record<RowStatus, { label: string; className: string }> = {
  ok: { label: 'Соответствует КТРУ', className: 'text-emerald-600 dark:text-emerald-400' },
  no_constraints: { label: 'Без ограничений в КТРУ', className: 'text-emerald-600 dark:text-emerald-400' },
  invalid: { label: 'Недопустимое значение', className: 'text-red-600 dark:text-red-400' },
  unit_mismatch: { label: 'Несовместимая единица', className: 'text-red-600 dark:text-red-400' },
  conflict: { label: 'Противоречие', className: 'text-amber-600 dark:text-amber-400' },
  ambiguous: { label: 'Неоднозначно', className: 'text-amber-600 dark:text-amber-400' },
  no_value: { label: 'Нет значения', className: 'text-amber-600 dark:text-amber-400' },
  ste_only: { label: 'Из выгрузки СТЕ', className: 'text-blue-600 dark:text-blue-400' },
  not_applicable: { label: 'Не для этой позиции', className: 'text-slate-500 dark:text-slate-400' },
  unrecognized: { label: 'Не распознана', className: 'text-red-600 dark:text-red-400' },
  missing: { label: 'Не указана', className: 'text-slate-500 dark:text-slate-400' },
};

export const CharacteristicRow: React.FC<Props> = ({ data, onEdit, onDelete, onApplySuggestion }) => {
  const status = data.status ? STATUS_LABELS[data.status] : null;
  const isError = data.status === 'invalid' || data.status === 'unit_mismatch' || data.status === 'unrecognized';
  const isMissing = data.status === 'missing';

  return (
    <tr
      className={`hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors border-b border-slate-100 dark:border-slate-800 text-xs align-top ${
        isError ? 'bg-red-50/40 dark:bg-red-950/10' : ''
      }`}
    >
      <td className="py-3.5 px-6 font-medium text-slate-800 dark:text-slate-200">
        <p className="relative w-fit pr-2">
          {data.name} {data.isRequired && <span className="text-red-500 dark:text-red-400 absolute top-[-6px] right-[-6px]">*</span>}
        </p>
        <div className="text-[10px] text-slate-400 dark:text-slate-500 font-normal mt-0.5">
          {status ? <span className={status.className}>{status.label}</span> : null}
          {data.confidence ? <span> · уверенность {data.confidence}</span> : null}
          {data.source === 'user' ? <span> · указано вами</span> : null}
        </div>
      </td>
      <td className="py-3.5 px-6 text-slate-600 dark:text-slate-300">
        {data.description || <span className="text-slate-300 dark:text-slate-600">—</span>}
      </td>
      <td className="py-3.5 px-6 font-semibold text-slate-900 dark:text-slate-100">
        {isMissing ? (
          <span className="font-normal text-slate-400 dark:text-slate-500">не указано</span>
        ) : (
          <span className={isError ? 'line-through decoration-red-400/70' : ''}>{data.normalized || '—'}</span>
        )}
        {data.matchedRange ? (
          <div className="mt-1 text-[10px] font-normal text-emerald-700 dark:text-emerald-400">
            в диапазоне КТРУ: {data.matchedRange}
          </div>
        ) : null}
        {data.notes && data.notes.length > 0 ? (
          <ul className="mt-1 space-y-0.5 text-[10px] font-normal text-slate-500 dark:text-slate-400 max-w-xs">
            {data.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        ) : null}
        {data.suggestions && data.suggestions.length > 0 && onApplySuggestion ? (
          <div className="mt-1.5 flex flex-wrap gap-1 max-w-xs">
            {data.suggestions.slice(0, 6).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => onApplySuggestion(data.id, value)}
                className="rounded-md border border-slate-200 dark:border-slate-700 px-1.5 py-0.5 text-[10px] font-normal text-slate-600 dark:text-slate-300 hover:border-red-400 hover:text-red-600 dark:hover:text-red-400 cursor-pointer transition-colors"
                title="Подставить значение из справочника КТРУ"
              >
                {value}
              </button>
            ))}
          </div>
        ) : null}
      </td>
      <td className="py-3.5 px-6 text-slate-500 dark:text-slate-400">{data.unit || '—'}</td>
      <td className="py-3.5 px-6 text-right space-x-2 whitespace-nowrap">
        {onEdit && (
          <button
            type="button"
            onClick={() => onEdit(data.id)}
            title={isMissing ? 'Указать значение' : 'Изменить значение'}
            className="text-slate-400 hover:text-blue-600 dark:text-slate-500 dark:hover:text-blue-400 cursor-pointer transition-colors"
          >
            {isMissing ? <Plus className="w-3.5 h-3.5" /> : <Edit2 className="w-3.5 h-3.5" />}
          </button>
        )}
        {onDelete && !isMissing && (
          <button
            type="button"
            onClick={() => onDelete(data.id)}
            title="Исключить из анализа"
            className="text-slate-400 hover:text-red-600 dark:text-slate-500 dark:hover:text-red-400 cursor-pointer transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </td>
    </tr>
  );
};
