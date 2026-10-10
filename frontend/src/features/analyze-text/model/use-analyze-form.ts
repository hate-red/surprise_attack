import { useState } from 'react';
import { useAnalyzeStore } from '@/shared/model/use-analyze-store';// Путь к файлу из Шага 1

interface UseAnalyzeFormProps {
  sendProductString: (text: string) => void;
}

export const useAnalyzeForm = ({ sendProductString }: UseAnalyzeFormProps) => {
  // 1. Берем текст и метод его изменения из Zustand-стора
  const { text, setText, clearText } = useAnalyzeStore();
  
  const [files, setFiles] = useState<File[]>([]);
  const [isManualInput, setIsManualInput] = useState<boolean>(true);

  const handleFilesSelected = (selectedFiles: File[]) => {
    setFiles((prev) => [...prev, ...selectedFiles]);
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const toggleInputMode = () => {
    setIsManualInput((prev) => !prev);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    
    // Отправляем текст (он берется прямо из стора)
    sendProductString(text);
    
    // Опционально: можно очистить стор после отправки
    // clearText();
  };

  return {
    text,
    setText, // передается в textarea для автосохранения в стор
    files,
    isManualInput,
    handleFilesSelected,
    handleRemoveFile,
    handleSubmit,
    toggleInputMode,
  };
};