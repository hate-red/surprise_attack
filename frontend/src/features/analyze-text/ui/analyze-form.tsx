'use client';

import React from 'react';
import { Card } from '@/shared/ui/card/card';
import { Button } from '@/shared/ui/button/button';
import { Sparkles, Paperclip, Pen } from 'lucide-react';
import { Dropzone } from '@/shared/ui/dropzone/ui/Dropzone';
import { useAnalyzeForm } from '../model/use-analyze-form';
import { FileList } from './file-list';

interface Props {
  sendProductString: (text: string) => void;
  isLoading?: boolean;
}

export const AnalyzeForm: React.FC<Props> = ({ sendProductString, isLoading }) => {
  const {
    text,
    setText,
    files,
    isManualInput,
    handleFilesSelected,
    handleRemoveFile,
    handleSubmit,
    toggleInputMode,
  } = useAnalyzeForm({ sendProductString });

  const maxLength = 2000;
  const currentLength = text?.length || 0;

  return (
    <>
      <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-5">
        Введите название и характеристики товара
      </h2>
      <Card>
        <form onSubmit={handleSubmit}>
          {isManualInput ? (
            <div className="mb-4">
              <textarea
                rows={5}
                maxLength={maxLength}
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="w-full border-2 border-slate-200 dark:border-slate-700 rounded-lg p-3 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:border-[#274a83] dark:focus:border-blue-500 resize-none bg-slate-50/50 dark:bg-slate-900/50 placeholder:text-slate-400 dark:placeholder:text-slate-500"
                placeholder="Ноутбук игровой Acer Nitro 5 Intel Core i5-12500H 15.6 дюймов 512 ГБ 16 ГБ"
              />
              <div className="flex justify-end mt-1">
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
            <Dropzone
              onFilesSelected={handleFilesSelected}
              accept={['image/png', 'image/jpeg', 'application/pdf']}
              maxSize={5 * 1024 * 1024} // 5 MB
              multiple={true}
            />
          )}

          <FileList files={files} onRemove={handleRemoveFile} />

          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={isLoading}
              icon={<Sparkles className="w-4 h-4" />}
              className="w-full cursor-pointer"
            >
              {isLoading ? 'Анализ...' : 'Анализировать'}
            </Button>

            <Button className="cursor-pointer" type="button" onClick={toggleInputMode}>
              {isManualInput ? <Paperclip /> : <Pen />}
            </Button>
          </div>
        </form>
      </Card>
    </>
  );
};