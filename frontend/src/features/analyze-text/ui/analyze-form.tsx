'use client';

import React from 'react';
import { Card } from '@/shared/ui/card/card';
import { Button } from '@/shared/ui/button/button';
import { Sparkles, Paperclip, Pen, Upload } from 'lucide-react';
import { Dropzone } from '@/shared/ui/dropzone/ui/Dropzone';
import { useAnalyzeForm } from '../model/use-analyze-form';
import { FileList } from './file-list';

interface Props {
  sendProductString: (text: string) => void;
  isLoading?: boolean;
  /** Если передан — доступен режим загрузки CSV (кнопка со скрепкой) */
  onUploadFiles?: (files: File[]) => Promise<void> | void;
  title?: string;
}

export const AnalyzeForm: React.FC<Props> = ({
  sendProductString,
  isLoading,
  onUploadFiles,
  title = 'Введите название и характеристики товара',
}) => {
  const {
    text,
    setText,
    files,
    isManualInput,
    isUploading,
    uploadError,
    handleFilesSelected,
    handleRemoveFile,
    handleSubmit,
    toggleInputMode,
  } = useAnalyzeForm({ sendProductString, onUploadFiles });

  const maxLength = 2000;
  const currentLength = text?.length || 0;
  const canSubmit = isManualInput ? currentLength >= 3 && !isLoading : files.length > 0 && !isUploading;

  return (
    <>
      <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-5">
        {isManualInput ? title : 'Загрузите CSV с описаниями товаров'}
      </h2>
      <Card>
        <form onSubmit={handleSubmit}>
          {isManualInput ? (
            <div className="mb-2 relative">
              <textarea
                spellCheck={true}          
                rows={5}
                maxLength={maxLength}
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && canSubmit) {
                    e.preventDefault();
                    sendProductString(text);
                  }
                }}
                className="h-[160px] w-full border-2 border-slate-200 dark:border-slate-700 rounded-lg p-3 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:border-[#274a83] dark:focus:border-blue-500 resize-none bg-slate-50/50 dark:bg-slate-900/50 placeholder:text-slate-400 dark:placeholder:text-slate-500"
                placeholder="Стул ученический деревянный с регулировкой по высоте, ростовая группа 4"
              />
              <div className="flex justify-end mt-1 absolute bottom-2 right-2">
                <span className={`text-[10px] font-medium ${
                  currentLength >= maxLength 
                    ? 'text-red-500 font-bold' 
                    : 'text-slate-400 dark:text-slate-500'
                }`}>
                  {currentLength} / {maxLength}
                </span>
              </div>
            </div>
          ) : (
            <>
              <Dropzone
                onFilesSelected={handleFilesSelected}
                accept={['.csv', 'text/csv', 'application/vnd.ms-excel']}
                maxSize={5 * 1024 * 1024} // 5 MB
                multiple={true}
              />
              <p className="-mt-2 mb-3 text-[11px] text-slate-500 dark:text-slate-400">
                Одна колонка — одно описание товара. Каждая строка будет обработана, статус появится в панели ниже.
              </p>
            </>
          )}

          {!isManualInput ? <FileList files={files} onRemove={handleRemoveFile} /> : null}
          {uploadError ? <p className="mb-3 text-xs text-red-500">{uploadError}</p> : null}

          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={!canSubmit}
              icon={isManualInput ? <Sparkles className="w-4 h-4" /> : <Upload className="w-4 h-4" />}
              className="w-full cursor-pointer"
            >
              {isManualInput
                ? (isLoading ? 'Анализ...' : 'Анализировать')
                : (isUploading ? 'Загрузка...' : 'Загрузить CSV')}
            </Button>

            {onUploadFiles ? (
              <Button
                className="cursor-pointer"
                type="button"
                onClick={toggleInputMode}
                title={isManualInput ? 'Загрузить CSV с описаниями' : 'Ввести описание вручную'}
              >
                {isManualInput ? <Paperclip /> : <Pen />}
              </Button>
            ) : null}
          </div>
        </form>
      </Card>
    </>
  );
};
