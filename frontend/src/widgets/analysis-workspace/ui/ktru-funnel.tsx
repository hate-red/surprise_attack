import React from 'react';
import type { StageDto } from '@/entities/product/model/types';

interface Props {
  stages: StageDto[];
  /** код определён — нижняя ступень зелёная */
  resolved?: boolean;
}

// оттенки фирменного синего: чем ниже ступень, тем насыщеннее
const SHADES = ['#6d8fcb', '#5a7fbf', '#4a70b2', '#3d62a3', '#325694', '#2a4c86', '#244377'];
const MIN_WIDTH = 30; // % ширины воронки для одной позиции

const DETAIL_KINDS = new Set(['name', 'characteristic']);

function formatCount(n: number) {
  return n.toLocaleString('ru-RU');
}

/**
 * Воронка сужения позиций КТРУ: каждая ступень — реальная операция,
 * ширина — логарифм количества позиций после неё.
 */
export const KtruFunnel: React.FC<Props> = ({ stages, resolved }) => {
  if (stages.length === 0) return null;
  const max = Math.max(2, ...stages.map((s) => s.count_before ?? s.count_after));
  const width = (count: number) =>
    count <= 0 ? MIN_WIDTH * 0.6 : MIN_WIDTH + ((100 - MIN_WIDTH) * Math.log(count)) / Math.log(max);

  return (
    <ol className="flex flex-col" aria-label="Сужение позиций КТРУ">
      {stages.map((stage, index) => {
        const top = width(stage.count_before ?? stage.count_after);
        const bottom = width(stage.count_after);
        const isLast = index === stages.length - 1;
        const color = !stage.applied
          ? undefined
          : stage.count_after === 0
            ? '#cc1f14'
            : isLast && resolved
              ? '#059669'
              : SHADES[Math.min(index, SHADES.length - 1)];
        const tooltip = [
          `${stage.title}: ${stage.detail}`,
          stage.count_before !== null && stage.count_before !== stage.count_after
            ? `${formatCount(stage.count_before)} → ${formatCount(stage.count_after)}`
            : `${formatCount(stage.count_after)}`,
          stage.note,
        ]
          .filter(Boolean)
          .join('\n');
        return (
          <li key={`${stage.title}-${index}`} title={tooltip} data-stage={stage.kind}>
            <div
              className={`relative h-8 ${stage.applied ? '' : 'bg-slate-200 dark:bg-slate-700'}`}
              style={{
                backgroundColor: color,
                clipPath: `polygon(${(100 - top) / 2}% 0, ${(100 + top) / 2}% 0, ${(100 + bottom) / 2}% 100%, ${(100 - bottom) / 2}% 100%)`,
              }}
            >
              <span
                className={`absolute inset-0 flex items-center justify-center text-xs font-bold tabular-nums ${
                  stage.applied ? 'text-white' : 'text-slate-500 dark:text-slate-300'
                }`}
              >
                {formatCount(stage.count_after)}
              </span>
            </div>
            <div className={`px-0.5 pt-1 pb-1.5 text-center text-[10px] leading-tight ${stage.applied ? '' : 'opacity-60'}`}>
              <div className="truncate font-semibold text-slate-600 dark:text-slate-300">{stage.title}</div>
              {DETAIL_KINDS.has(stage.kind) && stage.detail ? (
                <div className="truncate text-slate-400 dark:text-slate-500">{stage.detail}</div>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
};