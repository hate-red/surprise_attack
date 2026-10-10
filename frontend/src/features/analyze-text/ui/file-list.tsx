import React from 'react';
import { FileIcon, X } from 'lucide-react';

interface FileListProps {
  files: File[];
  onRemove: (index: number) => void;
}

export const FileList: React.FC<FileListProps> = ({ files, onRemove }) => {
  if (files.length === 0) return null;

  return (
    <div className="space-y-2 mb-4">
      <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
        Выбранные файлы ({files.length})
      </p>
      <ul className="space-y-2">
        {files.map((file, index) => (
          <li
            key={`${file.name}-${index}`}
            className="flex items-center justify-between p-3 bg-zinc-100 dark:bg-zinc-800/60 rounded-xl text-sm"
          >
            <div className="flex items-center gap-3 overflow-hidden">
              <FileIcon className="w-5 h-5 text-blue-500 shrink-0" />
              <div className="truncate">
                <p className="font-medium text-zinc-800 dark:text-zinc-200 truncate">
                  {file.name}
                </p>
                <p className="text-xs text-zinc-400">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => onRemove(index)}
              className="p-1 text-zinc-400 hover:text-red-500 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-700 transition"
            >
              <X size={16} />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};