import { apiUrl, extractErrorDetail } from '@/shared/config/api';
import type { Batch, BatchDetail, BatchItemDetail } from '../model/types';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path).toString(), init);
  } catch {
    throw new Error('Сервер недоступен. Проверьте, что backend запущен.');
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(extractErrorDetail(payload) ?? `Ошибка сервера: ${response.status}`);
  }
  return payload as T;
}

/** Загрузка CSV: содержимое файла уходит телом запроса, имя — параметром. */
export async function uploadBatch(file: File): Promise<Batch> {
  return request<Batch>(`/batches?filename=${encodeURIComponent(file.name)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'text/csv' },
    body: file,
  });
}

export const listBatches = () => request<Batch[]>('/batches?limit=20');

export const getBatch = (batchId: number | string) => request<BatchDetail>(`/batches/${batchId}`);

export const getBatchItem = (batchId: number | string, itemId: number | string) =>
  request<BatchItemDetail>(`/batches/${batchId}/items/${itemId}`);
