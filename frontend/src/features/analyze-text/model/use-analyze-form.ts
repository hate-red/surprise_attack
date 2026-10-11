import { useState } from 'react';
import { useAnalyzeStore } from '@/shared/model/use-analyze-store';// Путь к файлу из Шага 1

interface UseAnalyzeFormProps {
  sendProductString: (text: string) => void;
  /** Загрузка CSV-файлов (одна колонка описаний) для пакетной обработки */
  onUploadFiles?: (files: File[]) => Promise<void> | void;
}

export const useAnalyzeForm = ({ sendProductString, onUploadFiles }: UseAnalyzeFormProps) => {
  // 1. Берем текст и метод его изменения из Zustand-стора
  const { text, setText } = useAnalyzeStore();
  
  const [files, setFiles] = useState<File[]>([]);
  const [isManualInput, setIsManualInput] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFilesSelected = (selectedFiles: File[]) => {
    setUploadError(null);
    setFiles((prev) => [...prev, ...selectedFiles]);
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const toggleInputMode = () => {
    setIsManualInput((prev) => !prev);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isManualInput) {
      if (!files.length || !onUploadFiles) return;
      setIsUploading(true);
      setUploadError(null);
      try {
        await onUploadFiles(files);
        setFiles([]);
      } catch (error) {
        setUploadError(error instanceof Error ? error.message : 'Не удалось загрузить файл');
      } finally {
        setIsUploading(false);
      }
      return;
    }
    if (!text.trim()) return;
    
    // Отправляем текст (он берется прямо из стора)
    sendProductString(text);
  };

  return {
    text,
    setText, // передается в textarea для автосохранения в стор
    files,
    isManualInput,
    isUploading,
    uploadError,
    handleFilesSelected,
    handleRemoveFile,
    handleSubmit,
    toggleInputMode,
  };
};
