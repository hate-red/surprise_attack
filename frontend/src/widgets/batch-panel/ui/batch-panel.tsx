'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { ChevronDown, ChevronRight, FileText, LoaderCircle } from 'lucide-react';
import { Card } from '@/shared/ui/card/card';
import { Badge } from '@/shared/ui/badge/badge';
import { getBatch, listBatches } from '@/entities/batch/api/batches';
import type { Batch, BatchDetail, BatchItem, BatchStatus } from '@/entities/batch/model/types';

const STATUS: Record<BatchStatus, { label: string; variant: 'success' | 'warning' | 'info' | 'dark' }> = {
  pending: { label: 'В очереди', variant: 'info' },
  processing: { label: 'Обработка', variant: 'warning' },
  done: { label: 'Готово', variant: 'success' },
  error: { label: 'Ошибка', variant: 'dark' },
};

const RESULT: Record<string, { label: string; className: string }> = {
  resolved: { label: 'Код определён', className: 'text-emerald-600 dark:text-emerald-400' },
  need_more_info: { label: 'Нужны уточнения', className: 'text-amber-600 dark:text-amber-400' },
  low_confidence: { label: 'Неуверенно', className: 'text-amber-600 dark:text-amber-400' },
  name_not_found: { label: 'Наименование не найдено', className: 'text-red-600 dark:text-red-400' },
};

const isActive = (status: BatchStatus) => status === 'pending' || status === 'processing';

function ItemRow({ item }: { item: BatchItem }) {
  const result = item.result_status ? RESULT[item.result_status] : null;
  return (
    <li>
      <Link
        href={`/batches/${item.batch_id}/items/${item.id}`}
        className="flex items-start gap-3 px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <span className="w-6 shrink-0 text-[11px] text-slate-400 dark:text-slate-500 text-right">{item.row_number}</span>
        <span className="flex-1 min-w-0">
          <span className="block text-xs text-slate-800 dark:text-slate-200 truncate" title={item.description}>
            {item.description}
          </span>
          <span className="block text-[10px] text-slate-500 dark:text-slate-400">
            {item.status === 'done' && result ? (
              <span className={result.className}>
                {result.label}
                {item.ktru_code ? `: ${item.ktru_code}` : ''}
                {item.result_status === 'need_more_info' && item.candidates_count ? ` · кандидатов ${item.candidates_count}` : ''}
              </span>
            ) : item.status === 'error' ? (
              <span className="text-red-600 dark:text-red-400">Ошибка: {item.error}</span>
            ) : (
              STATUS[item.status].label
            )}
          </span>
        </span>
        {item.status === 'processing' ? <LoaderCircle className="w-3.5 h-3.5 text-amber-500 animate-spin shrink-0 mt-0.5" /> : null}
      </Link>
    </li>
  );
}

interface Props {
  refreshKey?: number;
  focusBatchId?: number | null;
}

export const BatchPanel = React.forwardRef<HTMLDivElement, Props>(({ refreshKey = 0, focusBatchId = null }, ref) => {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [details, setDetails] = useState<Record<number, BatchDetail>>({});
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const expandedRef = useRef(expanded);
  expandedRef.current = expanded;

  const load = useCallback(async () => {
    try {
      const list = await listBatches();
      setBatches(list);
      setError(null);
      const open = [...expandedRef.current];
      const loaded = await Promise.all(open.map((id) => getBatch(id).catch(() => null)));
      setDetails((prev) => {
        const next = { ...prev };
        loaded.forEach((d) => {
          if (d) next[d.id] = d;
        });
        return next;
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить пакеты');
    }
  }, []);

  useEffect(() => {
    if (focusBatchId) setExpanded((prev) => new Set(prev).add(focusBatchId));
  }, [focusBatchId]);

  useEffect(() => {
    void load();
  }, [load, refreshKey, expanded]);

  // пока есть пакеты в обработке — обновляем статусы
  const hasActive = batches.some((b) => isActive(b.status)) ||
    Object.values(details).some((d) => d.items.some((i) => isActive(i.status)));
  useEffect(() => {
    if (!hasActive) return;
    const timer = setInterval(() => void load(), 1500);
    return () => clearInterval(timer);
  }, [hasActive, load]);

  const toggle = (id: number) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  return (
    <div ref={ref} className="mt-10">
      <div className="mb-5 flex items-baseline justify-between">
        <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100">Пакетная обработка CSV</h2>
        <span className="text-[11px] text-slate-400 dark:text-slate-500">загрузка — кнопка со скрепкой в форме</span>
      </div>
      <Card className="p-0 overflow-hidden">
        {error ? <p className="p-4 text-xs text-red-500">{error}</p> : null}
        {!error && batches.length === 0 ? (
          <p className="p-6 text-xs text-slate-400 dark:text-slate-500 text-center">
            Пакетов пока нет. Загрузите CSV-файл с колонкой описаний товаров.
          </p>
        ) : null}
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {batches.map((b) => {
            const open = expanded.has(b.id);
            const detail = details[b.id];
            const percent = b.total_items ? Math.round((b.processed_items / b.total_items) * 100) : 0;
            return (
              <li key={b.id}>
                <button
                  type="button"
                  onClick={() => toggle(b.id)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                >
                  {open ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                  <FileText className="w-4 h-4 text-red-600 dark:text-red-500 shrink-0" />
                  <span className="flex-1 min-w-0">
                    <span className="block text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                      #{b.id} · {b.filename}
                    </span>
                    <span className="block text-[10px] text-slate-500 dark:text-slate-400">
                      {new Date(b.created_at).toLocaleString('ru-RU')} · обработано {b.processed_items} из {b.total_items}
                    </span>
                    <span className="mt-1.5 block w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <span
                        className={`block h-full rounded-full transition-all ${b.status === 'error' ? 'bg-red-500' : 'bg-emerald-500'}`}
                        style={{ width: `${percent}%` }}
                      />
                    </span>
                  </span>
                  <Badge variant={STATUS[b.status].variant}>{STATUS[b.status].label}</Badge>
                </button>
                {open ? (
                  detail ? (
                    <ul className="border-t border-slate-100 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-950/30 max-h-96 overflow-y-auto">
                      {detail.items.map((item) => (
                        <ItemRow key={item.id} item={item} />
                      ))}
                    </ul>
                  ) : (
                    <p className="px-4 py-3 text-xs text-slate-400">Загрузка строк…</p>
                  )
                ) : null}
              </li>
            );
          })}
        </ul>
      </Card>
    </div>
  );
});
BatchPanel.displayName = 'BatchPanel';
