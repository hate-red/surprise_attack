import { create } from "zustand";

// Типы для ошибок и опечаток, возвращаемых ML-сервисом
export interface ValidationError {
  readonly id: string;
  readonly type: "typo" | "mismatch";
  readonly title: string;
  readonly description: string;
  readonly autoFixed?: boolean;
}

// Тип состояния стора
interface KtruState {
  inputText: string;
  isLoading: boolean;
  hasSearched: boolean;
  errors: readonly ValidationError[];

  // Экшены
  setInputText: (text: string) => void;
  analyzeText: () => Promise<void>;
  clearState: () => void;
}

export const useKtruStore = create<KtruState>((set, get) => ({
  inputText:
    "Светильник светодиодный офисный, встраиваемый, 36Вт, 220В, 4000К, корпус аллюминий, белый, IP20.",
  isLoading: false,
  hasSearched: false,
  errors: [],

  setInputText: (text: string): void => set({ inputText: text }),

  analyzeText: async (): Promise<void> => {
    set({ isLoading: true });

    // Пример запроса к FastAPI:
    // const response = await fetch('http://localhost:8000/api/v1/analyze', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ text: get().inputText })
    // });
    // const data: ValidationError[] = await response.json();

    // Имитация ответа от ML с задержкой
    await new Promise((resolve) => setTimeout(resolve, 1200));

    const text: string = get().inputText.toLowerCase();
    const detectedErrors: ValidationError[] = [];

    if (text.includes("аллюминий")) {
      detectedErrors.push({
        id: "1",
        type: "typo",
        title: "Исправлена опечатка",
        description:
          "«аллюминий» → «алюминий». Изменение применено автоматически.",
        autoFixed: true,
      });
    }

    if (text.includes("220v") || text.includes("220в")) {
      detectedErrors.push({
        id: "2",
        type: "mismatch",
        title: "Напряжение противоречит категории",
        description:
          "Значение напряжения требует подтверждения для выбранной категории встраиваемых светильников.",
        autoFixed: false,
      });
    }

    set({
      isLoading: false,
      hasSearched: true,
      errors: detectedErrors,
    });
  },

  clearState: (): void =>
    set({ inputText: "", hasSearched: false, errors: [] }),
}));
