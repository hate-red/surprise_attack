import { ThemeSwitcher } from "@/features/theme-switcher/ui/theme-switcher";
import { Button } from "@/shared/ui/button";
import { Icon } from "@/shared/ui/icon/icon";
import { Brand } from "./brand";
import { Breadcrumbs } from "./breadcrumbs";
import { UserMenu } from "./user-menu";

export function Header() {
  return (
    <header className="fixed inset-x-0 top-0 z-40 flex h-16 items-center border-b border-border bg-card max-md:h-[60px]">
      <Brand />
      <div className="flex flex-1 items-center justify-between px-7 max-md:justify-end max-md:pl-0 max-md:pr-[15px]">
        <Breadcrumbs />
        <div className="flex items-center gap-4 max-md:gap-3">
          <ThemeSwitcher />
          <Button
            aria-label="Уведомления"
            className="relative text-muted-foreground hover:text-primary"
            size="none"
            variant="bare"
          >
            <Icon name="bell" size={21} />
            <span className="absolute -right-0.5 -top-0.5 size-2 rounded-full border-2 border-card bg-destructive" />
          </Button>
          <div className="h-7 w-px bg-border max-md:hidden" />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
