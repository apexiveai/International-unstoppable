"use client";

import Image from "next/image";
import { FormEvent, useCallback, useEffect, useState } from "react";
import API_URL from "@/lib/api";

type Match = {
  match_id: number;
  page: number;
  score: number;
  score_percent: number;
  x: number;
  y: number;
  width: number;
  height: number;
  center_x: number;
  center_y: number;
  radius: number;
  matched_points: number;
};

type AnalysisResult = {
  overall_similarity: number;
  similarity_percent: number;
  matching_area_count: number;
  matched_points: number;
  matches: Match[];
  annotated_original: { page: number; image: string }[];
  original_page_count: number;
  comparison_page_count: number;
  engine: Record<string, unknown>;
};

type CheckSummary = {
  id: number;
  original_filename: string;
  comparison_filename: string;
  similarity_percent: number;
  created_at: string;
};

type CheckDetails = Omit<CheckSummary, "similarity_percent"> & {
  similarity_percent?: number;
  result: AnalysisResult;
};

type CheckHistory = {
  items: CheckSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

const MAX_FILE_SIZE = 20 * 1024 * 1024;

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("apexive_token");
  if (!token) {
    throw new Error("Sign in to use the Trademark Conflict workspace.");
  }
  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // Use the status-based error when the backend response is not JSON.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

export default function TrademarkWorkspace() {
  const [original, setOriginal] = useState<File | null>(null);
  const [comparison, setComparison] = useState<File | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [selectedCheck, setSelectedCheck] = useState<CheckDetails | null>(null);
  const [history, setHistory] = useState<CheckHistory | null>(null);
  const [page, setPage] = useState(1);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  function selectFile(
    file: File | undefined,
    setFile: (file: File | null) => void,
    input: HTMLInputElement,
    label: string,
  ) {
    if (file && file.size > MAX_FILE_SIZE) {
      input.value = "";
      setFile(null);
      setError(`${label} must be 20 MB or smaller.`);
      return;
    }
    setFile(file ?? null);
    setError("");
  }

  const loadHistory = useCallback(async (nextPage: number) => {
    try {
      const data = await request<CheckHistory>(
        `/api/clone-detector/checks?page=${nextPage}`,
      );
      setHistory(data);
      setPage(nextPage);
      setError("");
      return data;
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to load Trademark Conflict history.",
      );
      return null;
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(() => loadHistory(1));
  }, [loadHistory]);

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!original || !comparison) {
      setError("Choose both the original and comparison files.");
      return;
    }
    setAnalyzing(true);
    setError("");
    setSelectedCheck(null);
    setResult(null);
    try {
      const payload = new FormData();
      payload.append("original", original);
      payload.append("comparison", comparison);
      const analysis = await request<AnalysisResult>(
        "/api/clone-detector/analyze",
        { method: "POST", body: payload },
      );
      setResult(analysis);
      setLoadingHistory(true);
      const refreshedHistory = await loadHistory(1);
      const savedCheck = refreshedHistory?.items[0];
      if (savedCheck) {
        setSelectedCheck({ ...savedCheck, result: analysis });
      }
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The conflict check could not be completed.",
      );
    } finally {
      setAnalyzing(false);
    }
  }

  async function openCheck(checkId: number) {
    setError("");
    try {
      const details = await request<CheckDetails>(
        `/api/clone-detector/checks/${checkId}`,
      );
      setSelectedCheck(details);
      setResult(details.result);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to load this conflict check.",
      );
    }
  }

  function downloadReport() {
    if (!result) return;
    const report = {
      generated_at: new Date().toISOString(),
      check_id: selectedCheck?.id ?? null,
      original_filename: selectedCheck?.original_filename ?? original?.name ?? null,
      comparison_filename:
        selectedCheck?.comparison_filename ?? comparison?.name ?? null,
      disclaimer:
        "Visual similarity screening only; not legal advice or a determination of trademark conflict, likelihood of confusion, or registrability.",
      result,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = `trademark-conflict-report-${selectedCheck?.id ?? "new"}.json`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }

  return (
    <section
      id="workspace"
      className="mx-auto grid max-w-7xl gap-8 px-6 py-12 lg:grid-cols-[minmax(0,1.3fr)_minmax(18rem,0.7fr)] lg:px-8"
    >
      <div className="space-y-8">
        <form
          onSubmit={analyze}
          className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
        >
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">
              Trademark Conflict Workspace
            </p>
            <h2 className="mt-2 text-2xl font-bold">New conflict check</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Compare two trademark files for visual similarity. PDF, JPG,
              JPEG, PNG, and WEBP files are supported up to 20 MB each.
            </p>
          </div>

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <label className="block text-sm font-medium text-slate-700">
              Original file
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.webp"
                required
                onChange={(event) =>
                  selectFile(
                    event.target.files?.[0],
                    setOriginal,
                    event.currentTarget,
                    "Original file",
                  )
                }
                className="mt-2 block w-full rounded-xl border border-slate-300 bg-slate-50 p-3 text-sm"
              />
              {original && (
                <span className="mt-2 block truncate text-xs text-slate-500">
                  {original.name}
                </span>
              )}
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Comparison file
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.webp"
                required
                onChange={(event) =>
                  selectFile(
                    event.target.files?.[0],
                    setComparison,
                    event.currentTarget,
                    "Comparison file",
                  )
                }
                className="mt-2 block w-full rounded-xl border border-slate-300 bg-slate-50 p-3 text-sm"
              />
              {comparison && (
                <span className="mt-2 block truncate text-xs text-slate-500">
                  {comparison.name}
                </span>
              )}
            </label>
          </div>

          {error && (
            <p
              role="alert"
              className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
            >
              {error}
            </p>
          )}
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <button
              type="submit"
              disabled={analyzing}
              className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-wait disabled:opacity-60"
            >
              {analyzing ? "Analyzing files..." : "Compare files"}
            </button>
            <p className="text-xs text-slate-500">
              Analysis results and annotated evidence are saved to your
              company&apos;s history. Uploaded source files are not retained.
            </p>
          </div>
        </form>

        {result && (
          <section
            aria-live="polite"
            className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
          >
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {selectedCheck ? `Check #${selectedCheck.id}` : "Analysis result"}
                </p>
                <h2 className="mt-2 text-2xl font-bold">Similarity analysis</h2>
              </div>
              <button
                type="button"
                onClick={downloadReport}
                className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Download report (JSON)
              </button>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <Metric
                label="Visual similarity"
                value={`${result.similarity_percent}%`}
              />
              <Metric
                label="Matching areas"
                value={String(result.matching_area_count)}
              />
              <Metric label="Matched points" value={String(result.matched_points)} />
            </div>

            <div className="mt-8">
              <h3 className="text-lg font-semibold">Visual evidence</h3>
              {result.annotated_original.length ? (
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  {result.annotated_original.map((image) => (
                    <figure
                      key={image.page}
                      className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50"
                    >
                      <Image
                        src={image.image}
                        alt={`Annotated evidence from original page ${image.page}`}
                        width={1200}
                        height={900}
                        unoptimized
                        className="h-auto w-full"
                      />
                      <figcaption className="p-3 text-sm text-slate-600">
                        Original document · page {image.page}
                      </figcaption>
                    </figure>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-500">
                  No annotated visual evidence was returned for this check.
                </p>
              )}
            </div>

            <div className="mt-8">
              <h3 className="text-lg font-semibold">Detected matches</h3>
              {result.matches.length ? (
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full min-w-[30rem] text-left text-sm">
                    <thead className="border-b border-slate-200 text-slate-500">
                      <tr>
                        <th className="py-3 pr-4 font-medium">Match</th>
                        <th className="py-3 pr-4 font-medium">Page</th>
                        <th className="py-3 pr-4 font-medium">Score</th>
                        <th className="py-3 font-medium">Matched points</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.matches.map((match) => (
                        <tr
                          key={match.match_id}
                          className="border-b border-slate-100 last:border-0"
                        >
                          <td className="py-3 pr-4">#{match.match_id}</td>
                          <td className="py-3 pr-4">{match.page}</td>
                          <td className="py-3 pr-4">{match.score_percent}%</td>
                          <td className="py-3">{match.matched_points}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-500">
                  No matching regions were detected.
                </p>
              )}
            </div>
            <p className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
              This visual similarity result is a screening aid only. It does
              not determine legal conflict, likelihood of confusion, or
              trademark registrability.
            </p>
          </section>
        )}
      </div>

      <aside className="h-fit rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Tenant history
          </p>
          <h2 className="mt-2 text-2xl font-bold">Previous checks</h2>
          <p className="mt-2 text-sm text-slate-600">
            History is shared within your company account and isolated from
            other tenants.
          </p>
        </div>

        {loadingHistory ? (
          <p className="mt-6 text-sm text-slate-500">Loading company history...</p>
        ) : history?.items.length ? (
          <>
            <ol className="mt-6 space-y-3">
              {history.items.map((check) => (
                <li key={check.id}>
                  <button
                    type="button"
                    onClick={() => void openCheck(check.id)}
                    className="w-full rounded-xl border border-slate-200 p-4 text-left transition hover:border-blue-300 hover:bg-blue-50/50"
                  >
                    <span className="flex items-center justify-between gap-3">
                      <span className="font-semibold text-slate-900">
                        Check #{check.id}
                      </span>
                      <span className="text-sm font-semibold text-blue-700">
                        {check.similarity_percent}% visual
                      </span>
                    </span>
                    <span className="mt-2 block truncate text-xs text-slate-600">
                      {check.original_filename} vs {check.comparison_filename}
                    </span>
                    <span className="mt-1 block text-xs text-slate-400">
                      {formatDate(check.created_at)}
                    </span>
                  </button>
                </li>
              ))}
            </ol>
            <div className="mt-5 flex items-center justify-between gap-3 text-sm">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => {
                  setLoadingHistory(true);
                  void loadHistory(page - 1);
                }}
                className="rounded-lg border border-slate-300 px-3 py-2 text-slate-700 disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-slate-500">
                Page {page} of {history.pages}
              </span>
              <button
                type="button"
                disabled={page >= history.pages}
                onClick={() => {
                  setLoadingHistory(true);
                  void loadHistory(page + 1);
                }}
                className="rounded-lg border border-slate-300 px-3 py-2 text-slate-700 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </>
        ) : (
          <p className="mt-6 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
            No checks have been saved for this company yet.
          </p>
        )}
      </aside>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
    </div>
  );
}
