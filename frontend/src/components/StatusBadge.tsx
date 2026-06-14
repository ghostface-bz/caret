import { STATUS_COLOR } from "../lib/ui";
import type { ScanStatus } from "../api/types";

/** Scan status pill — coloured, with a pulsing dot while running. */
export default function StatusBadge({ status }: { status: ScanStatus }) {
  const color = STATUS_COLOR[status];
  return (
    <span
      className="inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-[11.5px] font-semibold capitalize"
      style={{ color, background: `color-mix(in srgb, ${color} 14%, transparent)` }}
    >
      <span
        className={`h-[7px] w-[7px] rounded-full ${status === "running" ? "pulse-dot" : ""}`}
        style={{ background: color }}
      />
      {status}
    </span>
  );
}
