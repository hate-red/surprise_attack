import { cn } from "@/shared/lib/cn";

type ProgressBarProps = {
  value: number;
  className?: string;
  trackClassName?: string;
  barClassName?: string;
};

export function ProgressBar({ value, className, trackClassName, barClassName }: ProgressBarProps) {
  return (
    <div className={cn("h-1.5 overflow-hidden rounded-full", trackClassName ?? "bg-muted", className)}>
      <div
        className={cn("h-full rounded-full bg-emerald-500", barClassName)}
        style={{ width: `${value}%` }}
      />
    </div>
  );
}
