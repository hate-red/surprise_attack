import { create } from 'zustand';
import { sendProductString } from '../api/sendProductString';
import type { CharacteristicOverride, ParseResponse } from './types';

interface AnalysisState {
  /** Ответ backend для analyzedText (null — анализ ещё не выполнялся). */
  result: ParseResponse | null;
  analyzedText: string;
  overrides: CharacteristicOverride[];
  excluded: string[];
  selectedCode: string | null;
  isLoading: boolean;
  error: string | null;

  /** Анализ текста. Новый текст сбрасывает правки пользователя прежнего описания. */
  analyze: (text: string) => Promise<void>;
  /** Повторный анализ текущего описания с текущими правками. */
  refresh: () => Promise<void>;
  setOverride: (name: string, value: string) => Promise<void>;
  removeCharacteristic: (name: string) => Promise<void>;
  selectCandidate: (code: string | null) => Promise<void>;
  /** Готовый результат (например, строки CSV-пакета) без запроса к API. */
  loadResult: (text: string, result: ParseResponse | null) => void;
  reset: () => void;
}

let controller: AbortController | null = null;

export const useAnalysisStore = create<AnalysisState>((set, get) => {
  const run = async (text: string) => {
    controller?.abort();
    const current = new AbortController();
    controller = current;
    set({ isLoading: true, error: null });
    const { overrides, excluded, selectedCode } = get();
    try {
      const response = await sendProductString(text, {
        overrides,
        excluded,
        selectedCode,
        signal: current.signal,
      });
      if (controller !== current) return; // пришёл ответ на устаревший запрос
      if (response.ok) {
        set({ result: response.data, analyzedText: text, isLoading: false, error: null });
      } else {
        set({ isLoading: false, error: response.error });
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return;
      set({ isLoading: false, error: 'Не удалось выполнить анализ.' });
    }
  };

  return {
    result: null,
    analyzedText: '',
    overrides: [],
    excluded: [],
    selectedCode: null,
    isLoading: false,
    error: null,

    analyze: async (text) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      if (trimmed !== get().analyzedText) {
        set({ overrides: [], excluded: [], selectedCode: null });
      }
      await run(trimmed);
    },

    refresh: async () => {
      const { analyzedText } = get();
      if (analyzedText) await run(analyzedText);
    },

    setOverride: async (name, value) => {
      const key = name.trim().toLowerCase();
      set((state) => ({
        overrides: [...state.overrides.filter((o) => o.name.trim().toLowerCase() !== key), { name, value }],
        excluded: state.excluded.filter((e) => e.trim().toLowerCase() !== key),
        selectedCode: null,
      }));
      await get().refresh();
    },

    removeCharacteristic: async (name) => {
      const key = name.trim().toLowerCase();
      set((state) => ({
        overrides: state.overrides.filter((o) => o.name.trim().toLowerCase() !== key),
        excluded: [...state.excluded.filter((e) => e.trim().toLowerCase() !== key), name],
        selectedCode: null,
      }));
      await get().refresh();
    },

    selectCandidate: async (code) => {
      set({ selectedCode: code });
      await get().refresh();
    },

    loadResult: (text, result) => {
      controller?.abort();
      controller = null;
      set({
        result,
        analyzedText: text.trim(),
        overrides: [],
        excluded: [],
        selectedCode: null,
        isLoading: false,
        error: null,
      });
    },

    reset: () => {
      controller?.abort();
      controller = null;
      set({ result: null, analyzedText: '', overrides: [], excluded: [], selectedCode: null, isLoading: false, error: null });
    },
  };
});
