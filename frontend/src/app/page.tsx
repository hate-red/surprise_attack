// src/app/page.tsx
'use client';

import { Header } from '@/widgets/header/ui/header';
import { Footer } from '@/widgets/footer/ui/footer';
import { AnalyzeForm } from '@/features/analyze-text/ui/analyze-form';
import { KtruTableWidget } from '@/widgets/ktru-analysis/ui/ktru-table-widget';
import { Card } from '@/shared/ui/card/card';
import { Badge } from '@/shared/ui/badge/badge';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import { sendProductString } from '@/entities/product/api/sendProductString';

const mockCharacteristics = [
  { id: '1', name: 'Тип процессора', description: 'Intel Core i5', normalized: 'Intel Core i5', unit: '—', confidence: '99%', isRequired: true },
  { id: '2', name: 'Диагональ экрана', description: 'Intel Core i5', normalized: '15,6', unit: '—', confidence: '99%', isRequired: true },
  { id: '3', name: 'Объем SSD-накопителя', description: 'Intel Core i5', normalized: '512', unit: '—', confidence: '99%', isRequired: true },
  { id: '4', name: 'Диагональ экрана', description: 'Intel Core i5', normalized: 'Intel Core i5', unit: 'дюйм', confidence: '99%', isRequired: true },
];

export default function Page() {
  const handleAnalyze = (text: string) => {
    sendProductString(text)
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
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Работает на основе сложных LLM моделей</p>
        </div>

        {/* Сетка страницы */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Левая колонка: Форма ввода + Блок КТРУ */}
          <div className="lg:col-span-5 space-y-5">
            <AnalyzeForm sendProductString={handleAnalyze} />

            {/* Блок проверки качества и КТРУ */}
            <div className="space-y-6">
              <Card>
                <div className="flex justify-between items-center mb-3">
                  <span className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Проверка качества</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">5 из 6</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden mb-3">
                  <div className="bg-emerald-500 h-full w-[85%] rounded-full"></div>
                </div>
                <div className="flex items-center space-x-4 text-xs text-slate-500 dark:text-slate-400">
                  <span className="flex items-center text-emerald-600 dark:text-emerald-400"><CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Ошибок нет</span>
                  <span className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 mr-1.5"></span> Опечаток нет</span>
                </div>
              </Card>

              <Card>
                <div className="flex justify-between items-center mb-4">
                  <span className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Подбор КТРУ</span>
                  <Badge variant="success">СУЖЕНИЕ ЗАВЕРШЕНО</Badge>
                </div>

                <div className="grid grid-cols-3 gap-2 mb-4">
                  <div className="bg-slate-50 dark:bg-slate-900/60 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                    <div className="w-5 h-5 bg-red-600 text-white rounded-full flex items-center justify-center text-xs font-bold mb-1">1</div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">26 · Оборудование...</div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-900/60 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                    <div className="w-5 h-5 bg-red-600 text-white rounded-full flex items-center justify-center text-xs font-bold mb-1">2</div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">26.20 · Компьютеры...</div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-900/60 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                    <div className="w-5 h-5 bg-red-600 text-white rounded-full flex items-center justify-center text-xs font-bold mb-1">3</div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">26.20.11 · Портативные...</div>
                  </div>
                </div>

                <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-900/50 rounded-lg p-3.5 mb-4 flex items-start space-x-3">
                  <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-bold text-amber-900 dark:text-amber-400 mb-1">Уточните одну характеристику</div>
                    <p className="text-[11px] text-amber-800 dark:text-amber-300/85 leading-relaxed mb-2">
                      Для полного соответствия КТРУ укажите тип матрицы экрана.
                    </p>
                    <button className="text-xs font-semibold text-amber-900 dark:text-amber-400 hover:underline">
                      Добавить тип матрицы →
                    </button>
                  </div>
                </div>

                <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-4 bg-white dark:bg-slate-900/50">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-red-600 dark:text-red-500 block mb-1">Рекомендуемый код</span>
                  <div className="font-bold text-slate-900 dark:text-slate-100 text-sm mb-1">26.20.11.110-00000023</div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mb-3">Компьютеры портативные массой не более 10 кг</p>
                  <div className="flex justify-between items-center text-[11px] pt-2 border-t border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 dark:text-slate-500">Соответствие</span>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">94%</span>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Правая колонка: Таблица итоговых характеристик */}
          <div className="lg:col-span-7">
            <div className="mb-5">
              <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100">Итоговые Характеристики</h2>
            </div>
            <KtruTableWidget items={mockCharacteristics} />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}