import type { ScanStatus, Severity, SeverityCounts, TriageStatus } from "../api/types";

/* All colours are CSS variables (defined per-theme in index.css) so inline
   styles follow the active light/dark theme. */

export const SEV_COLOR: Record<Severity, string> = {
  critical: "var(--sev-crit)",
  high: "var(--sev-high)",
  medium: "var(--sev-med)",
  low: "var(--sev-low)",
  info: "var(--info)",
};
export const SEV_BG: Record<Severity, string> = {
  critical: "var(--sev-crit-bg)",
  high: "var(--sev-high-bg)",
  medium: "var(--sev-med-bg)",
  low: "var(--sev-low-bg)",
  info: "var(--info-bg)",
};
export const SEV_BD: Record<Severity, string> = {
  critical: "var(--sev-crit-bd)",
  high: "var(--sev-high-bd)",
  medium: "var(--sev-med-bd)",
  low: "var(--sev-low-bd)",
  info: "var(--info-bg)",
};
export const SEV_GLOW: Record<Severity, string> = {
  critical: "color-mix(in srgb, var(--sev-crit) 55%, transparent)",
  high: "color-mix(in srgb, var(--sev-high) 55%, transparent)",
  medium: "color-mix(in srgb, var(--sev-med) 55%, transparent)",
  low: "color-mix(in srgb, var(--sev-low) 55%, transparent)",
  info: "transparent",
};

export const STATUS_COLOR: Record<ScanStatus, string> = {
  queued: "var(--tx-faint)",
  running: "var(--sev-low)",
  completed: "var(--ok)",
  failed: "var(--sev-crit)",
};

export const TRIAGE_PILL: Record<TriageStatus, { c: string; bg: string }> = {
  open: { c: "var(--tx)", bg: "var(--st-open-bg)" },
  false_positive: { c: "var(--info)", bg: "var(--info-bg)" },
  resolved: { c: "var(--ok)", bg: "var(--ok-bg)" },
  suppressed: { c: "var(--sev-med)", bg: "var(--sev-med-bg)" },
};

export const CAT_PALETTE = [
  "var(--sev-crit)", "var(--accent)", "var(--sev-med)", "var(--sev-low)",
  "var(--sev-high)", "var(--c-teal)", "var(--c-violet)", "var(--tx-fainter)",
];

/** Weighted posture score (0–100) + letter grade, derived from severity counts. */
export function posture(counts: SeverityCounts): { score: number; grade: string } {
  const penalty = counts.critical * 16 + counts.high * 7 + counts.medium * 3 + counts.low * 1;
  const score = Math.max(0, Math.min(100, 100 - penalty));
  const grade = score >= 90 ? "A" : score >= 75 ? "B" : score >= 60 ? "C" : score >= 40 ? "D" : "F";
  return { score, grade };
}

const CWE_CATEGORY: Record<string, string> = {
  "CWE-89": "Injection", "CWE-78": "Injection", "CWE-77": "Injection", "CWE-94": "Injection",
  "CWE-79": "XSS", "CWE-80": "XSS",
  "CWE-798": "Secrets", "CWE-259": "Secrets", "CWE-321": "Secrets", "CWE-522": "Secrets",
  "CWE-22": "Path Traversal", "CWE-23": "Path Traversal",
  "CWE-327": "Cryptography", "CWE-328": "Cryptography", "CWE-326": "Cryptography", "CWE-916": "Cryptography",
  "CWE-502": "Deserialization",
  "CWE-209": "Info Leak", "CWE-200": "Info Leak", "CWE-532": "Info Leak",
  "CWE-770": "Misconfig", "CWE-16": "Misconfig", "CWE-489": "Misconfig", "CWE-668": "Misconfig",
  "CWE-352": "CSRF", "CWE-601": "Open Redirect", "CWE-918": "SSRF", "CWE-611": "XXE",
  "CWE-287": "Auth", "CWE-306": "Auth", "CWE-863": "Authz", "CWE-862": "Authz",
  "CWE-20": "Validation", "CWE-400": "DoS", "CWE-1333": "DoS",
};

export function categoryOf(f: { cwe: string | null; tool: string }): string {
  if (f.cwe && CWE_CATEGORY[f.cwe]) return CWE_CATEGORY[f.cwe];
  return f.tool === "gitleaks" ? "Secrets" : f.tool === "trivy" ? "Dependencies" : "Other";
}

export function relativeTime(iso: string | null): string {
  if (!iso) return "—";
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}
