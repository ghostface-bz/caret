import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import { SeveritySummaryInline } from "../components/SeveritySummary";
import type { ScanListItem } from "../api/types";

const POLL_INTERVAL_MS = 2000;

function hasActiveScan(scans: ScanListItem[] | undefined): boolean {
  if (!scans) return false;
  return scans.some((s) => s.status === "queued" || s.status === "running");
}

export default function ScanList() {
  const navigate = useNavigate();
  const { data, error, isLoading, isFetching } = useQuery({
    queryKey: ["scans"],
    queryFn: () => api.listScans(),
    refetchInterval: (query) => (hasActiveScan(query.state.data) ? POLL_INTERVAL_MS : false),
  });

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Scans</h1>
        <Link
          to="/new"
          className="rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-700"
        >
          New Scan
        </Link>
      </div>

      {isLoading ? (
        <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-gray-500">
          Loading scans...
        </div>
      ) : error ? (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error instanceof ApiError
            ? `API unreachable: ${error.message}`
            : `Failed to load scans: ${String(error)}`}
        </div>
      ) : !data || data.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-gray-500">
          No scans yet.{" "}
          <Link to="/new" className="font-medium text-gray-900 underline">
            Start one
          </Link>
          .
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2">Source</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Findings</th>
                <th className="px-4 py-2">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((scan) => (
                <tr
                  key={scan.id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => navigate(`/scans/${scan.id}`)}
                >
                  <td className="px-4 py-3">
                    <Link to={`/scans/${scan.id}`} className="font-medium text-gray-900 hover:underline">
                      {scan.source_type === "git" ? "git: " : "zip: "}
                      {scan.source_ref}
                    </Link>
                    <div className="text-xs text-gray-400">{scan.id}</div>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={scan.status} />
                  </td>
                  <td className="px-4 py-3">
                    <SeveritySummaryInline counts={scan.counts} />
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(scan.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {isFetching && !isLoading ? (
        <p className="mt-2 text-xs text-gray-400">Refreshing...</p>
      ) : null}
    </div>
  );
}
