import { API_BASE_URL, apiUrl, extractErrorDetail } from '@/shared/config/api';
import type { ParseOptions, ParseResponse, ParseResult } from '../model/types';

/**
 * POST /kgru-positions/parse?user_input=...
 * Тело запроса — значения, изменённые/подтверждённые пользователем.
 * Возвращает {ok: true, data} или {ok: false, error} — без исключений для
 * ошибок сервера, чтобы интерфейс всегда мог показать честное сообщение.
 * Отмена запроса (AbortController) пробрасывается как AbortError.
 */
export async function sendProductString(rawString: string, options: ParseOptions = {}): Promise<ParseResult> {
  const url = apiUrl('/kgru-positions/parse');
  url.searchParams.append('user_input', rawString);

  let response: Response;
  try {
    response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        overrides: options.overrides ?? [],
        excluded: options.excluded ?? [],
        selected_code: options.selectedCode ?? null,
      }),
      signal: options.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    return {
      ok: false,
      status: 0,
      error: `Сервер анализа недоступен (${API_BASE_URL}). Проверьте, что backend запущен.`,
    };
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    return {
      ok: false,
      status: response.status,
      error: extractErrorDetail(payload) ?? `Ошибка сервера: ${response.status} ${response.statusText}`,
    };
  }
  if (!payload || typeof payload !== 'object' || !('status' in payload)) {
    return { ok: false, status: response.status, error: 'Сервер вернул ответ в неизвестном формате.' };
  }
  return { ok: true, data: payload as ParseResponse };
}
