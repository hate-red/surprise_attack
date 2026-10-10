import { Button } from "@/shared/ui/button";
import { Icon } from "@/shared/ui/icon/icon";
import type { Characteristic } from "../model/types";
import { characteristicGridClass } from "./characteristic-grid";

type CharacteristicRowProps = {
  item: Characteristic;
  onRemove: () => void;
};

export function CharacteristicRow({ item, onRemove }: CharacteristicRowProps) {
  return (
    <div
      className={`${characteristicGridClass} group items-center border-t border-border px-5 py-3 first:border-t-0`}
    >
      <div className="pr-3">
        <div className="text-[12px] font-semibold text-foreground">{item.title}</div>
        <div className="mt-1 flex items-center gap-1 text-[9px] font-semibold text-emerald-500">
          <Icon name="check" size={11} />
          Уверенность {item.confidence}%
        </div>
      </div>
      <span className="pr-3 text-[11px] text-muted-foreground">{item.original}</span>
      <span className="pr-3 text-[12px] font-semibold text-foreground">{item.normalized}</span>
      <span className="text-[11px] text-muted-foreground">{item.unit}</span>
      <div className="flex items-center gap-1 opacity-30 transition group-hover:opacity-100">
        <Button
          aria-label={`Редактировать ${item.title}`}
          className="p-1 text-muted-foreground hover:text-primary"
          size="none"
          variant="bare"
        >
          <Icon name="edit" size={14} />
        </Button>
        <Button
          aria-label={`Удалить ${item.title}`}
          className="p-1 text-muted-foreground hover:text-destructive"
          onClick={onRemove}
          size="none"
          variant="bare"
        >
          <Icon name="trash" size={14} />
        </Button>
      </div>
    </div>
  );
}
