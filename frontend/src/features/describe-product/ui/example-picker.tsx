"use client";

import { useState } from "react";
import { Button } from "@/shared/ui/button";
import { Icon } from "@/shared/ui/icon/icon";
import { descriptionExamples } from "../model/examples";

export function ExamplePicker({ onPick }: { onPick: (example: string) => void }) {
  const [isOpen, setIsOpen] = useState(false);

  function pick(example: string) {
    onPick(example);
    setIsOpen(false);
  }

  return (
    <div className="relative">
      <Button
        className="gap-1.5 text-[11px] font-medium"
        onClick={() => setIsOpen(!isOpen)}
        size="none"
        variant="link"
      >
        Выбрать пример
        <Icon name="chevron" size={14} />
      </Button>
      {isOpen && (
        <div className="absolute right-0 top-7 z-20 w-80 rounded-xl border border-border bg-card p-2 shadow-xl">
          {descriptionExamples.map((example, index) => (
            <Button
              className="w-full flex-col items-start rounded-lg px-3 py-2.5 text-left text-xs leading-5 text-muted-foreground hover:bg-muted"
              key={example}
              onClick={() => pick(example)}
              size="none"
              variant="bare"
            >
              <span className="mb-0.5 font-semibold text-foreground">Пример {index + 1}</span>
              {example}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
