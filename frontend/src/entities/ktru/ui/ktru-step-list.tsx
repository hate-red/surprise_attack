import { cn } from "@/shared/lib/cn";
import type { KtruStep } from "../model/mock-data";

export function KtruStepList({ steps }: { steps: KtruStep[] }) {
  const lastIndex = steps.length - 1;

  return (
    <ol className="relative ml-1 space-y-4 before:absolute before:bottom-3 before:left-[10px] before:top-3 before:w-px before:bg-border">
      {steps.map((step, index) => (
        <li className="relative flex gap-3" key={step.code}>
          <span
            className={cn(
              "z-10 mt-0.5 grid size-[21px] place-items-center rounded-full border text-[9px] font-bold",
              index === lastIndex
                ? "border-primary bg-primary text-white"
                : "border-border bg-card text-primary",
            )}
          >
            {index + 1}
          </span>
          <div>
            <div className="text-[11px] font-semibold text-foreground">
              {step.code} · {step.title}
            </div>
            <div className="mt-0.5 text-[9px] text-muted-foreground">{step.categoriesCount}</div>
          </div>
        </li>
      ))}
    </ol>
  );
}
