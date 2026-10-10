"use client";

import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { Icon } from "@/shared/ui/icon/icon";
import { IconBox } from "@/shared/ui/icon-box";
import { Textarea } from "@/shared/ui/textarea";
import { MAX_DESCRIPTION_LENGTH } from "../model/examples";
import { ExamplePicker } from "./example-picker";

type DescriptionFormProps = {
  description: string;
  isAnalyzing: boolean;
  canAnalyze: boolean;
  onChange: (value: string) => void;
  onAnalyze: () => void;
};

export function DescriptionForm({
  description,
  isAnalyzing,
  canAnalyze,
  onChange,
  onAnalyze,
}: DescriptionFormProps) {
  return (
    <Card className="p-5 shadow-[0_2px_8px_rgba(20,39,75,0.03)]">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <IconBox className="size-7 rounded-lg bg-muted text-primary" iconSize={15} name="edit" />
          <h2 className="text-sm font-semibold text-foreground">Описание товара</h2>
        </div>
        <ExamplePicker onPick={onChange} />
      </div>

      <div className="relative">
        <Textarea
          className="h-[92px] max-md:h-[132px]"
          maxLength={MAX_DESCRIPTION_LENGTH}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Например: Ноутбук, экран 15.6 дюймов, 16 ГБ ОЗУ, SSD 512 ГБ..."
          value={description}
        />
        <span className="absolute bottom-3 right-3 text-[10px] text-muted-foreground">
          {description.length} / {MAX_DESCRIPTION_LENGTH}
        </span>
      </div>

      <div className="mt-3 flex items-center justify-between max-md:flex-col max-md:items-stretch max-md:gap-3">
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground max-md:items-start max-md:leading-[1.5]">
          <IconBox className="size-5 rounded-full bg-muted text-primary" iconSize={12} name="sparkles" />
          Чем точнее описание, тем выше качество подбора КТРУ
        </div>
        <Button
          className="min-w-40 px-5 max-md:min-h-[42px] max-md:w-full"
          disabled={!canAnalyze}
          onClick={onAnalyze}
        >
          <Icon name={isAnalyzing ? "refresh" : "sparkles"} size={16} />
          {isAnalyzing ? "Анализируем..." : "Анализировать"}
        </Button>
      </div>
    </Card>
  );
}
