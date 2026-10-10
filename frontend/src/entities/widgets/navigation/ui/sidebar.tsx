import { cn } from "@/shared/lib/cn";
import { Button } from "@/shared/ui/button";
import { Icon } from "@/shared/ui/icon/icon";
import { navigationItems } from "../model/navigation-items";
import { ModelAccuracyCard } from "./model-accuracy-card";

const itemClass = "w-full justify-start gap-3 rounded-[9px] px-3 py-2.5 text-left text-[13px] font-medium";

type SidebarProps = {
  activeId: string;
  onSelect: (id: string) => void;
};

export function Sidebar({ activeId, onSelect }: SidebarProps) {
  return (
    <aside className="fixed bottom-0 left-0 top-16 z-30 flex w-[256px] flex-col border-r border-border bg-card p-3 max-md:hidden">
      <nav className="space-y-1">
        {navigationItems.map((item) => (
          <Button
            className={cn(
              itemClass,
              item.id === activeId
                ? "bg-muted text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
            key={item.id}
            onClick={() => onSelect(item.id)}
            size="none"
            variant="bare"
          >
            <Icon name={item.icon} size={19} />
            {item.label}
          </Button>
        ))}
      </nav>

      <div className="mt-6 border-t border-border pt-4">
        <Button className={cn(itemClass, "text-muted-foreground hover:bg-muted")} size="none" variant="bare">
          <Icon name="help" size={19} />
          Центр помощи
        </Button>
      </div>

      <ModelAccuracyCard />
    </aside>
  );
}
