import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";

type SourceMode = "zip" | "git";

export default function NewScan() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<SourceMode>("zip");
  const [file, setFile] = useState<File | null>(null);
  const [gitUrl, setGitUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (mode === "zip" && !file) {
      setError("Please choose a .zip file to upload.");
      return;
    }
    if (mode === "git" && !gitUrl.trim()) {
      setError("Please enter a public git repository URL.");
      return;
    }

    setSubmitting(true);
    try {
      const scan =
        mode === "zip"
          ? await api.createScanFromZip(file as File)
          : await api.createScanFromGit(gitUrl.trim());
      navigate(`/scans/${scan.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(String(err));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="mb-4 text-2xl font-semibold text-gray-900">New Scan</h1>

      <div className="mb-4 flex gap-2">
        <button
          type="button"
          onClick={() => setMode("zip")}
          className={`rounded-md px-3 py-2 text-sm font-medium ${
            mode === "zip"
              ? "bg-gray-900 text-white"
              : "bg-white text-gray-700 ring-1 ring-gray-300 hover:bg-gray-50"
          }`}
        >
          Upload .zip
        </button>
        <button
          type="button"
          onClick={() => setMode("git")}
          className={`rounded-md px-3 py-2 text-sm font-medium ${
            mode === "git"
              ? "bg-gray-900 text-white"
              : "bg-white text-gray-700 ring-1 ring-gray-300 hover:bg-gray-50"
          }`}
        >
          Git URL
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-gray-200 bg-white p-4">
        {mode === "zip" ? (
          <div>
            <label htmlFor="zip-file" className="mb-1 block text-sm font-medium text-gray-700">
              Project archive (.zip, max 50 MB)
            </label>
            <input
              id="zip-file"
              type="file"
              accept=".zip,application/zip"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-gray-700 file:mr-3 file:rounded-md file:border-0 file:bg-gray-900 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-gray-700"
            />
            {file ? (
              <p className="mt-1 text-xs text-gray-500">
                Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            ) : null}
          </div>
        ) : (
          <div>
            <label htmlFor="git-url" className="mb-1 block text-sm font-medium text-gray-700">
              Public git repository URL
            </label>
            <input
              id="git-url"
              type="text"
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-gray-500 focus:outline-none"
            />
          </div>
        )}

        {error ? (
          <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Submitting..." : "Start Scan"}
        </button>
      </form>
    </div>
  );
}
