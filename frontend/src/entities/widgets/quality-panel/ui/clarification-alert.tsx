import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { Icon } from "@/shared/ui/icon/icon";

export function ClarificationAlert() {
  return (
    <Card className="flex gap-3 p-4" tone="warning">
      <span className="mt-0.5 text-amber-500">
        <Icon name="alert" size={18} />
      </span>
      <div>
        <h3 className="text-[12px] font-semibold text-amber-700">Уточните одну характеристику</h3>
        <p className="mt-1 text-[10px] leading-4 text-amber-600">
          Для полного соответствия КТРУ укажите тип матрицы экрана.
        </p>
        <Button className="mt-2 gap-1 text-[10px] font-bold text-amber-500" size="none" variant="bare">
          Добавить тип матрицы
          <Icon name="arrow" size={12} />
        </Button>
      </div>
    </Card>
  );
}
