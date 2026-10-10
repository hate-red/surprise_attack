import type { ComponentProps } from "react";
import { cn } from "@/shared/lib/cn";

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "w-full resize-none rounded-[10px] border border-border bg-background px-4 py-3",
        "text-[13px] leading-[1.65] text-foreground outline-none transition",
        "placeholder:text-muted-foreground focus:border-ring focus:bg-card focus:ring-3 focus:ring-ring/20",
        className,
      )}
      {...props}
    />
  );
}
