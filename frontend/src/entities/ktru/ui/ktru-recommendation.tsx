import { IconBox } from "@/shared/ui/icon-box";
import { recommendedKtru } from "../model/mock-data";

export function KtruRecommendation() {
  return (
    <div className="mt-4 rounded-[10px] border border-border bg-accent p-3.5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[9px] font-bold uppercase tracking-[0.06em] text-primary">
            Рекомендуемый код
          </div>
          <div className="mt-1 text-[16px] font-bold tracking-[-0.01em] text-foreground">
            {recommendedKtru.code}
          </div>
        </div>
        <IconBox className="size-8 rounded-lg bg-card text-primary shadow-sm" iconSize={18} name="box" />
      </div>
      <div className="mt-2 text-[11px] leading-4 text-muted-foreground">
        {recommendedKtru.description}
      </div>
      <div className="mt-3 flex items-center justify-between border-t border-border pt-2.5">
        <span className="text-[9px] text-muted-foreground">Соответствие</span>
        <span className="text-[11px] font-bold text-emerald-500">{recommendedKtru.match}%</span>
      </div>
    </div>
  );
}
