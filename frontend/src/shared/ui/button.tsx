import type { ComponentProps } from "react";
import { cn } from "@/shared/lib/cn";

const variantClasses = {
  primary: "bg-primary text-white hover:bg-primary/90",
  outline: "border border-border bg-card text-muted-foreground hover:border-ring",
  inverse: "bg-white text-secondary hover:bg-slate-100",
  link: "text-primary hover:text-primary/80",
  bare: "",
} as const;

const sizeClasses = {
  md: "gap-2 rounded-lg px-4 py-2.5 text-xs font-semibold",
  none: "",
} as const;

export type ButtonProps = ComponentProps<"button"> & {
  variant?: keyof typeof variantClasses;
  size?: keyof typeof sizeClasses;
};

export function Button({
  variant = "primary",
  size = "md",
  className,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center transition",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      type={type}
      {...props}
    />
  );
}
