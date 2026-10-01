"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import SiteHeader from "@/components/SiteHeader";
import { useEffect, useState } from "react";
import API_URL from "@/lib/api";

type Execution = {
  id: number;
  workflow_name: string;
  status: string;
  current_step: string;
  created_at: string;
};

export default function HistoryPage() {
  const router = useRouter();
  const [items, setItems] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("apexive_token");
    if (!token) {
      router.replace("/login?next=/history");
      return;
    }
    fetch(`${API_URL}/api/executions`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail ?? "Unable to load history.");
        setItems(data);
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Unable to load history.");
      })
      .finally(() => setLoading(false));
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <SiteHeader />
      <main className="mx-auto max-w-6xl px-6 py-14">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400">Account</p>
        <h1 className="mt-3 text-4xl font-bold">My execution history</h1>
        <p className="mt-3 text-slate-400">
          Only executions submitted by your account are shown here.
        </p>
        {loading && <p className="mt-8 text-slate-400">Loading history...</p>}
        {error && <p className="mt-8 rounded-xl bg-red-500/10 p-4 text-red-300">{error}</p>}
        {!loading && !error && items.length === 0 && (
          <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-400">
            No executions yet. <Link className="text-emerald-400" href="/workforce">Start one from Workforce</Link>.
          </div>
        )}
        <div className="mt-8 space-y-4">
          {items.map((item) => (
            <article key={item.id} className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-lg font-semibold">{item.workflow_name}</h2>
                <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-sm text-emerald-400">{item.status}</span>
              </div>
              <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-400">
                <span>Execution #{item.id}</span>
                <span>Step: {item.current_step}</span>
                <span>{new Date(item.created_at).toLocaleString()}</span>
              </div>
            </article>
          ))}
        </div>
      </main>
    </div>
  );
}
