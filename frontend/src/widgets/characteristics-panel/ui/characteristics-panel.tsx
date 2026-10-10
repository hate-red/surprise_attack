"use client";

import { useState } from "react";
import { characteristics } from "@/entities/characteristic/model/mock-data";
import { CharacteristicRow } from "@/entities/characteristic/ui/characteristic-row";
import { CharacteristicTableHead } from "@/entities/characteristic/ui/characteristic-table-head";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { Icon } from "@/shared/ui/icon/icon";
import { TabButton } from "@/shared/ui/tab-button";

type Tab = "characteristics" | "source";

export function CharacteristicsPanel({ sourceText }: { sourceText: string }) {
  const [activeTab, setActiveTab] = useState<Tab>("characteristics");
  const [removedTitles, setRemovedTitles] = useState<string[]>([]);

  const visibleItems = characteristics.filter((item) => !removedTitles.includes(item.title));

  return (
    <Card className="overflow-hidden shadow-[0_2px_8px_rgba(20,39,75,0.03)] max-md:overflow-x-auto">
      <div className="flex items-center justify-between border-b border-border px-5 pt-4 max-md:sticky max-md:left-0 max-md:min-w-[calc(100vw-30px)] max-md:bg-card">
        <div className="flex gap-6">
          <TabButton active={activeTab === "characteristics"} onClick={() => setActiveTab("characteristics")}>
            Характеристики
            <Badge className="ml-2">{visibleItems.length}</Badge>
          </TabButton>
          <TabButton active={activeTab === "source"} onClick={() => setActiveTab("source")}>
            Исходный текст
          </TabButton>
        </div>
        {activeTab === "characteristics" && (
          <Button
            className="mb-3 gap-1.5 text-[11px] font-medium"
            onClick={() => setRemovedTitles([])}
            size="none"
            variant="link"
          >
            <Icon name="refresh" size={14} />
            Обновить
          </Button>
        )}
      </div>

      {activeTab === "source" ? (
        <SourceText text={sourceText} />
      ) : (
        <>
          <CharacteristicTableHead />
          <div className="max-md:min-w-[680px]">
            {visibleItems.map((item) => (
              <CharacteristicRow
                item={item}
                key={item.title}
                onRemove={() => setRemovedTitles([...removedTitles, item.title])}
              />
            ))}
          </div>
          <Button className="m-4 gap-2 text-[11px] font-semibold" size="none" variant="link">
            <span className="grid size-5 place-items-center rounded-md border border-border">
              <Icon name="plus" size={13} />
            </span>
            Добавить характеристику
          </Button>
        </>
      )}
    </Card>
  );
}

function SourceText({ text }: { text: string }) {
  return (
    <div className="p-5">
      <div className="rounded-xl border border-border bg-background p-5 text-[13px] leading-7 text-muted-foreground">
        {text}
      </div>
      <p className="mt-3 text-[11px] text-muted-foreground">Последний проанализированный вариант описания</p>
    </div>
  );
}
