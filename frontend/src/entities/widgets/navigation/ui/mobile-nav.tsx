import { cn } from "@/shared/lib/cn";
import { Button } from "@/shared/ui/button";
import { IconBox } from "@/shared/ui/icon-box";
import { navigationItems } from "../model/navigation-items";

type MobileNavProps = {
  activeId: string;
  onSelect: (id: string) => void;
};

export function MobileNav({ activeId, onSelect }: MobileNavProps) {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-50 hidden h-[66px] items-center justify-around border-t border-border bg-card px-2 shadow-[0_-5px_20px_rgba(26,48,83,0.08)] max-md:flex">
      {navigationItems.map((item) => {
        const isActive = item.id === activeId;

        return (
          <Button
            className={cn(
              "min-w-16 flex-col gap-1 text-[9px] font-semibold",
              isActive ? "text-primary" : "text-muted-foreground",
            )}
            key={item.id}
            onClick={() => onSelect(item.id)}
            size="none"
            variant="bare"
          >
            <IconBox
              className={cn("h-8 w-10 rounded-lg", isActive && "bg-muted")}
              iconSize={18}
              name={item.icon}
            />
            {item.shortLabel}
          </Button>
        );
      })}
    </nav>
  );
}
