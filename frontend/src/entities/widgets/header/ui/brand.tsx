import { IconBox } from "@/shared/ui/icon-box";

export function Brand() {
  return (
    <div className="flex w-[256px] items-center gap-3 border-r border-border px-5 max-md:w-auto max-md:gap-2 max-md:border-r-0 max-md:px-4">
      <IconBox
        className="size-9 rounded-[10px] bg-primary text-white shadow-sm max-md:size-[34px]"
        iconSize={21}
        name="sparkles"
      />
      <div>
        <div className="text-[15px] font-bold leading-4 tracking-[-0.01em] text-foreground">SmartСТЕ</div>
        <div className="mt-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground max-md:hidden">
          Интеллектуальный помощник
        </div>
      </div>
    </div>
  );
}
