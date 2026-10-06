"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import RequireAuth from "@/components/RequireAuth";
import {
  createAdminClient,
  getAdminDashboard,
  rejectAdminPayment,
  resetAdminClientPassword,
  setAdminClientStatus,
  updateAdminSubscription,
  verifyAdminPayment,
  type AdminAuditLog,
  type AdminClient,
  type AdminPayment,
  type AdminSubscription,
} from "@/lib/admin";

type DashboardData = {
  clients: AdminClient[];
  payments: AdminPayment[];
  subscriptions: AdminSubscription[];
  auditLogs: AdminAuditLog[];
};

const emptyDashboard: DashboardData = {
  clients: [],
  payments: [],
  subscriptions: [],
  auditLogs: [],
};

function AdminDashboard() {
  const router = useRouter();
  const [data, setData] = useState(emptyDashboard);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [newClientPassword, setNewClientPassword] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      setData(await getAdminDashboard());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load admin data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    const rawUser = localStorage.getItem("apexive_user");
    try {
      const user = rawUser ? (JSON.parse(rawUser) as { is_admin?: boolean }) : null;
      if (!user?.is_admin) {
        router.replace("/");
      } else {
        getAdminDashboard()
          .then((result) => {
            if (mounted) setData(result);
          })
          .catch((reason: unknown) => {
            if (mounted) {
              setError(
                reason instanceof Error
                  ? reason.message
                  : "Unable to load admin data.",
              );
            }
          })
          .finally(() => {
            if (mounted) setLoading(false);
          });
      }
    } catch {
      router.replace("/");
    }
    return () => {
      mounted = false;
    };
  }, [router]);

  async function runAction(action: () => Promise<unknown>, successMessage: string) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(successMessage);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The requested action failed.");
    } finally {
      setBusy(false);
    }
  }

  async function addClient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await createAdminClient({
        username: String(form.get("username") ?? ""),
        email: String(form.get("email") ?? ""),
        display_name: String(form.get("display_name") ?? ""),
        company_name: String(form.get("company_name") ?? ""),
      });
      setNewClientPassword(result.temporary_password);
      setNotice(`Created client account for ${result.client.email}. Save the temporary password now.`);
      formElement.reset();
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create client.");
    } finally {
      setBusy(false);
    }
  }

  async function rejectPayment(payment: AdminPayment) {
    const reason = window.prompt("Enter a reason for rejecting this payment:");
    if (!reason?.trim()) {
      return;
    }
    await runAction(
      () => rejectAdminPayment(payment.id, reason.trim()),
      `Payment #${payment.id} rejected.`,
    );
  }

  async function resetClientPassword(client: AdminClient) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await resetAdminClientPassword(client.id);
      setNewClientPassword(result.temporary_password);
      setNotice(`Temporary password for ${client.email}. Share it securely.`);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to reset client password.");
    } finally {
      setBusy(false);
    }
  }

  const pendingPayments = data.payments.filter((payment) =>
    ["pending", "processing"].includes(payment.status),
  ).length;
  const activeSubscriptions = data.subscriptions.filter(
    (subscription) => subscription.status === "active",
  ).length;

  return (
    <main className="min-h-screen bg-slate-50">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4 px-6 py-10">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-600">
              Apexive administration
            </p>
            <h1 className="mt-2 text-3xl font-bold text-slate-950">Admin dashboard</h1>
            <p className="mt-2 text-sm text-slate-500">
              Manage client accounts, payment decisions, subscriptions, and audit history.
            </p>
          </div>
          <Link className="text-sm font-semibold text-blue-600" href="/dashboard">
            Client dashboard
          </Link>
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        {error && (
          <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}
        {notice && (
          <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
            <p>{notice}</p>
            {newClientPassword && (
              <p className="mt-2 break-all font-mono font-bold">
                Temporary password: {newClientPassword}
              </p>
            )}
          </div>
        )}
        {loading ? (
          <p className="py-16 text-center text-sm text-slate-500">Loading admin dashboard…</p>
        ) : (
          <>
            <section className="grid gap-4 sm:grid-cols-3">
              {[
                ["Clients", data.clients.length],
                ["Payments to review", pendingPayments],
                ["Active subscriptions", activeSubscriptions],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
                  <p className="mt-2 text-3xl font-bold text-slate-950">{value}</p>
                </div>
              ))}
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-bold text-slate-950">Create client</h2>
              <form onSubmit={addClient} className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <input name="username" required minLength={3} maxLength={50} placeholder="Username" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                <input name="email" type="email" required placeholder="Email" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                <input name="display_name" required minLength={2} maxLength={100} placeholder="Contact name" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                <input name="company_name" maxLength={200} placeholder="Company / workspace" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                <button disabled={busy} className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 sm:col-span-2 lg:col-span-4">
                  Create account and show temporary password
                </button>
              </form>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-bold text-slate-950">Clients</h2>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[680px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500">
                    <tr><th className="py-2">Client</th><th>Workspace</th><th>Status</th><th>Created</th><th /></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.clients.map((client) => (
                      <tr key={client.id}>
                        <td className="py-3"><p className="font-semibold text-slate-900">{client.display_name}</p><p className="text-slate-500">{client.email}</p></td>
                        <td>{client.company_name ?? "—"}</td>
                        <td>{client.is_active ? "Active" : "Disabled"}</td>
                        <td>{new Date(client.created_at).toLocaleDateString()}</td>
                        <td className="space-x-3 text-right">
                          <button disabled={busy} onClick={() => void resetClientPassword(client)} className="font-semibold text-amber-700 disabled:opacity-50">
                            Reset password
                          </button>
                          <button disabled={busy} onClick={() => void runAction(() => setAdminClientStatus(client.id, !client.is_active), client.is_active ? "Client disabled." : "Client enabled.")} className="font-semibold text-blue-700 disabled:opacity-50">
                            {client.is_active ? "Disable" : "Enable"}
                          </button>
                        </td>
                      </tr>
                    ))}
                    {!data.clients.length && <tr><td colSpan={5} className="py-5 text-slate-500">No clients created yet.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-bold text-slate-950">Payments</h2>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[680px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500">
                    <tr><th className="py-2">Payment</th><th>Tenant</th><th>Amount</th><th>Method</th><th>Status</th><th /></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.payments.map((payment) => (
                      <tr key={payment.id}>
                        <td className="py-3">#{payment.id}<p className="text-xs text-slate-500">Plan #{payment.plan_id}</p></td>
                        <td>{payment.tenant_id}</td>
                        <td>{payment.amount} {payment.currency}</td>
                        <td>{payment.payment_method}</td>
                        <td className="capitalize">{payment.status}</td>
                        <td className="space-x-3 text-right">
                          {["pending", "processing"].includes(payment.status) && (
                            <>
                              <button disabled={busy} onClick={() => void runAction(() => verifyAdminPayment(payment.id), `Payment #${payment.id} verified.`)} className="font-semibold text-emerald-700 disabled:opacity-50">Verify</button>
                              <button disabled={busy} onClick={() => void rejectPayment(payment)} className="font-semibold text-red-700 disabled:opacity-50">Reject</button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))}
                    {!data.payments.length && <tr><td colSpan={6} className="py-5 text-slate-500">No payments found.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-bold text-slate-950">Subscriptions</h2>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[680px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500">
                    <tr><th className="py-2">Subscription</th><th>Tenant</th><th>Product</th><th>Status</th><th>Period ends</th><th /></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.subscriptions.map((subscription) => (
                      <tr key={subscription.id}>
                        <td className="py-3">#{subscription.id}</td>
                        <td>{subscription.tenant_id}</td>
                        <td>{subscription.plan.name}</td>
                        <td className="capitalize">{subscription.status}</td>
                        <td>{subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : "—"}</td>
                        <td className="space-x-3 text-right">
                          {["pending", "suspended", "expired"].includes(subscription.status) && (
                            <button disabled={busy} onClick={() => void runAction(() => updateAdminSubscription(subscription.id, "activate"), `Subscription #${subscription.id} activated.`)} className="font-semibold text-emerald-700 disabled:opacity-50">Activate</button>
                          )}
                          {subscription.status === "active" && (
                            <button disabled={busy} onClick={() => void runAction(() => updateAdminSubscription(subscription.id, "suspend"), `Subscription #${subscription.id} suspended.`)} className="font-semibold text-amber-700 disabled:opacity-50">Suspend</button>
                          )}
                          {["pending", "active", "suspended"].includes(subscription.status) && (
                            <button disabled={busy} onClick={() => void runAction(() => updateAdminSubscription(subscription.id, "cancel"), `Subscription #${subscription.id} cancelled.`)} className="font-semibold text-red-700 disabled:opacity-50">Cancel</button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {!data.subscriptions.length && <tr><td colSpan={6} className="py-5 text-slate-500">No subscriptions found.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-bold text-slate-950">Recent audit log</h2>
              <ul className="mt-4 divide-y divide-slate-100">
                {data.auditLogs.slice(0, 20).map((entry) => (
                  <li key={entry.id} className="flex flex-wrap justify-between gap-2 py-3 text-sm">
                    <span className="font-medium text-slate-800">{entry.action} · {entry.target_type} #{entry.target_id}</span>
                    <span className="text-slate-500">Tenant {entry.tenant_id} · {new Date(entry.created_at).toLocaleString()}</span>
                  </li>
                ))}
                {!data.auditLogs.length && <li className="py-3 text-sm text-slate-500">No audit activity yet.</li>}
              </ul>
            </section>
          </>
        )}
      </div>
    </main>
  );
}

export default function AdminPage() {
  return (
    <RequireAuth nextPath="/admin">
      <AdminDashboard />
    </RequireAuth>
  );
}
