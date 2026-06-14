import { SEV_COLOR, SEV_BG, SEV_BD } from "../lib/ui";
import type { Severity } from "../api/types";

/** Severity marker. `dot` = inline dot+label (tables); `pill` = bordered chip. */
export default function SeverityBadge({
  severity,
  variant = "dot",
}: {
  severity: Severity;
  variant?: "dot" | "pill";
}) {
  if (variant === "pill") {
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-bold uppercase tracking-wide"
        style={{ color: SEV_COLOR[severity], background: SEV_BG[severity], borderColor: SEV_BD[severity] }}
      >
        <span className="h-[7px] w-[7px] rounded-full" style={{ background: SEV_COLOR[severity] }} />
        {severity}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-2">
      <span className="h-2 w-2 rounded-full" style={{ background: SEV_COLOR[severity] }} />
      <span className="text-[12.5px] font-semibold capitalize" style={{ color: SEV_COLOR[severity] }}>
        {severity}
      </span>
    </span>
  );
}
