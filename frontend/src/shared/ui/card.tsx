import type { ComponentProps } from "react";
import { cn } from "@/shared/lib/cn";

const toneClasses = {
  default: "border-border bg-card",
  warning: "border-amber-500/40 bg-amber-500/10",
} as const;

type CardProps = ComponentProps<"section"> & {
  tone?: keyof typeof toneClasses;
};

export function Card({ tone = "default", className, ...props }: CardProps) {
  return <section className={cn("rounded-xl border", toneClasses[tone], className)} {...props} />;
}
