'use client';

import React, { useState, useEffect } from 'react';


interface CharacteristicModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Значение, выбранное или введённое пользователем */
  onSubmit: (value: string, name: string) => void;
  title?: string;
  description?: string;
  /** Название характеристики; если не задано — пользователь вводит его сам */
  characteristicName?: string;
  /** Названия характеристик для выбора (режим "Добавить характеристику") */
  characteristicNames?: string[];
  /** Допустимые значения из справочника КТРУ */
  options?: string[];
  unit?: string;
  initialValue?: string; // Принимает пустую строку или текущее значение
}

export const CharacteristicModal: React.FC<CharacteristicModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  title = 'Уточните характеристику',
  description = 'Выберите значение из справочника КТРУ или введите своё.',
  characteristicName,
  characteristicNames = [],
  options = [],
  unit,
  initialValue = '',
}) => {
  const [value, setValue] = useState(initialValue);
  const [name, setName] = useState(characteristicName ?? '');

  // Обновляем состояние при открытии или изменении initialValue
  useEffect(() => {
    if (isOpen) {
      setValue(initialValue);
      setName(characteristicName ?? '');
    }
  }, [isOpen, initialValue, characteristicName]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim() || !name.trim()) return;
    onSubmit(value.trim(), name.trim());
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg p-6 mx-4 rounded-2xl bg-[#1a1614] border border-[#3d2b21] shadow-2xl">
        {/* Кнопка закрытия (крестик) */}
        <button
          type="button"
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
          {characteristicName === undefined ? (
            <div>
              <label htmlFor="characteristic-name" className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
                Характеристика
              </label>
              <input
                id="characteristic-name"
                type="text"
                list="characteristic-name-options"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Например: Тип каркаса"
                className="w-full px-4 py-3 rounded-xl bg-[#261f1c] border border-[#4d372c] text-white placeholder-gray-500 focus:outline-none focus:border-orange-500 transition-colors"
                autoFocus
              />
              <datalist id="characteristic-name-options">
                {characteristicNames.map((n) => (
                  <option key={n} value={n} />
                ))}
              </datalist>
            </div>
          ) : null}
          <div>
            <label htmlFor="characteristic-value" className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
              {characteristicName ? characteristicName : 'Значение'}{unit ? `, ${unit}` : ''}
            </label>
            <input
              id="characteristic-value"
              type="text"
              list="characteristic-value-options"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={options.length ? `Например: ${options[0]}` : 'Введите значение'}
              className="w-full px-4 py-3 rounded-xl bg-[#261f1c] border border-[#4d372c] text-white placeholder-gray-500 focus:outline-none focus:border-orange-500 transition-colors"
              autoFocus={characteristicName !== undefined}
            />
            <datalist id="characteristic-value-options">
              {options.map((o) => (
                <option key={o} value={o} />
              ))}
            </datalist>
          </div>

          {options.length > 0 ? (
            <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
              {options.slice(0, 30).map((o) => (
                <button
                  key={o}
                  type="button"
                  onClick={() => setValue(o)}
                  className={`px-2.5 py-1 rounded-lg text-xs border transition-colors ${
                    value === o
                      ? 'bg-orange-500 text-black border-orange-500'
                      : 'border-[#4d372c] text-gray-300 hover:border-orange-500'
                  }`}
                >
                  {o}
                </button>
              ))}
            </div>
          ) : null}

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
              disabled={!value.trim() || !name.trim()}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-orange-500 text-black hover:bg-orange-400 transition-colors shadow-lg shadow-orange-500/20 disabled:opacity-50"
            >
              Сохранить →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
