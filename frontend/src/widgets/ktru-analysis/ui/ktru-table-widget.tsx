'use client';

import React, { useState } from 'react';
import { Card } from '@/shared/ui/card/card';
import { CharacteristicRow, Characteristic } from '@/entities/characteristic/ui/characteristic-row';
import { RefreshCw, Plus, Copy, Check } from 'lucide-react';

interface Props {
  items: Characteristic[];
  rawText?: string;
}

export const KtruTableWidget: React.FC<Props> = ({ 
  items, 
  rawText = 'Acer puper truper 20000 rtx 4000\n\nХарактеристики устройства:\n- Процессор: Intel Core i5\n- Экран: 15.6 дюймов\n- Накопитель: 512 ГБ SSD' 
}) => {
  const [activeTab, setActiveTab] = useState<'characteristics' | 'source'>('characteristics');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(rawText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="p-0 overflow-hidden">
      {/* Шапка с вкладками */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-white dark:bg-slate-900 transition-colors">
        <div className="flex space-x-6 text-sm font-semibold">
          <button 
            onClick={() => setActiveTab('characteristics')}
            className={`pb-2 flex items-center transition-colors border-b-2 cursor-pointer ${
              activeTab === 'characteristics'
                ? 'text-red-600 dark:text-red-500 border-red-600 dark:border-red-500'
                : 'text-slate-400 dark:text-slate-500 border-transparent hover:text-slate-600 dark:hover:text-slate-300'
            }`}
          >
            Характеристики{' '}
            <span className={`ml-1.5 text-xs px-2 py-0.5 rounded-full transition-colors ${
              activeTab === 'characteristics'
                ? 'bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
            }`}>
              {items.length}
            </span>
          </button>

          <button 
            onClick={() => setActiveTab('source')}
            className={`pb-2 transition-colors border-b-2 cursor-pointer ${
              activeTab === 'source'
                ? 'text-red-600 dark:text-red-500 border-red-600 dark:border-red-500'
                : 'text-slate-400 dark:text-slate-500 border-transparent hover:text-slate-600 dark:hover:text-slate-300'
            }`}
          >
            Исходный текст
          </button>
        </div>

        <button className="text-xs text-red-600 dark:text-red-400 font-semibold hover:underline flex items-center transition-colors cursor-pointer">
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Обновить
        </button>
      </div>

      {/* Вкладка 1: Таблица характеристик */}
      {activeTab === 'characteristics' && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#264b83] dark:bg-slate-800/80 text-white text-[11px] uppercase tracking-wider transition-colors">
                  <th className="py-3 px-6 font-semibold">Характеристика</th>
                  <th className="py-3 px-6 font-semibold">Из описания</th>
                  <th className="py-3 px-6 font-semibold">Нормализовано</th>
                  <th className="py-3 px-6 font-semibold">Ед. измерения</th>
                  <th className="py-3 px-6 font-semibold text-right">Действия</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <CharacteristicRow
                    key={item.id}
                    data={item}
                    onEdit={(id) => console.log('Edit', id)}
                    onDelete={(id) => console.log('Delete', id)}
                  />
                ))}
              </tbody>
            </table>
          </div>

          {/* Футер таблицы */}
          <div className="p-4 bg-slate-50/50 dark:bg-slate-900/60 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center transition-colors">
            <button className="text-xs font-semibold text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 flex items-center transition-colors cursor-pointer">
              <Plus className="w-4 h-4 mr-1" /> Добавить характеристику
            </button>
            <span className="text-[11px] text-slate-400 dark:text-slate-500">
              <span className="text-red-500 dark:text-red-400">*</span> обязательная характеристика
            </span>
          </div>
        </>
      )}

      {/* Вкладка 2: Исходный текст */}
      {activeTab === 'source' && (
        <div className="p-6 bg-white dark:bg-slate-900 transition-colors">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Введенный текст для распознавания
            </span>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Скопировано!' : 'Скопировать'}
            </button>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800 font-mono text-xs text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap min-h-[220px]">
            {rawText}
          </div>
        </div>
      )}
    </Card>
  );
};