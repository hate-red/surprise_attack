import { Button } from "@/shared/ui/button";
import { Icon } from "@/shared/ui/icon/icon";

export function UserMenu() {
  return (
    <Button className="gap-2.5" size="none" variant="bare">
      <span className="grid size-8 place-items-center rounded-full bg-muted text-xs font-bold text-primary">
        АИ
      </span>
      <span className="text-left max-md:hidden">
        <span className="block text-xs font-semibold text-foreground">Алексей Иванов</span>
        <span className="block text-[10px] text-muted-foreground">Поставщик</span>
      </span>
      <span className="max-md:hidden">
        <Icon name="chevron" size={16} />
      </span>
    </Button>
  );
}
