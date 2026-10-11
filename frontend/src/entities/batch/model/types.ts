import type { ParseResponse, ResultStatus } from '@/entities/product/model/types';

export type BatchStatus = 'pending' | 'processing' | 'done' | 'error';

export interface Batch {
  id: number;
  filename: string;
  status: BatchStatus;
  total_items: number;
  processed_items: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface BatchItem {
  id: number;
  batch_id: number;
  row_number: number;
  description: string;
  status: BatchStatus;
  result_status: ResultStatus | null;
  ktru_code: string | null;
  candidates_count: number | null;
  error: string | null;
  updated_at: string;
}

export interface BatchDetail extends Batch {
  items: BatchItem[];
}

export interface BatchItemDetail extends BatchItem {
  result: ParseResponse | null;
}
