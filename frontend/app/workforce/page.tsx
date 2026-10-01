"use client";

import SiteHeader from "@/components/SiteHeader";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import RequireSubscription from "@/components/RequireSubscription";
import API_URL from "@/lib/api";

const lifecycle = [
  ["POST /executions", "202 Accepted"],
  ["AEWE Worker", "Claimed run"],
  ["Supervisor Planning", "LangGraph checkpoint"],
  ["Agent Execution", "Tool and agent work"],
  ["Review", "Approval gate"],
  ["Approval / Resume", "Human decision"],
  ["Verification", "Validate outputs"],
  ["Audit", "Immutable event trail"],
  ["Workflow Completed", "Verified result"],
];

type Execution = {
  id: number;
  workflow_name: string;
  status: string;
  current_step: string;
};

export default function WorkforcePage() {
  const router = useRouter();
  const [workflowName, setWorkflowName] = useState("Enterprise workflow");
  const [execution, setExecution] = useState<Execution | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("apexive_token");
    if (!token) return;
    fetch(`${API_URL}/api/executions`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (!response.ok) {
          const data = await response.json().catch(() => null);
          throw new Error(data?.detail ?? "Unable to load executions.");
        }
        return response.json();
      })
      .then((items: Execution[]) => setExecution(items[0] ?? null))
      .catch((reason: unknown) => {
        setMessage(
          reason instanceof Error
            ? reason.message
            : "Unable to load executions.",
        );
      });
  }, []);

  async function startExecution(event: FormEvent) {
    event.preventDefault();
    const token = localStorage.getItem("apexive_token");
    if (!token) {
      router.push("/login?next=/workforce");
      return;
    }
    setMessage("");
    const response = await fetch(`${API_URL}/api/executions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ workflow_name: workflowName }),
    }).catch((reason: unknown) => {
      setMessage(
        reason instanceof Error
          ? reason.message
          : "Unable to connect to the workforce API.",
      );
      return null;
    });
    if (!response) return;
    const data = await response.json().catch(() => null);
    if (!response.ok || !data) {
      setMessage(
        data?.detail ?? `Unable to start execution (${response.status}).`,
      );
      return;
    }
    setExecution(data);
    setMessage(`Execution #${data.id} accepted with 202 status.`);
  }

  return (
    <RequireSubscription productKey="workforce">
      <div className="min-h-screen bg-white text-slate-950">
        <SiteHeader />
        <main className="mx-auto max-w-7xl px-6 py-16">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400">
            Autonomous Enterprise Workforce
          </p>
          <h1 className="mt-3 max-w-4xl text-4xl font-bold tracking-tight sm:text-6xl">
            Governed agents that plan, execute, pause, and resume.
          </h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-400">
            Every run is checkpointed, approval-gated, verified, and recorded
            for tenant-scoped auditability.
          </p>

          <div className="mt-12 grid gap-4 md:grid-cols-3 lg:grid-cols-5">
            {lifecycle.map(([title, detail], index) => (
              <div key={title} className="relative rounded-2xl border border-slate-800 bg-slate-900 p-5 text-white">
                <div className="text-xs font-semibold text-emerald-400">0{index + 1}</div>
                <h2 className="mt-4 font-semibold">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-400">{detail}</p>
              </div>
            ))}
          </div>

          <section className="mt-12 grid gap-8 lg:grid-cols-[1fr_1.2fr]">
            <form onSubmit={startExecution} className="rounded-2xl border border-slate-800 bg-slate-900 p-7 text-white">
              <h2 className="text-xl font-semibold">Start an execution</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                The API accepts the run and returns immediately. A worker claims
                it before supervisor planning begins.
              </p>
              <input
                value={workflowName}
                onChange={(event) => setWorkflowName(event.target.value)}
                className="mt-6 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-emerald-500"
                placeholder="Workflow name"
              />
              <button className="mt-4 rounded-xl bg-emerald-500 px-5 py-3 font-semibold text-slate-950 hover:bg-emerald-400">
                POST /executions
              </button>
              {message && <p className="mt-4 text-sm text-slate-300">{message}</p>}
            </form>

            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-7 text-white">
              <h2 className="text-xl font-semibold">Current run</h2>
              {execution ? (
                <div className="mt-6 grid gap-4 sm:grid-cols-3">
                  <div><div className="text-xs text-slate-500">Execution</div><div className="mt-1 font-semibold">#{execution.id}</div></div>
                  <div><div className="text-xs text-slate-500">Status</div><div className="mt-1 font-semibold text-emerald-400">{execution.status}</div></div>
                  <div><div className="text-xs text-slate-500">Step</div><div className="mt-1 font-semibold">{execution.current_step}</div></div>
                </div>
              ) : (
                <p className="mt-6 text-slate-400">No execution has been submitted for this tenant yet.</p>
              )}
            </div>
          </section>

          <div className="mt-10 flex justify-center">
            <a
              href={`${API_URL}/docs`}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-6 py-4 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
            >
              Open Autonomous Enterprise Workforce
              <span aria-hidden="true">→</span>
            </a>
          </div>
        </main>
      </div>
    </RequireSubscription>
  );
}
