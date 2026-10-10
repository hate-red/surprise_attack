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

  return (
    <>
      <h2 className="text-sm font-bold text-slate-800 mb-5">
        Введите название и характеристики товара
      </h2>
      <Card>
        <form onSubmit={handleSubmit}>
          {isManualInput ? (
            <textarea
              rows={4}
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full  border-3 border-slate-200 rounded-lg p-3 text-xs text-slate-800 focus:outline-none focus:border-[#274a83] resize-none mb-4 bg-slate-50/50"
              placeholder="Введите данные..."
            />
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

            <Button className='cursor-pointer' type="button" onClick={toggleInputMode}>
              {isManualInput ? <Paperclip /> : <Pen />}
            </Button>
          </div>
        </form>
      </Card>
    </>
  );
};