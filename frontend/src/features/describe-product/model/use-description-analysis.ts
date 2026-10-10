"use client";

import { useState } from "react";
import { defaultDescription } from "./examples";

const ANALYSIS_DELAY_MS = 700;

export function useDescriptionAnalysis(onAnalyzed: () => void) {
  const [description, setDescription] = useState(defaultDescription);
  const [analyzedDescription, setAnalyzedDescription] = useState(defaultDescription);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const canAnalyze = description.trim() !== "" && !isAnalyzing;

  function analyze() {
    if (!canAnalyze) return;
    setIsAnalyzing(true);
    window.setTimeout(() => {
      setAnalyzedDescription(description);
      setIsAnalyzing(false);
      onAnalyzed();
    }, ANALYSIS_DELAY_MS);
  }

  return {
    description,
    setDescription,
    analyzedDescription,
    isAnalyzing,
    canAnalyze,
    analyze,
  };
}
