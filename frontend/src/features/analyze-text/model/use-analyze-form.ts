import { useState } from 'react';

interface UseAnalyzeFormProps {
  sendProductString: (text: string) => void;
}

export const useAnalyzeForm = ({ sendProductString }: UseAnalyzeFormProps) => {
  const [text, setText] = useState('Acer puper truper 20000 rtx 4000');
  const [files, setFiles] = useState<File[]>([]);
  const [isManualInput, setIsManualInput] = useState(true);

  const handleFilesSelected = (newFiles: File[]) => {
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendProductString(text);
  };

  const toggleInputMode = () => {
    setIsManualInput((prev) => !prev);
  };

  return {
    text,
    setText,
    files,
    isManualInput,
    handleFilesSelected,
    handleRemoveFile,
    handleSubmit,
    toggleInputMode,
  };
};