"use client";

import { DescriptionForm } from "@/features/describe-product/ui/description-form";
import { useDescriptionAnalysis } from "@/features/describe-product/model/use-description-analysis";
import { useToast } from "@/shared/lib/use-toast";
import { Toast } from "@/shared/ui/toast";
import { CharacteristicsPanel } from "@/widgets/characteristics-panel/ui/characteristics-panel";
import { CompletionBanner } from "@/widgets/completion-banner/ui/completion-banner";
import { KtruPanel } from "@/widgets/ktru-panel/ui/ktru-panel";
import { ClarificationAlert } from "@/widgets/quality-panel/ui/clarification-alert";
import { QualityCheck } from "@/widgets/quality-panel/ui/quality-check";
import { PageHeading } from "./page-heading";

export function SpecificationWorkspace() {
  const { message, showToast } = useToast();
  const analysis = useDescriptionAnalysis(() => showToast("Анализ завершен: найдено 6 характеристик"));

  return (
    <>
      {message && <Toast message={message} />}

      <PageHeading
        onCreateNew={() => analysis.setDescription("")}
        onSaveDraft={() => showToast("Черновик спецификации сохранен")}
      />

      <DescriptionForm
        canAnalyze={analysis.canAnalyze}
        description={analysis.description}
        isAnalyzing={analysis.isAnalyzing}
        onAnalyze={analysis.analyze}
        onChange={analysis.setDescription}
      />

      <div className="mt-5 grid grid-cols-[minmax(0,1.58fr)_minmax(300px,0.82fr)] gap-5 max-md:grid-cols-1">
        <CharacteristicsPanel sourceText={analysis.analyzedDescription} />
        <div className="space-y-5">
          <KtruPanel />
          <ClarificationAlert />
          <QualityCheck />
        </div>
      </div>

      <CompletionBanner />
    </>
  );
}
