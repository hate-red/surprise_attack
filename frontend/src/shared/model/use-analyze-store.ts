import { create } from 'zustand';

interface AnalyzeState {
  text: string;
  setText: (text: string) => void;
  clearText: () => void;
}

export const useAnalyzeStore = create<AnalyzeState>((set) => ({
  text: '',
  setText: (text) => set({ text }),
  clearText: () => set({ text: '' }),
}));