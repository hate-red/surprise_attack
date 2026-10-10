import { Card } from "@/shared/ui/card";
import { Icon } from "@/shared/ui/icon/icon";
import { ProgressBar } from "@/shared/ui/progress-bar";

export function QualityCheck() {
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-[12px] font-semibold text-foreground">Проверка качества</h3>
        <span className="text-[10px] font-bold text-emerald-500">5 из 6</span>
      </div>
      <ProgressBar value={83} />
      <div className="mt-3 grid grid-cols-2 gap-2 text-[9px] text-muted-foreground">
        <span className="flex items-center gap-1 text-emerald-500">
          <Icon name="check" size={12} /> Ошибок нет
        </span>
        <span className="flex items-center gap-1">
          <Icon name="search" size={12} /> Опечаток нет
        </span>
      </div>
    </Card>
  );
}
