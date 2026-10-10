import { ReactNode } from 'react';

export interface DropzoneProps {
  /** Функция, вызываемая при выборе или перетаскивании файлов */
  onFilesSelected: (files: File[]) => void;
  /** Разрешенные типы файлов (например: ['image/png', 'image/jpeg', 'application/pdf']) */
  accept?: string[];
  /** Разрешить выбор нескольких файлов */
  multiple?: boolean;
  /** Максимальный размер файла в байтах */
  maxSize?: number;
  /** Кастомный текст или контент внутри области */
  children?: ReactNode;
  /** Кастомные стили контейнера */
  className?: string;
  /** Отключить область */
  disabled?: boolean;
}