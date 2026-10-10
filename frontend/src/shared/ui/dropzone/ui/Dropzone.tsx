'use client';

import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { UploadCloud, File as FileIcon, X } from 'lucide-react';
import { DropzoneProps } from '../model/types';

export const Dropzone: React.FC<DropzoneProps> = ({
  onFilesSelected,
  accept,
  multiple = true,
  maxSize,
  children,
  className = '',
  disabled = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Валидация файлов
  const validateAndHandleFiles = (filesList: FileList | null) => {
    if (!filesList || filesList.length === 0 || disabled) return;

    const filesArray = Array.from(filesList);
    const validFiles: File[] = [];
    setError(null);

    for (const file of filesArray) {
      // Проверка размера
      if (maxSize && file.size > maxSize) {
        const sizeMb = (maxSize / (1024 * 1024)).toFixed(1);
        setError(`Файл "${file.name}" превышает допустимый размер (${sizeMb} MB)`);
        return;
      }

      // Проверка формата (MIME-type)
      if (accept && accept.length > 0) {
        const isAccepted = accept.some((type) => {
          if (type.endsWith('/*')) {
            const category = type.split('/')[0];
            return file.type.startsWith(`${category}/`);
          }
          return file.type === type;
        });

        if (!isAccepted) {
          setError(`Формат файла "${file.name}" не поддерживается`);
          return;
        }
      }

      validFiles.push(file);
      if (!multiple) break;
    }

    if (validFiles.length > 0) {
      onFilesSelected(validFiles);
    }
  };

  // Обработчики Drag & Drop
  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled) return;
    validateAndHandleFiles(e.dataTransfer.files);
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    validateAndHandleFiles(e.target.files);
    if (e.target) e.target.value = '';
  };

  const handleClick = () => {
    if (!disabled && inputRef.current) {
      inputRef.current.click();
    }
  };

  const acceptString = accept?.join(',');

  return (
    <div className="w-full mb-4">
      <div
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center w-full min-h-[160px] p-6 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-200 select-none ${
          isDragOver
            ? 'border-red-500 bg-red-50/50 dark:bg-red-950/20 scale-[0.99]'
            : 'border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-[#264b83] hover:border-slate-300 dark:hover:border-slate-600 hover:bg-[#264b83]/50 dark:hover:bg-[#264b83]/50'
        } ${disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''} ${className}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={acceptString}
          multiple={multiple}
          onChange={handleInputChange}
          disabled={disabled}
          className="hidden"
        />

        {children ? (
          children
        ) : (
          <div className="flex flex-col items-center text-center gap-2">
            <div
              className={`p-3 rounded-full transition-colors ${
                isDragOver
                  ? 'bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400'
                  : 'bg-slate-100 dark:bg-slate-200/60 text-slate-600 dark:text-slate-400'
              }`}
            >
              <UploadCloud className="w-6 h-6 text-red-600" />
            </div>

            <div>
              <p className="text-xs font-medium text-slate-800 dark:text-slate-200">
                <span className="text-red-600 dark:text-red-500 underline underline-offset-2 font-semibold">
                  Нажмите для загрузки
                </span>{' '}
                или перетащите файлы сюда
              </p>
              <p className="mt-1 text-[11px] text-white dark:text-gray-300">
                {accept ? `Форматы: ${accept.join(', ')}` : 'Любые файлы'}
                {maxSize && ` (до ${(maxSize / (1024 * 1024)).toFixed(0)} МБ)`}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Вывод ошибки валидации */}
      {error && (
        <div className="mt-2 text-xs text-red-500 flex items-center justify-between bg-red-50 dark:bg-red-950/30 p-2 rounded-lg border border-red-200 dark:border-red-900">
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-600 dark:hover:text-red-300"
          >
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
};