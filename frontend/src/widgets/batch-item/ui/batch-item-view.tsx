'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, LoaderCircle } from 'lucide-react';
import { Card } from '@/shared/ui/card/card';
import { Badge } from '@/shared/ui/badge/badge';
import { getBatchItem } from '@/entities/batch/api/batches';
import type { BatchItemDetail } from '@/entities/batch/model/types';
import { useAnalysisStore } from '@/entities/product/model/use-analysis-store';
import { useAnalyzeStore } from '@/shared/model/use-analyze-store';
import { AnalysisWorkspace } from '@/widgets/analysis-workspace/ui/analysis-workspace';

const STATUS_LABEL: Record<BatchItemDetail['status'], string> = {
  pending: 'В очереди',
  processing: 'Обрабатывается',
  done: 'Обработано',
  error: 'Ошибка',
};

export const BatchItemView: React.FC = () => {
  const { batchId, itemId } = useParams<{ batchId: string; itemId: string }>();
  const [item, setItem] = useState<BatchItemDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loadedFor = useRef<string | null>(null);
  const setText = useAnalyzeStore((s) => s.setText);
  const loadResult = useAnalysisStore((s) => s.loadResult);
  const analyze = useAnalysisStore((s) => s.analyze);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const key = `${batchId}/${itemId}`;

    const fetchItem = async () => {
      try {
        const data = await getBatchItem(batchId, itemId);
        if (cancelled) return;
        setItem(data);
        setError(null);
        if (data.status === 'done' && loadedFor.current !== key) {
          loadedFor.current = key;
          setText(data.description);
          loadResult(data.description, data.result);
        } else if (data.status === 'pending' || data.status === 'processing') {
          setText(data.description);
          timer = setTimeout(fetchItem, 1500);
        } else if (data.status === 'error' && loadedFor.current !== key) {
          loadedFor.current = key;
          setText(data.description);
          loadResult(data.description, null);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Не удалось загрузить строку пакета');
      }
    };
    void fetchItem();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [batchId, itemId, setText, loadResult]);

  return (
    <>
      <div className="mb-6 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-1.5 text-xs font-semibold text-red-600 dark:text-red-400 hover:underline">
          <ArrowLeft className="w-3.5 h-3.5" /> К пакетам
        </Link>
        <span className="text-[11px] text-slate-500 dark:text-slate-400">
          Пакет #{batchId}{item ? ` · строка ${item.row_number}` : ''}
        </span>
      </div>

      <Card className="mb-8">
        <div className="flex items-start justify-between gap-4 mb-2">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 dark:text-slate-400">
            Описание товара из CSV
          </span>
          {item ? (
            <Badge variant={item.status === 'done' ? 'success' : item.status === 'error' ? 'dark' : 'warning'}>
              {STATUS_LABEL[item.status]}
            </Badge>
          ) : null}
        </div>
        {error ? <p className="text-xs text-red-500">{error}</p> : null}
        {!item && !error ? <p className="text-xs text-slate-400 flex items-center gap-2"><LoaderCircle className="w-3.5 h-3.5 animate-spin" /> Загрузка…</p> : null}
        {item ? <p className="text-sm text-slate-800 dark:text-slate-100 leading-relaxed">{item.description}</p> : null}
        {item?.status === 'error' ? (
          <div className="mt-3 flex items-center gap-3">
            <span className="text-xs text-red-600 dark:text-red-400">Ошибка обработки: {item.error}</span>
            <button type="button" onClick={() => void analyze(item.description)} className="text-xs font-semibold text-red-600 hover:underline cursor-pointer">
              Повторить анализ
            </button>
          </div>
        ) : null}
        {item && (item.status === 'pending' || item.status === 'processing') ? (
          <p className="mt-2 text-xs text-amber-600 dark:text-amber-400 flex items-center gap-2">
            <LoaderCircle className="w-3.5 h-3.5 animate-spin" /> Строка ещё обрабатывается — результат появится автоматически.
          </p>
        ) : null}
      </Card>

      <AnalysisWorkspace formTitle="Описание и заполнение спецификации" />
    </>
  );
};
