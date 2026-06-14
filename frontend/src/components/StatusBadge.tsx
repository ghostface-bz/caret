import type { ScanStatus } from "../api/types";

const STATUS_STYLES: Record<ScanStatus, string> = {
  queued: "bg-gray-100 text-gray-700 border-gray-300",
  running: "bg-blue-100 text-blue-800 border-blue-300 animate-pulse",
  completed: "bg-green-100 text-green-800 border-green-300",
  failed: "bg-red-100 text-red-800 border-red-300",
};

export default function StatusBadge({ status }: { status: ScanStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}
