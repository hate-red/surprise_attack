export type ResultStatus = 'resolved' | 'need_more_info' | 'low_confidence' | 'name_not_found';

export type RowStatus =
  | 'ok'
  | 'no_constraints'
  | 'invalid'
  | 'unit_mismatch'
  | 'ambiguous'
  | 'no_value'
  | 'ste_only'
  | 'not_applicable'
  | 'unrecognized'
  | 'missing'
  | 'conflict';

export type RowSource = 'text' | 'user' | 'ste' | 'unknown' | 'reference';

export interface CharacteristicRowDto {
  id: string;
  name: string;
  source: RowSource;
  original: string;
  normalized: string;
  unit: string;
  status: RowStatus;
  required: boolean;
  char_type: 'quality' | 'quantity' | 'unknown';
  matched_range: string | null;
  notes: string[];
  suggestions: string[];
  options: string[];
  alternatives: string[];
  confidence: number;
  start: number | null;
  end: number | null;
  in_specification: boolean;
}

export interface StageDto {
  title: string;
  detail: string;
  count_before: number | null;
  count_after: number;
  applied: boolean;
  kind: string;
  note: string | null;
}

export interface CandidateDto {
  code: string;
  name: string;
  okpd2_code: string | null;
  okpd2_name: string | null;
  is_template: boolean;
  matched: number;
  validity_note: string | null;
}

export interface SuggestionDto {
  id: string;
  name: string;
  required: boolean;
  options: { value: string; count: number }[];
  reason: string;
}

export interface MessageDto {
  level: 'success' | 'info' | 'warning' | 'error';
  code: string;
  text: string;
}

export interface SpellingIssueDto {
  original: string;
  suggestion: string;
  start: number;
  end: number;
}

export interface FragmentDto {
  text: string;
  start: number;
  end: number;
  kind: string;
}

export interface ParseResponse {
  status: ResultStatus;
  message: string;
  query: string;
  corrected_query: string | null;
  product: { name: string; names: string[]; confidence: string; matched_text: string } | null;
  ktru_code: string | null;
  ktru_name: string | null;
  final_position: CandidateDto | null;
  characteristics: CharacteristicRowDto[];
  stages: StageDto[];
  candidates: CandidateDto[];
  candidates_total: number;
  suggestions: SuggestionDto[];
  name_refinements: { name: string; count: number }[];
  okpd2_refinements: { code: string; name: string; count: number }[];
  name_alternatives: string[];
  spelling: SpellingIssueDto[];
  unrecognized: FragmentDto[];
  messages: MessageDto[];
  quality: Record<string, number>;
  positions: unknown[];
  timings_ms: Record<string, number>;
}

export interface CharacteristicOverride {
  name: string;
  value: string;
}

export interface ParseOptions {
  overrides?: CharacteristicOverride[];
  excluded?: string[];
  selectedCode?: string | null;
  signal?: AbortSignal;
}

export type ParseResult =
  | { ok: true; data: ParseResponse }
  | { ok: false; status: number; error: string };
