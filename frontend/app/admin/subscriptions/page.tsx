"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import RequireAuth from "@/components/RequireAuth";
import {
  createAdminSubscription,
  getAdminSubscriptionClients,
  getAdminSubscriptionPayments,
  getAdminSubscriptions,
  rejectAdminPayment,
  renewAdminSubscription,
  updateAdminSubscription,
  verifyAdminPayment,
  type AdminPayment,
  type AdminSubscription,
  type AdminSubscriptionClient,
} from "@/lib/admin";
import {
  getSubscriptionPlans,
  type SubscriptionPlan,
} from "@/lib/subscriptions";

function statusClass(status: string) {
  if (status === "active" || status === "verified") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
  }
  if (status === "pending" || status === "processing") {
    return "border-amber-500/30 bg-amber-500/10 text-amber-300";
  }
  return "border-slate-600 bg-slate-700/30 text-slate-300";
}

function AdminSubscriptionsDashboard() {
  const router = useRouter();
  const [clients, setClients] = useState<AdminSubscriptionClient[]>([]);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [subscriptions, setSubscriptions] = useState<AdminSubscription[]>([]);
  const [payments, setPayments] = useState<AdminPayment[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    const [clientResult, planResult, subscriptionResult, paymentResult] =
      await Promise.all([
        getAdminSubscriptionClients(),
        getSubscriptionPlans(),
        getAdminSubscriptions(),
        getAdminSubscriptionPayments(),
      ]);
    setClients(clientResult.items);
    setPlans(planResult);
    setSubscriptions(subscriptionResult.items);
    setPayments(paymentResult.items);
  }, []);

  useEffect(() => {
    let mounted = true;
    const rawUser = localStorage.getItem("apexive_user");
    let isAdmin = false;
    try {
      const user = rawUser
        ? (JSON.parse(rawUser) as { is_admin?: boolean })
        : null;
      isAdmin = user?.is_admin === true;
    } catch {
      isAdmin = false;
    }
    if (!isAdmin) {
      router.replace("/");
      return () => {
        mounted = false;
      };
    }

    void Promise.resolve()
      .then(load)
      .catch((reason: unknown) => {
        if (mounted) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Unable to load subscription administration.",
          );
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [load, router]);

  async function runAction(action: () => Promise<unknown>, message: string) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(message);
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The requested action failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function submitSubscription(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const tenantId = Number(form.get("tenant_id"));
    const planId = Number(form.get("plan_id"));
    const durationDays = Number(form.get("duration_days"));
    const reason = String(form.get("reason") ?? "").trim();
    if (
      !Number.isInteger(tenantId) ||
      tenantId <= 0 ||
      !Number.isInteger(planId) ||
      planId <= 0 ||
      !Number.isInteger(durationDays) ||
      durationDays < 1 ||
      durationDays > 3660 ||
      reason.length < 3
    ) {
      setError(
        "Choose a client and plan, enter a valid duration, and provide an approval reason.",
      );
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");
    try {
      await createAdminSubscription({
        tenant_id: tenantId,
        plan_id: planId,
        duration_days: durationDays,
        reason,
      });
      setNotice("Subscription created and activated.");
      formElement.reset();
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to create subscription.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function extendSubscription(subscription: AdminSubscription) {
    const daysValue = window.prompt(
      "Number of days to add to this subscription:",
      "30",
    );
    if (daysValue === null) return;
    const durationDays = Number(daysValue);
    if (
      !Number.isInteger(durationDays) ||
      durationDays < 1 ||
      durationDays > 3660
    ) {
      setError("Enter a whole number of days between 1 and 3660.");
      return;
    }
    const reason = window.prompt("Enter the approval reason for this renewal:");
    if (!reason?.trim()) return;
    await runAction(
      () =>
        renewAdminSubscription(subscription.id, {
          duration_days: durationDays,
          reason: reason.trim(),
        }),
      `Subscription #${subscription.id} extended by ${durationDays} days.`,
    );
  }

  async function rejectPayment(payment: AdminPayment) {
    const reason = window.prompt("Enter a reason for rejecting this payment:");
    if (!reason?.trim()) return;
    await runAction(
      () => rejectAdminPayment(payment.id, reason.trim()),
      `Payment #${payment.id} rejected.`,
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 px-5 py-10 text-white sm:px-8">
      <div className="mx-auto max-w-7xl">
        <Link href="/" className="text-sm text-cyan-300 hover:underline">
          Back to community
        </Link>
        <header className="mt-5">
          <h1 className="text-3xl font-bold">Subscription Management</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Review customer payment requests, activate verified subscriptions,
            and create, extend, or cancel subscriptions. Manual access grants
            require an approval reason and are recorded in the audit log.
          </p>
        </header>

        {error && (
          <div role="alert" className="mt-5 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200">
            {error}
          </div>
        )}
        {notice && (
          <div role="status" className="mt-5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-200">
            {notice}
          </div>
        )}

        {loading ? (
          <p className="mt-8 text-sm text-slate-400">Loading subscriptions…</p>
        ) : (
          <div className="mt-8 space-y-8">
            <section className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
              <h2 className="text-lg font-semibold">Create manual subscription</h2>
              <p className="mt-1 text-sm text-slate-400">
                This activates access immediately without recording a payment.
              </p>
              <form
                onSubmit={(event) => void submitSubscription(event)}
                className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5"
              >
                <label className="grid gap-1 text-xs text-slate-400">
                  Client
                  <select
                    name="tenant_id"
                    required
                    defaultValue=""
                    className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 text-sm text-white"
                  >
                    <option value="" disabled>Select client</option>
                    {clients.map((client) => (
                      <option key={client.id} value={client.tenant_id}>
                        {client.display_name} · {client.email}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-xs text-slate-400">
                  Plan
                  <select
                    name="plan_id"
                    required
                    defaultValue=""
                    className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 text-sm text-white"
                  >
                    <option value="" disabled>Select plan</option>
                    {plans.map((plan) => (
                      <option key={plan.id} value={plan.id}>
                        {plan.name} · {plan.monthly_price} {plan.currency}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-xs text-slate-400">
                  Duration (days)
                  <input
                    name="duration_days"
                    type="number"
                    min="1"
                    max="3660"
                    step="1"
                    defaultValue="30"
                    required
                    className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 text-sm text-white"
                  />
                </label>
                <label className="grid gap-1 text-xs text-slate-400 md:col-span-2">
                  Approval reason
                  <input
                    name="reason"
                    minLength={3}
                    maxLength={2000}
                    required
                    placeholder="Record the authorization"
                    className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 text-sm text-white"
                  />
                </label>
                <button
                  disabled={busy || !clients.length || !plans.length}
                  className="rounded-lg bg-cyan-300 px-4 py-2 text-sm font-bold text-slate-950 disabled:opacity-50 md:justify-self-start"
                >
                  Create and activate
                </button>
              </form>
            </section>

            <section className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
              <h2 className="text-lg font-semibold">Subscriptions</h2>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[800px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500">
                    <tr>
                      <th className="py-2">ID</th>
                      <th>Tenant</th>
                      <th>Plan</th>
                      <th>Amount</th>
                      <th>Status</th>
                      <th>Period ends</th>
                      <th className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {subscriptions.map((subscription) => {
                      const hasVerifiedPayment = payments.some(
                        (payment) =>
                          payment.subscription_id === subscription.id &&
                          payment.status === "verified",
                      );
                      return (
                        <tr key={subscription.id}>
                          <td className="py-3">#{subscription.id}</td>
                          <td>{subscription.tenant_id}</td>
                          <td>{subscription.plan.name}</td>
                          <td>{subscription.price} {subscription.currency}</td>
                          <td>
                            <span className={`rounded-full border px-2 py-1 text-xs ${statusClass(subscription.status)}`}>
                              {subscription.status}
                            </span>
                          </td>
                          <td>
                            {subscription.current_period_end
                              ? new Date(subscription.current_period_end).toLocaleDateString()
                              : "—"}
                          </td>
                          <td className="space-x-3 text-right">
                            {subscription.status === "pending" && hasVerifiedPayment && (
                              <button
                                disabled={busy}
                                onClick={() =>
                                  void runAction(
                                    () => updateAdminSubscription(subscription.id, "activate"),
                                    `Subscription #${subscription.id} activated.`,
                                  )
                                }
                                className="font-semibold text-emerald-300 disabled:opacity-50"
                              >
                                Activate
                              </button>
                            )}
                            {["active", "expired"].includes(subscription.status) && (
                              <button
                                disabled={busy}
                                onClick={() => void extendSubscription(subscription)}
                                className="font-semibold text-cyan-300 disabled:opacity-50"
                              >
                                Extend
                              </button>
                            )}
                            {["pending", "active", "suspended"].includes(subscription.status) && (
                              <button
                                disabled={busy}
                                onClick={() => {
                                  if (window.confirm(`Cancel subscription #${subscription.id}?`)) {
                                    void runAction(
                                      () => updateAdminSubscription(subscription.id, "cancel"),
                                      `Subscription #${subscription.id} cancelled.`,
                                    );
                                  }
                                }}
                                className="font-semibold text-rose-300 disabled:opacity-50"
                              >
                                Cancel
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                    {!subscriptions.length && (
                      <tr><td colSpan={7} className="py-5 text-slate-400">No subscriptions found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
              <h2 className="text-lg font-semibold">Payment requests</h2>
              <p className="mt-1 text-sm text-slate-400">
                Verify a payment, then activate its pending subscription.
              </p>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[700px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500">
                    <tr>
                      <th className="py-2">Payment</th>
                      <th>Tenant</th>
                      <th>Amount</th>
                      <th>Method</th>
                      <th>Status</th>
                      <th className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {payments.map((payment) => (
                      <tr key={payment.id}>
                        <td className="py-3">
                          #{payment.id}
                          <p className="text-xs text-slate-500">
                            Subscription #{payment.subscription_id ?? "—"}
                          </p>
                        </td>
                        <td>{payment.tenant_id}</td>
                        <td>{payment.amount} {payment.currency}</td>
                        <td>{payment.payment_method}</td>
                        <td>
                          <span className={`rounded-full border px-2 py-1 text-xs ${statusClass(payment.status)}`}>
                            {payment.status}
                          </span>
                        </td>
                        <td className="space-x-3 text-right">
                          {["pending", "processing"].includes(payment.status) && (
                            <>
                              <button
                                disabled={busy}
                                onClick={() =>
                                  void runAction(
                                    () => verifyAdminPayment(payment.id),
                                    `Payment #${payment.id} verified.`,
                                  )
                                }
                                className="font-semibold text-emerald-300 disabled:opacity-50"
                              >
                                Verify
                              </button>
                              <button
                                disabled={busy}
                                onClick={() => void rejectPayment(payment)}
                                className="font-semibold text-rose-300 disabled:opacity-50"
                              >
                                Reject
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))}
                    {!payments.length && (
                      <tr><td colSpan={6} className="py-5 text-slate-400">No payment requests found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}

export default function AdminSubscriptionsPage() {
  return (
    <RequireAuth nextPath="/admin/subscriptions">
      <AdminSubscriptionsDashboard />
    </RequireAuth>
  );
}
