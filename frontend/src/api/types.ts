// Types mirroring docs/API_CONTRACT.md and docs/DATA_MODEL.md exactly.
// Field names are snake_case to match the JSON wire format (frozen contract).

export type SourceType = "zip" | "git";

export type ScanStatus = "queued" | "running" | "completed" | "failed";

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type Tool = "gitleaks" | "semgrep" | "trivy";

export interface SeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  total: number;
}

/** Shape returned by POST /api/scans and as a list item from GET /api/scans */
export interface ScanListItem {
  id: string;
  source_type: SourceType;
  source_ref: string;
  status: ScanStatus;
  created_at: string;
  finished_at: string | null;
  counts: SeverityCounts;
}

/** Shape returned by POST /api/scans (creation response) */
export interface ScanCreateResponse {
  id: string;
  source_type: SourceType;
  source_ref: string;
  status: ScanStatus;
  created_at: string;
}

/** Shape returned by GET /api/scans/{id} — list item + started_at + error */
export interface ScanDetail extends ScanListItem {
  started_at: string | null;
  error: string | null;
}

/** A single finding, as returned by GET /api/scans/{id}/findings */
export interface Finding {
  id: string;
  tool: Tool;
  rule_id: string;
  severity: Severity;
  title: string;
  message: string;
  file_path: string;
  line_start: number | null;
  line_end: number | null;
  cwe: string | null;
  owasp: string | null;
}

/** Optional, combinable query filters for GET /api/scans/{id}/findings */
export interface FindingsQuery {
  severity?: Severity;
  tool?: Tool;
  cwe?: string;
  file?: string;
  q?: string;
}

export interface HealthResponse {
  status: string;
}

export const SEVERITIES: Severity[] = ["critical", "high", "medium", "low", "info"];

export const TOOLS: Tool[] = ["gitleaks", "semgrep", "trivy"];

export function emptyCounts(): SeverityCounts {
  return { critical: 0, high: 0, medium: 0, low: 0, info: 0, total: 0 };
}
