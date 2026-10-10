import type { ComponentProps } from "react";
import { cn } from "@/shared/lib/cn";

const toneClasses = {
  neutral: "bg-muted text-primary",
  success: "bg-emerald-500/10 text-emerald-500",
} as const;

type BadgeProps = ComponentProps<"span"> & {
  tone?: keyof typeof toneClasses;
};

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn("rounded-full px-2 py-0.5 text-[10px] font-bold", toneClasses[tone], className)}
      {...props}
    />
  );
}
