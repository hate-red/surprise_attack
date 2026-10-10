'use client';

import React from 'react';
import { Card } from '@/shared/ui/card/card';
import { CharacteristicRow, Characteristic } from '@/entities/characteristic/ui/characteristic-row';
import { RefreshCw, Plus } from 'lucide-react';

interface Props {
  items: Characteristic[];
}

export const KtruTableWidget: React.FC<Props> = ({ items }) => {
  return (
    <Card className="p-0 overflow-hidden">
      {/* Шапка таблицы */}
      <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-white">
        <div className="flex space-x-6 text-sm font-semibold">
          <button className="text-red-600 border-b-2 border-red-600 pb-2  flex items-center">
            Характеристики{' '}
            <span className="ml-1.5 bg-red-100 text-red-600 text-xs px-2 py-0.5 rounded-full">
              {items.length}
            </span>
          </button>
          <button className="text-slate-400 hover:text-slate-600 pb-4 -mb-4">
            Исходный текст
          </button>
        </div>
        <button className="text-xs text-red-600 font-semibold hover:underline flex items-center">
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Обновить
        </button>
      </div>

      {/* Таблица */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#264b83] text-white text-[11px] uppercase tracking-wider">
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
      <div className="p-4 bg-slate-50/50 border-t border-slate-200 flex justify-between items-center">
        <button className="text-xs font-semibold text-red-600 hover:text-red-700 flex items-center">
          <Plus className="w-4 h-4 mr-1" /> Добавить характеристику
        </button>
        <span className="text-[11px] text-slate-400">
          <span className="text-red-500">*</span> обязательная характеристика
        </span>
      </div>
    </Card>
  );
};