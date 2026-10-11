'use client';

import { useRef, useState } from 'react';
import { Header } from '@/widgets/header/ui/header';
import { Footer } from '@/widgets/footer/ui/footer';
import { AnalysisWorkspace } from '@/widgets/analysis-workspace/ui/analysis-workspace';
import { BatchPanel } from '@/widgets/batch-panel/ui/batch-panel';
import { uploadBatch } from '@/entities/batch/api/batches';

export default function Page() {
  const [batchRefreshKey, setBatchRefreshKey] = useState(0);
  const [focusBatchId, setFocusBatchId] = useState<number | null>(null);
  const batchPanelRef = useRef<HTMLDivElement>(null);

  // CSV с одной колонкой описаний -> пакет; статусы строк — в панели ниже
  const handleUpload = async (files: File[]) => {
    for (const file of files) {
      const batch = await uploadBatch(file);
      setFocusBatchId(batch.id);
    }
    setBatchRefreshKey((k) => k + 1);
    batchPanelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans transition-colors">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8">
        {/* Заголовок */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mb-2">
            Автозаполнение ключевых характеристик в <span className="text-[#cc1f14]">СТЕ</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Работает на основе справочника КТРУ и выгрузок портала поставщиков
          </p>
        </div>

        {/* Сетка страницы: форма, проверка качества, подбор КТРУ и таблица характеристик */}
        <AnalysisWorkspace onUploadFiles={handleUpload} />

        {/* Панель пакетной обработки CSV */}
        <BatchPanel ref={batchPanelRef} refreshKey={batchRefreshKey} focusBatchId={focusBatchId} />
      </main>

      <Footer />
    </div>
  );
}
