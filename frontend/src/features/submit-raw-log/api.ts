import axios from "axios";

// Создаем инстанс Axios с базовым URL бэкенда
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export interface ValidationError {
  readonly id: string;
  readonly type: "typo" | "mismatch";
  readonly title: string;
  readonly description: string;
}

export interface AnalyzeResponseDto {
  readonly success: boolean;
  readonly errors: readonly ValidationError[];
}

/**
 * Отправляет сырую строку описания товара на бэкенд FastAPI
 */
export async function analyzeProductText(text: string): Promise<readonly ValidationError[]> {
  // Так как бэкенд ждет строку или объект со строкой, 
  // если FastAPI ожидает тело в виде JSON {"text": "строка"}, передаем объект:
  const response = await apiClient.post<AnalyzeResponseDto>("/api/v1/analyze", {
    text,
  });

  return response.data.errors;
}