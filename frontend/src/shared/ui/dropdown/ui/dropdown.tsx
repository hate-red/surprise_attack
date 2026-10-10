'use client';

import React, { useState, useRef, useEffect } from 'react';
import { DropdownProps } from '../model/types';

export const Dropdown: React.FC<DropdownProps> = ({
  trigger,
  items,
  align = 'left',
  className = '',
  width = 'w-56',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Закрытие при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Закрытие по нажатию Esc
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      {/* Триггер (кнопка, аватарка и т.д.) */}
      <div onClick={() => setIsOpen((prev) => !prev)} className="cursor-pointer inline-flex items-center">
        {trigger}
      </div>

      {/* Выпадающее меню */}
      {isOpen && (
        <div
          className={`absolute z-50 mt-2 ${width} rounded-xl bg-white shadow-lg ring-1 ring-black/5 focus:outline-none dark:bg-zinc-900 dark:ring-white/10 transition-all transform origin-top animate-in fade-in zoom-in-95 duration-100 ${
            align === 'right' ? 'right-0' : 'left-0'
          }`}
        >
          <div className="p-1 space-y-0.5">
            {items.map((item) => (
              <button
                key={item.id}
                disabled={item.disabled}
                onClick={() => {
                  if (item.onClick) item.onClick();
                  setIsOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm rounded-lg text-left transition-colors ${
                  item.disabled
                    ? 'opacity-50 cursor-not-allowed text-zinc-400 dark:text-zinc-600'
                    : 'text-zinc-700 hover:bg-zinc-100 dark:text-zinc-200 dark:hover:bg-zinc-800/60'
                }`}
              >
                {item.icon && <span className="shrink-0 text-zinc-500 dark:text-zinc-400">{item.icon}</span>}
                <span className="truncate">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};