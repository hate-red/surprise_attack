import React from 'react';
import { Edit2, Trash2 } from 'lucide-react';

export interface Characteristic {
  id: string;
  name: string;
  description: string;
  normalized: string;
  unit: string;
  confidence: string;
  isRequired: boolean;
}

interface Props {
  data: Characteristic;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export const CharacteristicRow: React.FC<Props> = ({ data, onEdit, onDelete }) => {
  return (
    <tr className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors border-b border-slate-100 dark:border-slate-800 text-xs">
      <td className="py-3.5 px-6 font-medium text-slate-800 dark:text-slate-200">
        <p className='relative w-fit'>
          {data.name} {data.isRequired && <span className="text-red-500 dark:text-red-400 absolute top-[-10px] right-[-10px]">*</span>}
        </p>
        <div className="text-[10px] text-slate-400 dark:text-slate-500 font-normal">
          Уверенность {data.confidence}
        </div>
      </td>
      <td className="py-3.5 px-6 text-slate-600 dark:text-slate-300">{data.description}</td>
      <td className="py-3.5 px-6 font-semibold text-slate-900 dark:text-slate-100">{data.normalized}</td>
      <td className="py-3.5 px-6 text-slate-500 dark:text-slate-400">{data.unit}</td>
      <td className="py-3.5 px-6 text-right space-x-2">
        {onEdit && (
          <button 
            onClick={() => onEdit(data.id)} 
            className="text-slate-400 hover:text-blue-600 dark:text-slate-500 dark:hover:text-blue-400 cursor-pointer transition-colors"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
        )}
        {onDelete && (
          <button 
            onClick={() => onDelete(data.id)} 
            className="text-slate-400 hover:text-red-600 dark:text-slate-500 dark:hover:text-red-400 cursor-pointer transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </td>
    </tr>
  );
};