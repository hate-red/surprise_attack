import { ktruSteps } from "@/entities/ktru/model/mock-data";
import { KtruRecommendation } from "@/entities/ktru/ui/ktru-recommendation";
import { KtruStepList } from "@/entities/ktru/ui/ktru-step-list";
import { Badge } from "@/shared/ui/badge";
import { Card } from "@/shared/ui/card";

export function KtruPanel() {
  return (
    <Card className="p-5 shadow-[0_2px_8px_rgba(20,39,75,0.03)]">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-foreground">Подбор КТРУ</h2>
        <Badge className="px-2.5 py-1 text-[9px] uppercase tracking-[0.05em]" tone="success">
          Сужение завершено
        </Badge>
      </div>
      <KtruStepList steps={ktruSteps} />
      <KtruRecommendation />
    </Card>
  );
}
