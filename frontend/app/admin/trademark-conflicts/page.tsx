"use client";

import { FormEvent, useEffect, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowLeft,
  ArrowUpRight,
  Building2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  FileSearch,
  RefreshCw,
  Search,
  ShieldCheck,
} from "lucide-react";

import TrademarkProductLaunchButton from "@/components/TrademarkProductLaunchButton";
import {
  getAdminTrademarkConflicts,
  type AdminTrademarkConflictResponse,
} from "@/lib/admin";

const emptyResponse: AdminTrademarkConflictResponse = {
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  pages: 0,
  summary: {
    total_checks: 0,
    checks_last_24h: 0,
    workspaces_with_checks: 0,
  },
};

function subscribeAdminRole(listener: () => void) {
  window.addEventListener("storage", listener);
  return () => window.removeEventListener("storage", listener);
}

function getAdminRoleSnapshot() {
  try {
    const rawUser = localStorage.getItem("apexive_user");
    return rawUser
      ? Boolean((JSON.parse(rawUser) as { is_admin?: boolean }).is_admin)
      : false;
  } catch {
    return false;
  }
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function similarityTone(value: number | null) {
  if (value === null) return "text-slate-400";
  if (value >= 70) return "text-rose-300";
  if (value >= 35) return "text-amber-300";
  return "text-cyan-200";
}

export default function TrademarkConflictAdminPage() {
  const router = useRouter();
  const isAdmin = useSyncExternalStore(
    subscribeAdminRole,
    getAdminRoleSnapshot,
    () => false,
  );
  const [response, setResponse] = useState(emptyResponse);
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [refreshId, setRefreshId] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAdmin) router.replace("/");
  }, [isAdmin, router]);

  useEffect(() => {
    if (!isAdmin) return;
    let current = true;
    getAdminTrademarkConflicts(page, activeSearch)
      .then((result) => {
        if (current) setResponse(result);
      })
      .catch((reason: unknown) => {
        if (current) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Unable to load trademark checks.",
          );
        }
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => {
      current = false;
    };
  }, [activeSearch, isAdmin, page, refreshId]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setPage(1);
    setActiveSearch(searchInput.trim());
    setRefreshId((value) => value + 1);
  }

  if (!isAdmin) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#070b12] text-cyan-100">
        <span className="animate-pulse text-xs font-bold uppercase tracking-[0.24em]">
          Verifying access
        </span>
      </main>
    );
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#070b12] text-slate-100">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 bg-cover bg-center opacity-30"
        style={{
          backgroundImage:
            "linear-gradient(90deg, #070b12 4%, rgba(7,11,18,.78) 48%, #070b12 100%), linear-gradient(0deg, #070b12 2%, transparent 68%), url('https://images.unsplash.com/photo-1519608487953-e999c86e7455?auto=format&fit=crop&w=2200&q=85')",
        }}
      />
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 opacity-[0.08]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(90,220,255,.45) 1px, transparent 1px), linear-gradient(90deg, rgba(90,220,255,.35) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          maskImage: "linear-gradient(to bottom, black, transparent 78%)",
        }}
      />

      <div className="relative mx-auto max-w-[1440px] px-4 py-5 sm:px-7 lg:px-10 lg:py-8">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-5">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center border border-cyan-300/30 bg-cyan-300/10 text-cyan-200">
              <ShieldCheck className="size-5" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-white">Apexive AI</p>
              <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-200/70">Operations / Trademark</p>
            </div>
          </div>
          <nav aria-label="Admin navigation" className="flex flex-wrap items-center gap-2">
            <Link href="/admin" className="inline-flex items-center gap-2 border border-white/15 px-3 py-2 text-xs font-semibold text-slate-300 transition hover:border-cyan-200/50 hover:text-white">
              <ArrowLeft className="size-4" /> Admin console
            </Link>
            <Link href="/trademark-intelligence" className="inline-flex items-center gap-2 border border-white/15 px-3 py-2 text-xs font-semibold text-slate-300 transition hover:border-cyan-200/50 hover:text-white">
              Product workspace <ArrowUpRight className="size-4" />
            </Link>
          </nav>
        </header>

        <section className="grid gap-7 border-b border-white/10 py-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end lg:py-12">
          <div className="max-w-3xl">
            <p className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-cyan-200">
              <span className="size-1.5 bg-cyan-300 shadow-[0_0_14px_2px_rgba(103,232,249,.8)]" />
              System online <span className="text-white/30">/</span> Detector linked
            </p>
            <h1 className="mt-4 text-3xl font-semibold leading-tight text-white sm:text-4xl">
              Trademark conflict <span className="text-cyan-200">operations</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300/80">
              Monitor submitted comparisons across Apexive workspaces and open the connected detector with administrator access.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <TrademarkProductLaunchButton />
          </div>
        </section>

        <section aria-label="Trademark activity summary" className="grid gap-px border border-white/10 bg-white/10 sm:grid-cols-3">
          <div className="bg-[#0a111b]/95 p-5 sm:p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Total comparisons</span>
              <FileSearch className="size-4 text-cyan-200" />
            </div>
            <p className="mt-4 font-mono text-3xl text-white">{response.summary.total_checks.toLocaleString()}</p>
            <p className="mt-2 text-xs text-slate-500">Across all Apexive workspaces</p>
          </div>
          <div className="bg-[#0a111b]/95 p-5 sm:p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Last 24 hours</span>
              <Activity className="size-4 text-fuchsia-200" />
            </div>
            <p className="mt-4 font-mono text-3xl text-white">{response.summary.checks_last_24h.toLocaleString()}</p>
            <p className="mt-2 text-xs text-slate-500">New comparisons recorded</p>
          </div>
          <div className="bg-[#0a111b]/95 p-5 sm:p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Workspaces</span>
              <Building2 className="size-4 text-amber-200" />
            </div>
            <p className="mt-4 font-mono text-3xl text-white">{response.summary.workspaces_with_checks.toLocaleString()}</p>
            <p className="mt-2 text-xs text-slate-500">With at least one comparison</p>
          </div>
        </section>

        <section className="mt-8 border border-white/10 bg-[#0a111b]/95">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 px-4 py-4 sm:px-6">
            <div>
              <h2 className="text-base font-semibold text-white">Comparison activity</h2>
              <p className="mt-1 text-xs text-slate-500">Customer and file metadata only. Comparison evidence remains in the detector workspace.</p>
            </div>
            <div className="flex w-full flex-wrap gap-2 sm:w-auto">
              <form onSubmit={submitSearch} className="flex min-w-0 flex-1 sm:w-80 sm:flex-none">
                <label htmlFor="trademark-search" className="sr-only">Search checks, workspaces, or users</label>
                <div className="flex min-w-0 flex-1 items-center border border-white/15 bg-black/20 px-3 focus-within:border-cyan-200/60">
                  <Search className="size-4 shrink-0 text-slate-500" />
                  <input
                    id="trademark-search"
                    value={searchInput}
                    onChange={(event) => setSearchInput(event.target.value)}
                    placeholder="Search checks or customers"
                    className="min-w-0 flex-1 bg-transparent px-2 py-2.5 text-sm text-white outline-none placeholder:text-slate-600"
                  />
                </div>
                <button type="submit" className="border border-l-0 border-cyan-200/30 bg-cyan-200/10 px-3 text-xs font-bold text-cyan-100 transition hover:bg-cyan-200/20">Search</button>
              </form>
              <button
                type="button"
                onClick={() => {
                  setLoading(true);
                  setError("");
                  setRefreshId((value) => value + 1);
                }}
                aria-label="Refresh comparisons"
                title="Refresh comparisons"
                className="grid size-10 shrink-0 place-items-center border border-white/15 text-slate-300 transition hover:border-cyan-200/50 hover:text-cyan-100 disabled:opacity-50"
                disabled={loading}
              >
                <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {error && <p role="alert" className="border-b border-rose-300/20 bg-rose-400/10 px-5 py-3 text-sm text-rose-200">{error}</p>}

          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-left">
              <thead className="bg-white/[0.025] text-[10px] uppercase tracking-[0.15em] text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Comparison</th>
                  <th className="px-5 py-3 font-semibold">Workspace / submitted by</th>
                  <th className="px-5 py-3 font-semibold">Similarity</th>
                  <th className="px-5 py-3 font-semibold">Submitted</th>
                  <th className="px-5 py-3 font-semibold">ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.07]">
                {response.items.map((item) => {
                  const similarity = item.similarity_percent;
                  const normalized = similarity === null ? 0 : Math.max(0, Math.min(100, similarity));
                  return (
                    <tr key={item.id} className="transition hover:bg-cyan-100/[0.035]">
                      <td className="max-w-[290px] px-5 py-4">
                        <p className="truncate text-sm font-semibold text-slate-100" title={item.original_filename}>{item.original_filename}</p>
                        <p className="mt-1 truncate text-xs text-slate-500" title={item.comparison_filename}>vs. {item.comparison_filename}</p>
                      </td>
                      <td className="px-5 py-4">
                        <p className="text-sm text-slate-200">{item.tenant_name}</p>
                        <p className="mt-1 text-xs text-slate-500">{item.user_name} <span className="text-white/20">/</span> {item.user_email}</p>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <span className={`w-12 font-mono text-sm ${similarityTone(similarity)}`}>
                            {similarity === null ? "N/A" : `${similarity.toFixed(1)}%`}
                          </span>
                          <span className="h-1 w-20 overflow-hidden bg-white/10">
                            <span className="block h-full bg-cyan-200" style={{ width: `${normalized}%` }} />
                          </span>
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-xs text-slate-400">
                        <span className="inline-flex items-center gap-2"><Clock3 className="size-3.5" />{formatDate(item.created_at)}</span>
                      </td>
                      <td className="px-5 py-4 font-mono text-xs text-slate-500">#{item.id}</td>
                    </tr>
                  );
                })}
                {!loading && response.items.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-5 py-14 text-center">
                      <p className="text-sm font-medium text-slate-300">No comparisons found</p>
                      <p className="mt-1 text-xs text-slate-500">Try a different search or open the detector workspace.</p>
                    </td>
                  </tr>
                )}
                {loading && response.items.length === 0 && (
                  <tr><td colSpan={5} className="px-5 py-14 text-center text-xs uppercase tracking-[0.16em] text-cyan-100/70">Loading activity</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-white/10 px-4 py-3 sm:px-6">
            <p className="text-xs text-slate-500">
              {response.total === 0 ? "0 comparisons" : `Showing ${(page - 1) * response.page_size + 1}–${Math.min(page * response.page_size, response.total)} of ${response.total.toLocaleString()}`}
            </p>
            <div className="flex items-center gap-2">
              <button type="button" onClick={() => { setLoading(true); setPage((current) => Math.max(1, current - 1)); }} disabled={page <= 1 || loading} aria-label="Previous page" className="grid size-9 place-items-center border border-white/15 text-slate-300 hover:border-cyan-200/50 hover:text-white disabled:cursor-not-allowed disabled:opacity-35">
                <ChevronLeft className="size-4" />
              </button>
              <span className="min-w-20 text-center font-mono text-xs text-slate-400">{response.pages === 0 ? 0 : page} / {response.pages}</span>
              <button type="button" onClick={() => { setLoading(true); setPage((current) => Math.min(response.pages, current + 1)); }} disabled={page >= response.pages || loading} aria-label="Next page" className="grid size-9 place-items-center border border-white/15 text-slate-300 hover:border-cyan-200/50 hover:text-white disabled:cursor-not-allowed disabled:opacity-35">
                <ChevronRight className="size-4" />
              </button>
            </div>
          </footer>
        </section>

        <p className="flex items-center justify-center gap-2 py-6 text-[10px] uppercase tracking-[0.16em] text-slate-600">
          <ShieldCheck className="size-3.5" /> Protected administrator view <span className="text-white/20">/</span> Apexive trademark service
        </p>
      </div>
    </main>
  );
}