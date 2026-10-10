import { Button } from "@/shared/ui/button";
import { Icon } from "@/shared/ui/icon/icon";
import { IconBox } from "@/shared/ui/icon-box";

export function CompletionBanner() {
  return (
    <div className="mt-5 flex items-center justify-between rounded-xl bg-secondary px-5 py-4 text-white max-md:flex-col max-md:items-stretch max-md:gap-4">
      <div className="flex items-center gap-3">
        <IconBox className="size-9 rounded-lg bg-card/10" iconSize={19} name="check" />
        <div>
          <div className="text-xs font-semibold">Спецификация готова на 83%</div>
          <div className="mt-0.5 text-[10px] text-white/60">
            Заполните одну характеристику, чтобы завершить создание
          </div>
        </div>
      </div>
      <Button className="text-[11px] font-bold" variant="inverse">
        Перейти к созданию СТЕ
        <Icon name="arrow" size={15} />
      </Button>
    </div>
  );
}
