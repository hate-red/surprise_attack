import type { ComponentProps } from "react";
import { cn } from "@/shared/lib/cn";
import { Button } from "@/shared/ui/button";

type TabButtonProps = ComponentProps<"button"> & {
  active: boolean;
};

export function TabButton({ active, className, ...props }: TabButtonProps) {
  return (
    <Button
      className={cn(
        "border-b-2 pb-3 text-xs font-semibold",
        active ? "border-primary text-primary" : "border-transparent text-muted-foreground",
        className,
      )}
      size="none"
      variant="bare"
      {...props}
    />
  );
}
