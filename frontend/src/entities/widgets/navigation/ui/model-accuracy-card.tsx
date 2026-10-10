import { IconBox } from "@/shared/ui/icon-box";
import { ProgressBar } from "@/shared/ui/progress-bar";

const ACCURACY = 96.8;

export function ModelAccuracyCard() {
  return (
    <div className="mt-auto rounded-xl bg-gradient-to-br from-secondary to-primary p-4 text-white">
      <IconBox className="mb-3 size-8 rounded-lg bg-card/15" iconSize={18} name="sparkles" />
      <p className="text-xs font-semibold">Точность модели</p>
      <div className="mt-2 flex items-end justify-between">
        <span className="text-2xl font-bold tracking-tight">{ACCURACY.toString().replace(".", ",")}%</span>
        <span className="mb-1 text-[10px] text-white/65">за 30 дней</span>
      </div>
      <ProgressBar
        barClassName="bg-emerald-400"
        className="mt-3"
        trackClassName="bg-card/20"
        value={ACCURACY}
      />
    </div>
  );
}
