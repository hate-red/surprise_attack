'use client';

import React, { useState, useEffect } from 'react';
import { useAnalyzeStore } from '@/shared/model/use-analyze-store';


interface CharacteristicModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (value: string) => void;
  title?: string;
  description?: string;
  initialValue?: string; // Принимает пустую строку или текущее значение
}

export const CharacteristicModal: React.FC<CharacteristicModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  title = 'Уточните характеристику',
  description = 'Укажите тип матрицы экрана для полного соответствия КТРУ.',
  initialValue = '',
}) => {
  const [value, setValue] = useState(initialValue);
  const { text, setText, clearText } = useAnalyzeStore();

  // Обновляем состояние при открытии или изменении initialValue
  useEffect(() => {
    if (isOpen) {
      setValue(initialValue);
    }
  }, [isOpen, initialValue]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log(text + value)
    setText(text + " " + value)
    onSubmit(text + " " + value);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg p-6 mx-4 rounded-2xl bg-[#1a1614] border border-[#3d2b21] shadow-2xl">
        {/* Кнопка закрытия (крестик) */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          ✕
        </button>

        {/* Заголовок */}
        <h3 className="text-xl font-bold text-orange-500 mb-2">
          {title}
        </h3>
        
        {/* Описание */}
        <p className="text-sm text-gray-300 mb-6">
          {description}
        </p>

        {/* Форма */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
              Тип матрицы экрана
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Например: IPS, OLED, VA..."
              className="w-full px-4 py-3 rounded-xl bg-[#261f1c] border border-[#4d372c] text-white placeholder-gray-500 focus:outline-none focus:border-orange-500 transition-colors"
              autoFocus
            />
          </div>

          {/* Кнопки действий */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl text-sm font-medium text-gray-300 hover:bg-white/5 transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-orange-500 text-black hover:bg-orange-400 transition-colors shadow-lg shadow-orange-500/20"
            >
              Сохранить →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};