import type { SeverityCounts } from "../api/types";
import { SEVERITIES } from "../api/types";
import SeverityBadge from "./SeverityBadge";

/** Compact inline summary of severity counts, e.g. for the scan list rows. */
export function SeveritySummaryInline({ counts }: { counts: SeverityCounts }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {SEVERITIES.map((sev) =>
        counts[sev] > 0 ? (
          <span key={sev} className="inline-flex items-center gap-1">
            <SeverityBadge severity={sev} />
            <span className="text-sm text-gray-600">{counts[sev]}</span>
          </span>
        ) : null
      )}
      <span className="text-sm text-gray-400">total: {counts.total}</span>
    </div>
  );
}

/** Larger card-style summary for the scan detail page. */
export function SeveritySummaryCards({ counts }: { counts: SeverityCounts }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-6">
      {SEVERITIES.map((sev) => (
        <div key={sev} className="rounded-lg border border-gray-200 bg-white p-3 text-center">
          <div className="mb-1">
            <SeverityBadge severity={sev} />
          </div>
          <div className="text-2xl font-semibold text-gray-900">{counts[sev]}</div>
        </div>
      ))}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-center">
        <div className="mb-1 text-xs font-medium uppercase text-gray-500">Total</div>
        <div className="text-2xl font-semibold text-gray-900">{counts.total}</div>
      </div>
    </div>
  );
}
