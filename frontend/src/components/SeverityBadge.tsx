import type { Severity } from "../api/types";

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: "bg-purple-100 text-purple-800 border-purple-300",
  high: "bg-red-100 text-red-800 border-red-300",
  medium: "bg-orange-100 text-orange-800 border-orange-300",
  low: "bg-yellow-100 text-yellow-800 border-yellow-300",
  info: "bg-blue-100 text-blue-800 border-blue-300",
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${SEVERITY_STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}
