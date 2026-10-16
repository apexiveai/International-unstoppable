"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import RequireAuth from "@/components/RequireAuth";
import {
  assignAdminLicenseCustomer,
  changeAdminLicenseStatus,
  createAdminLicense,
  createAdminLicensePlan,
  deactivateAdminLicenseActivation,
  extendAdminLicense,
  getAdminDashboard,
  getAdminLicensePlans,
  getAdminLicenseRenewals,
  getAdminLicenseReports,
  getAdminLicenses,
  sendAdminLicenseRenewalAlerts,
  type AdminClient,
  type AdminLicense,
  type AdminLicensePlan,
} from "@/lib/admin";

const fieldClass =
  "w-full rounded-lg border border-slate-700 bg-[#091321] px-3 py-2 text-sm text-slate-100";
const buttonClass =
  "rounded-lg border border-cyan-400/30 px-3 py-2 text-sm font-semibold text-cyan-200 hover:bg-cyan-400/10 disabled:opacity-50";

function LicenseManagement() {
  const router = useRouter();
  const [clients, setClients] = useState<AdminClient[]>([]);
  const [plans, setPlans] = useState<AdminLicensePlan[]>([]);
  const [licenses, setLicenses] = useState<AdminLicense[]>([]);
  const [renewals, setRenewals] = useState<AdminLicense[]>([]);
  const [reports, setReports] = useState<Awaited<ReturnType<typeof getAdminLicenseReports>> | null>(null);
  const [newKey, setNewKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const [dashboard, planResult, licenseResult, renewalResult, reportResult] =
        await Promise.all([
          getAdminDashboard(false),
          getAdminLicensePlans(),
          getAdminLicenses(),
          getAdminLicenseRenewals(),
          getAdminLicenseReports(),
        ]);
      setClients(dashboard.clients);
      setPlans(planResult);
      setLicenses(licenseResult.items);
      setRenewals(renewalResult.items);
      setReports(reportResult);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load license data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let admin = false;
    try {
      const user = JSON.parse(localStorage.getItem("apexive_user") ?? "null") as {
        is_admin?: boolean;
        role?: string;
      } | null;
      admin = Boolean(user?.is_admin && user.role?.toUpperCase() !== "SUPPORT");
    } catch {
      admin = false;
    }
    if (!admin) {
      router.replace("/");
      return;
    }
    void Promise.resolve().then(load);
  }, [load, router]);

  async function perform(action: () => Promise<unknown>, message: string): Promise<boolean> {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(message);
      await load();
      return true;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The license action failed.");
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function submitPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    let features: Record<string, boolean>;
    try {
      features = JSON.parse(String(form.get("features") || "{}")) as Record<string, boolean>;
      if (
        typeof features !== "object" ||
        features === null ||
        Array.isArray(features) ||
        Object.values(features).some((value) => typeof value !== "boolean")
      ) {
        throw new Error("Features must be a JSON object with boolean values.");
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Features must be valid JSON.");
      return;
    }
    const element = event.currentTarget;
    const created = await perform(
      () =>
        createAdminLicensePlan({
          name: String(form.get("name") ?? "").trim(),
          description: String(form.get("description") ?? "").trim(),
          price: String(form.get("price") ?? ""),
          currency: String(form.get("currency") ?? "USD"),
          duration_days: Number(form.get("duration_days")),
          max_robots: Number(form.get("max_robots")),
          max_workflows: Number(form.get("max_workflows")),
          max_activations: Number(form.get("max_activations")),
          features,
        }),
      "License plan created.",
    );
    if (created) element.reset();
  }

  async function submitLicense(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const element = event.currentTarget;
    const form = new FormData(element);
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const selectedTenant = String(form.get("tenant_id") ?? "");
      const result = await createAdminLicense({
        plan_id: Number(form.get("plan_id")),
        tenant_id: selectedTenant ? Number(selectedTenant) : null,
      });
      setNewKey(result.license_key);
      setNotice("License generated. Copy the key now; it cannot be retrieved again.");
      element.reset();
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to generate license.");
    } finally {
      setBusy(false);
    }
  }

  async function copyKey() {
    try {
      await navigator.clipboard.writeText(newKey);
      setNotice("License key copied.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not copy license key.");
    }
  }

  async function extend(license: AdminLicense) {
    const value = window.prompt("How many days should this license be extended?", "30");
    if (!value) return;
    const days = Number(value);
    if (!Number.isInteger(days) || days <= 0) {
      setError("Enter a positive whole number of days.");
      return;
    }
    await perform(
      () => extendAdminLicense(license.id, days),
      `License #${license.id} extended by ${days} days.`,
    );
  }

  async function setStatus(license: AdminLicense, status: "active" | "suspended" | "revoked") {
    if (status === "revoked" && !window.confirm(`Permanently revoke license #${license.id}?`)) {
      return;
    }
    await perform(
      () => changeAdminLicenseStatus(license.id, status),
      `License #${license.id} ${status}.`,
    );
  }

  return (
    <main className="min-h-screen bg-[#08111e] text-slate-100">
      <header className="border-b border-slate-800 bg-[#0b1422] px-6 py-7 lg:px-10">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">Apexive administration</p>
            <h1 className="mt-2 text-3xl font-bold">License Management</h1>
            <p className="mt-2 text-sm text-slate-400">Issue keys, manage customer access and activation, and review renewals and sales.</p>
          </div>
          <div className="flex gap-3">
            <Link href="/admin" className={buttonClass}>Admin dashboard</Link>
            <button type="button" onClick={() => void load()} disabled={busy || loading} className={buttonClass}>Refresh</button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-8 px-6 py-8 lg:px-10">
        {error && <div role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div>}
        {notice && <div role="status" className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 p-4 text-sm text-emerald-200">{notice}</div>}
        {newKey && (
          <section className="rounded-2xl border border-amber-400/30 bg-amber-400/10 p-5">
            <p className="font-bold text-amber-100">Copy this license key now; it is displayed only once.</p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <code className="break-all rounded bg-black/30 px-3 py-2 font-mono text-sm">{newKey}</code>
              <button type="button" onClick={() => void copyKey()} className={buttonClass}>Copy key</button>
              <button type="button" onClick={() => setNewKey("")} className="text-sm text-slate-300 underline">Dismiss</button>
            </div>
          </section>
        )}

        {loading ? <p className="py-16 text-center text-slate-400">Loading licenses…</p> : (
          <>
            {reports && (
              <section id="reports" className="grid gap-4 sm:grid-cols-3">
                {[
                  ["Total licenses", reports.total_licenses],
                  ["Active licenses", reports.active_licenses],
                  ["Expired licenses", reports.expired_licenses],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
                    <p className="mt-3 text-3xl font-bold">{value}</p>
                  </div>
                ))}
                <div className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5 sm:col-span-3">
                  <h2 className="font-bold">Issued license value</h2>
                  {reports.issued_value_by_currency.length ? (
                    <ul className="mt-3 flex flex-wrap gap-5 text-sm text-slate-300">
                      {reports.issued_value_by_currency.map((item) => (
                        <li key={item.currency}>{item.currency} {item.amount} · {item.licenses} licenses</li>
                      ))}
                    </ul>
                  ) : <p className="mt-2 text-sm text-slate-400">No licenses issued.</p>}
                  <p className="mt-2 text-xs text-slate-500">Issued plan value; this is not a payment-settled revenue figure.</p>
                </div>
              </section>
            )}

            <section className="grid gap-8 lg:grid-cols-2">
              <form onSubmit={(event) => void submitPlan(event)} className="space-y-4 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                <div><h2 className="text-lg font-bold">Create License Plan</h2><p className="mt-1 text-sm text-slate-400">Configure price, duration, robot/workflow and activation limits.</p></div>
                <input required name="name" placeholder="Plan name" className={fieldClass} />
                <textarea name="description" placeholder="Description" className={fieldClass} />
                <div className="grid gap-3 sm:grid-cols-2">
                  <input required name="price" type="number" min="0" step="0.01" placeholder="Price" className={fieldClass} />
                  <input required name="currency" defaultValue="USD" placeholder="Currency" className={fieldClass} />
                  <input required name="duration_days" type="number" min="1" placeholder="Duration (days)" className={fieldClass} />
                  <input required name="max_robots" type="number" min="1" placeholder="Robot limit" className={fieldClass} />
                  <input required name="max_workflows" type="number" min="1" placeholder="Workflow limit" className={fieldClass} />
                  <input required name="max_activations" type="number" min="1" placeholder="Activation limit" className={fieldClass} />
                </div>
                <textarea name="features" defaultValue="{}" placeholder='Features JSON, e.g. {"scheduling":true}' className={`${fieldClass} min-h-20 font-mono`} />
                <button disabled={busy} className={buttonClass}>Create plan</button>
              </form>

              <form onSubmit={(event) => void submitLicense(event)} className="space-y-4 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                <div><h2 className="text-lg font-bold">Generate License</h2><p className="mt-1 text-sm text-slate-400">A cryptographically random key is shown once; only its SHA-256 hash is stored.</p></div>
                <select required name="plan_id" defaultValue="" className={fieldClass}>
                  <option value="" disabled>Select a license plan</option>
                  {plans.filter((plan) => plan.is_active).map((plan) => <option key={plan.id} value={plan.id}>{plan.name} · {plan.currency} {plan.price}</option>)}
                </select>
                <select name="tenant_id" defaultValue="" className={fieldClass}>
                  <option value="">Unassigned — assign customer later</option>
                  {clients.filter((client) => client.tenant_id).map((client) => <option key={client.id} value={client.tenant_id!}>{client.company_name || client.display_name} · {client.email}</option>)}
                </select>
                <button disabled={busy || !plans.some((plan) => plan.is_active)} className={buttonClass}>Generate key</button>
              </form>
            </section>

            <section id="renewals" className="rounded-2xl border border-amber-400/20 bg-[#0d1726] p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div><h2 className="text-lg font-bold">Renewal Alerts</h2><p className="mt-1 text-sm text-slate-400">Active customer licenses expiring within 30 days.</p></div>
                <button type="button" disabled={busy || !renewals.length} onClick={() => void perform(
                  sendAdminLicenseRenewalAlerts,
                  "Renewal reminders sent to eligible customer accounts.",
                )} className={buttonClass}>Send customer reminders</button>
              </div>
              {renewals.length ? <ul className="mt-4 divide-y divide-slate-800">
                {renewals.map((license) => <li key={license.id} className="flex flex-wrap justify-between gap-2 py-3 text-sm">
                  <span>{license.tenant_name || "Unassigned"} · {license.plan_name} · #{license.id}</span>
                  <time dateTime={license.expires_at}>{new Date(license.expires_at).toLocaleDateString()}</time>
                </li>)}
              </ul> : <p className="mt-4 text-sm text-slate-400">No licenses expiring in the next 30 days.</p>}
            </section>

            <section id="activations" className="overflow-hidden rounded-2xl border border-slate-800 bg-[#0d1726]">
              <div className="border-b border-slate-800 p-6"><h2 className="text-lg font-bold">License & Activation Management</h2><p className="mt-1 text-sm text-slate-400">Assign customers, extend, suspend/revoke keys, and review device activation history.</p></div>
              {!licenses.length ? <p className="p-6 text-sm text-slate-400">No licenses have been generated.</p> : (
                <div className="divide-y divide-slate-800">
                  {licenses.map((license) => (
                    <article key={license.id} className="space-y-4 p-6">
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <p className="font-bold">#{license.id} · {license.plan_name ?? "Plan"} <span className="ml-2 rounded-full border border-slate-600 px-2 py-1 text-xs capitalize text-slate-300">{license.status}</span></p>
                          <p className="mt-1 text-sm text-slate-400">{license.tenant_name || "Unassigned"} · {license.currency} {license.price}</p>
                          <p className="mt-1 text-xs text-slate-500">Expires {new Date(license.expires_at).toLocaleString()}</p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <button type="button" disabled={busy || license.status === "revoked"} onClick={() => void extend(license)} className={buttonClass}>Extend</button>
                          <button type="button" disabled={busy || license.status === "suspended" || license.status === "revoked"} onClick={() => void setStatus(license, "suspended")} className={buttonClass}>Suspend</button>
                          {license.status === "suspended" && <button type="button" disabled={busy} onClick={() => void setStatus(license, "active")} className={buttonClass}>Reactivate</button>}
                          <button type="button" disabled={busy || license.status === "revoked"} onClick={() => void setStatus(license, "revoked")} className="rounded-lg border border-rose-400/30 px-3 py-2 text-sm font-semibold text-rose-200 hover:bg-rose-400/10 disabled:opacity-50">Revoke</button>
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <select aria-label={`Assign customer to license ${license.id}`} defaultValue={license.tenant_id ?? ""} id={`customer-${license.id}`} className={`${fieldClass} max-w-xl`}>
                          <option value="">Select customer</option>
                          {clients.filter((client) => client.tenant_id).map((client) => <option key={client.id} value={client.tenant_id!}>{client.company_name || client.display_name} · {client.email}</option>)}
                        </select>
                        <button type="button" disabled={busy} onClick={() => {
                          const value = document.getElementById(`customer-${license.id}`) as HTMLSelectElement | null;
                          if (value?.value) void perform(
                            () => assignAdminLicenseCustomer(license.id, Number(value.value)),
                            `Customer assigned to license #${license.id}.`,
                          );
                        }} className={buttonClass}>Assign customer</button>
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-slate-300">Device / Robot activations</h3>
                        {license.activations.length ? <ul className="mt-2 space-y-2">
                          {license.activations.map((activation) => <li key={activation.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-black/20 px-3 py-2 text-sm">
                            <span>{activation.device_name} <span className="text-slate-500">({activation.device_id})</span> · {activation.is_active ? "Active" : `Deactivated ${activation.deactivated_at ? new Date(activation.deactivated_at).toLocaleString() : ""}`}</span>
                            {activation.is_active && <button type="button" disabled={busy} onClick={() => void perform(
                              () => deactivateAdminLicenseActivation(activation.id),
                              `Activation for ${activation.device_name} deactivated.`,
                            )} className="text-xs font-semibold text-rose-200 underline">Deactivate</button>}
                          </li>)}
                        </ul> : <p className="mt-2 text-sm text-slate-500">No activation history.</p>}
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-slate-300">Audit trail</h3>
                        <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500">
                          {license.events.map((event) => (
                            <li key={event.id}>{new Date(event.created_at).toLocaleString()} · {event.event_type} · admin {event.actor_user_id ?? "system"}</li>
                          ))}
                        </ul>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}

export default function AdminLicensesPage() {
  return <RequireAuth nextPath="/admin/licenses"><LicenseManagement /></RequireAuth>;
}
