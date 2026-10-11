/**
 * Адрес backend API. Задаётся переменной окружения NEXT_PUBLIC_API_BASE_URL
 * (например, в frontend/.env.local); по умолчанию — локальный FastAPI.
 */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
).replace(/\/+$/, '');

/** URL эндпоинта; относительный путь сохраняет префикс из API_BASE_URL (http://host/api). */
export function apiUrl(path: string): URL {
  return new URL(path.replace(/^\/+/, ''), `${API_BASE_URL}/`);
}

/** Текст ошибки из ответа FastAPI ({detail: string | [{msg}]}). */
export function extractErrorDetail(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : null))
      .filter(Boolean);
    return messages.length ? messages.join('; ') : null;
  }
  return null;
}
