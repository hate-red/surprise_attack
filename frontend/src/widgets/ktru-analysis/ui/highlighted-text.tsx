import React from 'react';

export interface TextHighlight {
  start: number;
  end: number;
  kind: 'typo' | 'characteristic' | 'unrecognized' | 'name';
  title?: string;
}

const STYLES: Record<TextHighlight['kind'], string> = {
  typo: 'underline decoration-wavy decoration-red-500 underline-offset-2 bg-red-50 dark:bg-red-950/40',
  characteristic: 'bg-emerald-100/80 dark:bg-emerald-900/40 rounded-sm',
  name: 'bg-blue-100/80 dark:bg-blue-900/40 rounded-sm',
  unrecognized: 'bg-amber-100/80 dark:bg-amber-900/40 rounded-sm',
};

// при пересечении фрагментов показываем самый важный
const PRIORITY: Record<TextHighlight['kind'], number> = { typo: 3, unrecognized: 2, characteristic: 1, name: 0 };

export const HighlightedText: React.FC<{ text: string; highlights: TextHighlight[] }> = ({ text, highlights }) => {
  const kinds: (TextHighlight | null)[] = Array(text.length).fill(null);
  for (const h of highlights) {
    for (let i = Math.max(0, h.start); i < Math.min(text.length, h.end); i++) {
      const current = kinds[i];
      if (!current || PRIORITY[h.kind] > PRIORITY[current.kind]) kinds[i] = h;
    }
  }
  const parts: React.ReactNode[] = [];
  let i = 0;
  while (i < text.length) {
    const h = kinds[i];
    let j = i + 1;
    while (j < text.length && kinds[j] === h) j++;
    const chunk = text.slice(i, j);
    parts.push(
      h ? (
        <mark key={i} className={`${STYLES[h.kind]} text-inherit`} title={h.title}>
          {chunk}
        </mark>
      ) : (
        <React.Fragment key={i}>{chunk}</React.Fragment>
      ),
    );
    i = j;
  }
  return <>{parts}</>;
};

export const HighlightLegend: React.FC = () => (
  <div className="flex flex-wrap gap-3 text-[10px] text-slate-500 dark:text-slate-400">
    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-blue-100 dark:bg-blue-900/60" /> наименование</span>
    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-emerald-100 dark:bg-emerald-900/60" /> характеристика</span>
    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-amber-100 dark:bg-amber-900/60" /> не распознано</span>
    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-red-100 dark:bg-red-900/60" /> опечатка</span>
  </div>
);
