"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import RequireAuth from "@/components/RequireAuth";
import {
  approveAdminManualSubscription,
  bulkUpdateAdminSubscriptions,
  createAdminSubscription,
  downloadAdminReport,
  getAdminSubscriptionDetails,
  getAdminSubscriptionClients,
  getAdminSubscriptionPayments,
  getAdminSubscriptionStatistics,
  getAdminSubscriptions,
  rejectAdminPayment,
  renewAdminSubscription,
  sendAdminSubscriptionReminders,
  updateAdminSubscription,
  verifyAdminPayment,
  type AdminPayment,
  type AdminSubscription,
  type AdminSubscriptionClient,
  type AdminSubscriptionDetails,
  type AdminSubscriptionStatistics,
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
  const [statistics, setStatistics] = useState<AdminSubscriptionStatistics | null>(null);
  const [details, setDetails] = useState<AdminSubscriptionDetails | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [planFilter, setPlanFilter] = useState("");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [isSupport, setIsSupport] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    const [clientResult, planResult, subscriptionResult, paymentResult, stats] =
      await Promise.all([
        getAdminSubscriptionClients(),
        getSubscriptionPlans(),
        getAdminSubscriptions({
          search,
          status: statusFilter,
          planId: planFilter ? Number(planFilter) : undefined,
        }),
        getAdminSubscriptionPayments(),
        getAdminSubscriptionStatistics(),
      ]);
    setClients(clientResult.items);
    setPlans(planResult);
    setSubscriptions(subscriptionResult.items);
    setPayments(paymentResult.items);
    setStatistics(stats);
    setSelectedIds([]);
  }, [planFilter, search, statusFilter]);

  useEffect(() => {
    let mounted = true;
    const rawUser = localStorage.getItem("apexive_user");
    let isAdmin = false;
    try {
      const user = rawUser
        ? (JSON.parse(rawUser) as {
            is_admin?: boolean;
            is_super_admin?: boolean;
            role?: string;
          })
        : null;
      isAdmin = user?.is_admin === true;
      setIsSuperAdmin(user?.is_super_admin === true);
      setIsSupport(user?.role?.toUpperCase() === "SUPPORT");
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
  const canManage = !isSupport;

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

  async function sendExpiryReminders() {
    if (
      !window.confirm(
        "Send email reminders to eligible clients whose subscriptions expire in 3 or 7 days? Already-sent reminders will be skipped.",
      )
    ) {
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await sendAdminSubscriptionReminders();
      setNotice(
        result.processed === 0
          ? "No new 3-day or 7-day subscription reminders were due."
          : `${result.processed} reminder${result.processed === 1 ? "" : "s"} processed; ${result.email_failures} email delivery failure${result.email_failures === 1 ? "" : "s"}.`,
      );
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to send subscription email reminders.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function submitSubscription(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const clientId = Number(form.get("client_id"));
    const planId = Number(form.get("plan_id"));
    const durationDays = Number(form.get("duration_days"));
    const reason = String(form.get("reason") ?? "").trim();
    if (
      !Number.isInteger(clientId) ||
      clientId <= 0 ||
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
        client_id: clientId,
        plan_id: planId,
        duration_days: durationDays,
        reason,
      });
      setNotice("Manual subscription request submitted for Super Admin approval.");
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

  async function cancelSubscription(subscription: AdminSubscription) {
    if (!window.confirm(`Cancel subscription #${subscription.id}?`)) return;
    const reason = window.prompt("Enter a reason for this cancellation:");
    if (!reason?.trim() || reason.trim().length < 3) {
      setError("A cancellation reason of at least 3 characters is required.");
      return;
    }
    if (!window.confirm("This is the final confirmation. Cancel this subscription now?")) {
      return;
    }
    await runAction(
      () => updateAdminSubscription(subscription.id, "cancel", { reason: reason.trim() }),
      `Subscription #${subscription.id} cancelled.`,
    );
  }

  async function openDetails(subscriptionId: number) {
    setError("");
    try {
      setDetails(await getAdminSubscriptionDetails(subscriptionId));
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to load subscription details.",
      );
    }
  }

  async function runBulkAction(action: "extend" | "cancel") {
    if (!selectedIds.length) return;
    let durationDays: number | undefined;
    if (action === "extend") {
      const value = window.prompt("Number of days to add:", "30");
      if (value === null) return;
      durationDays = Number(value);
      if (!Number.isInteger(durationDays) || durationDays < 1 || durationDays > 3660) {
        setError("Enter a whole number of days between 1 and 3660.");
        return;
      }
    } else if (!window.confirm(`Cancel ${selectedIds.length} selected subscriptions?`)) {
      return;
    }
    const reason = window.prompt(
      action === "cancel"
        ? "Confirm cancellation by entering the reason:"
        : "Enter the reason for this bulk extension:",
    );
    if (!reason?.trim() || reason.trim().length < 3) {
      setError("A reason of at least 3 characters is required.");
      return;
    }
    if (
      action === "cancel" &&
      !window.confirm("This is the final confirmation. Cancel the selected subscriptions now?")
    ) {
      return;
    }
    await runAction(
      () =>
        bulkUpdateAdminSubscriptions({
          action,
          subscription_ids: selectedIds,
          reason: reason.trim(),
          ...(durationDays ? { duration_days: durationDays } : {}),
        }),
      `${selectedIds.length} subscriptions ${action === "extend" ? "extended" : "cancelled"}.`,
    );
  }

  function exportPath(path: string) {
    const params = new URLSearchParams();
    if (search.trim()) params.set("search", search.trim());
    if (statusFilter) params.set("status", statusFilter);
    if (planFilter) params.set("plan_id", planFilter);
    return `${path}${params.size ? `?${params.toString()}` : ""}`;
  }

  const allVisibleSelected =
    subscriptions.length > 0 &&
    subscriptions.every((subscription) => selectedIds.includes(subscription.id));
  const revenueByCurrency = new Map<
    string,
    AdminSubscriptionStatistics["revenue_history"]
  >();
  for (const entry of statistics?.revenue_history ?? []) {
    const entries = revenueByCurrency.get(entry.currency) ?? [];
    entries.push(entry);
    revenueByCurrency.set(entry.currency, entries);
  }

  return (
    <main className="min-h-screen bg-slate-950 px-5 py-10 text-white sm:px-8">
      <div className="mx-auto max-w-7xl">
        {isSuperAdmin && (
          <Link
            href="/admin"
            className="mr-4 text-sm text-cyan-300 hover:underline"
          >
            Back to Admin Dashboard
          </Link>
        )}
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
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {[
                ["Total Active", statistics?.active_subscriptions ?? 0],
                [
                  "Revenue this month",
                  statistics
                    ? Object.entries(statistics.monthly_revenue_by_currency)
                        .map(([currency, amount]) => `${amount} ${currency}`)
                        .join(" · ") || "0"
                    : "—",
                ],
                ["Pending Requests", statistics?.pending_payment_requests ?? 0],
                ["Expiring Soon", statistics?.expiring_soon_count ?? 0],
              ].map(([label, value]) => (
                <article
                  key={label}
                  className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5"
                >
                  <p className="text-sm text-slate-400">{label}</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
                </article>
              ))}
            </section>

            <section className="grid gap-4 xl:grid-cols-2">
              <article className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">Revenue Dashboard</h2>
                    <p className="mt-1 text-sm text-slate-400">
                      Verified payments by month and currency · last 6 months
                    </p>
                  </div>
                  {canManage && (
                    <button
                      disabled={busy}
                      onClick={() =>
                        void runAction(
                          () =>
                            downloadAdminReport(
                              "/api/admin/revenue-report.csv",
                              "revenue-report.csv",
                            ),
                          "Revenue report downloaded.",
                        )
                      }
                      className="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-200 disabled:opacity-40"
                    >
                      Export CSV
                    </button>
                  )}
                </div>
                <div className="mt-5 space-y-5">
                  {[...revenueByCurrency.entries()].map(([currency, entries]) => {
                    const maxAmount = Math.max(
                      ...entries.map((entry) => Number(entry.amount)),
                      0,
                    );
                    return (
                      <div key={currency}>
                        <p className="mb-2 text-sm font-semibold text-slate-200">
                          {currency}
                        </p>
                        <div className="space-y-2">
                          {entries.map((entry) => {
                            const amount = Number(entry.amount);
                            const width =
                              maxAmount > 0
                                ? Math.max((amount / maxAmount) * 100, amount > 0 ? 3 : 0)
                                : 0;
                            return (
                              <div
                                key={`${entry.month}-${entry.currency}`}
                                className="grid grid-cols-[4.5rem_1fr_auto] items-center gap-3 text-xs"
                              >
                                <span className="text-slate-400">
                                  {new Date(`${entry.month}-01T00:00:00`).toLocaleDateString(
                                    undefined,
                                    { month: "short", year: "2-digit" },
                                  )}
                                </span>
                                <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                                  <div
                                    className="h-full rounded-full bg-cyan-400"
                                    style={{ width: `${width}%` }}
                                  />
                                </div>
                                <span className="min-w-20 text-right text-slate-200">
                                  {entry.amount}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                  {!revenueByCurrency.size && (
                    <p className="text-sm text-slate-500">
                      No verified payments recorded in the last 6 months.
                    </p>
                  )}
                </div>
              </article>

              <article className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">Expiring Soon</h2>
                    <p className="mt-1 text-sm text-slate-400">
                      Active subscriptions ending in the next 30 days
                    </p>
                  </div>
                  <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-200">
                    {statistics?.expiring_soon_count ?? 0}
                  </span>
                </div>
                <div className="mt-4 divide-y divide-slate-800">
                  {(statistics?.expiring_soon ?? []).map((subscription) => (
                    <div
                      key={subscription.id}
                      className="flex flex-wrap items-center justify-between gap-2 py-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-100">
                          {subscription.tenant_name}
                        </p>
                        <p className="text-xs text-slate-400">
                          {subscription.plan_name}
                        </p>
                      </div>
                      <time
                        dateTime={subscription.current_period_end}
                        className="text-xs text-amber-200"
                      >
                        {new Date(
                          subscription.current_period_end,
                        ).toLocaleDateString()}
                      </time>
                    </div>
                  ))}
                  {!statistics?.expiring_soon.length && (
                    <p className="py-4 text-sm text-slate-500">
                      No active subscriptions expire within 30 days.
                    </p>
                  )}
                  {Boolean(
                    statistics &&
                      statistics.expiring_soon_count >
                        statistics.expiring_soon.length,
                  ) && (
                    <p className="pt-3 text-xs text-slate-500">
                      Showing the first {statistics?.expiring_soon.length} of{" "}
                      {statistics?.expiring_soon_count} subscriptions.
                    </p>
                  )}
                </div>
              </article>
            </section>

            <section className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold">Email Notifications</h2>
                  <p className="mt-1 max-w-3xl text-sm text-slate-400">
                    Subscription expiry emails are sent 7 and 3 days before
                    renewal. Already-sent reminders are skipped automatically.
                  </p>
                  <p
                    className={`mt-2 text-xs font-semibold ${
                      statistics?.email_enabled
                        ? "text-emerald-300"
                        : "text-amber-300"
                    }`}
                  >
                    {statistics?.email_enabled
                      ? "Email delivery is enabled."
                      : "Email delivery is disabled. Configure EMAIL_ENABLED and SMTP settings in the backend."}
                  </p>
                </div>
                {canManage && (
                  <button
                    disabled={busy || !statistics?.email_enabled}
                    onClick={() => void sendExpiryReminders()}
                    className="rounded-lg border border-cyan-700 px-4 py-2 text-sm font-semibold text-cyan-200 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Send due reminders
                  </button>
                )}
              </div>
              <p className="mt-3 text-xs text-slate-500">
                To send reminders automatically, schedule{" "}
                <code className="text-slate-300">
                  python send_subscription_reminders.py
                </code>{" "}
                to run daily from the backend directory.
              </p>
            </section>

            {canManage && (
            <section className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
              <h2 className="text-lg font-semibold">Create manual subscription</h2>
              <p className="mt-1 text-sm text-slate-400">
                Requests remain pending until a Super Admin approves them. Trademark access always requires verified payment.
              </p>
              <form
                onSubmit={(event) => void submitSubscription(event)}
                className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5"
              >
                <label className="grid gap-1 text-xs text-slate-400">
                  Client
                  <select
                    name="client_id"
                    required
                    defaultValue=""
                    className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 text-sm text-white"
                  >
                    <option value="" disabled>
                      {clients.length ? "Select client" : "No clients available"}
                    </option>
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.display_name} · {client.email}
                      </option>
                    ))}
                  </select>
                  {clients.length ? (
                    <span className="text-[11px] leading-4 text-slate-500">
                      Choose the client who should receive this subscription. Use
                      their name and email to identify the correct account.
                    </span>
                  ) : (
                    <span className="text-[11px] leading-4 text-amber-300">
                      No client accounts are available.{" "}
                      <Link
                        href="/admin#create-client"
                        className="font-semibold text-cyan-300 underline"
                      >
                        Create a client account
                      </Link>{" "}
                      before creating a subscription.
                    </span>
                  )}
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
            )}

            <section className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-lg font-semibold">Subscriptions</h2>
                {canManage && (
                  <div className="flex flex-wrap gap-2">
                    <button
                      disabled={busy || !selectedIds.length}
                      onClick={() => void runBulkAction("extend")}
                      className="rounded-lg border border-cyan-700 px-3 py-2 text-xs font-semibold text-cyan-200 disabled:opacity-40"
                    >
                      Bulk extend ({selectedIds.length})
                    </button>
                    <button
                      disabled={busy || !selectedIds.length}
                      onClick={() => void runBulkAction("cancel")}
                      className="rounded-lg border border-rose-700 px-3 py-2 text-xs font-semibold text-rose-200 disabled:opacity-40"
                    >
                      Bulk cancel ({selectedIds.length})
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        void runAction(
                          () => downloadAdminReport(exportPath("/api/admin/subscriptions/export/csv"), "subscriptions.csv"),
                          "CSV export downloaded.",
                        )
                      }
                      className="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-200 disabled:opacity-40"
                    >
                      CSV
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        void runAction(
                          () => downloadAdminReport(exportPath("/api/admin/subscriptions/export/xlsx"), "subscriptions.xlsx"),
                          "Excel export downloaded.",
                        )
                      }
                      className="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-200 disabled:opacity-40"
                    >
                      Excel
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        void runAction(
                          () => downloadAdminReport("/api/admin/revenue-report.csv", "revenue-report.csv"),
                          "Revenue report downloaded.",
                        )
                      }
                      className="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-200 disabled:opacity-40"
                    >
                      Revenue report
                    </button>
                  </div>
                )}
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search tenant name"
                  aria-label="Search tenant name"
                  className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 text-sm text-white"
                />
                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                  aria-label="Filter by status"
                  className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 text-sm text-white"
                >
                  <option value="">All statuses</option>
                  <option value="active">Active</option>
                  <option value="expired">Expired</option>
                  <option value="pending">Pending</option>
                  <option value="cancelled">Cancelled</option>
                </select>
                <select
                  value={planFilter}
                  onChange={(event) => setPlanFilter(event.target.value)}
                  aria-label="Filter by plan"
                  className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 text-sm text-white"
                >
                  <option value="">All plans</option>
                  {plans.map((plan) => (
                    <option key={plan.id} value={plan.id}>{plan.name}</option>
                  ))}
                </select>
              </div>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[800px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500">
                    <tr>
                      {canManage && (
                        <th className="py-2">
                          <input
                            type="checkbox"
                            aria-label="Select all visible subscriptions"
                            checked={allVisibleSelected}
                            onChange={(event) =>
                              setSelectedIds(
                                event.target.checked
                                  ? subscriptions.map((item) => item.id)
                                  : [],
                              )
                            }
                          />
                        </th>
                      )}
                      <th className="py-2">ID</th>
                      <th>Tenant</th>
                      <th>Plan</th>
                      <th>Amount</th>
                      <th>Status</th>
                      <th>Period ends</th>
                      <th>Days left</th>
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
                          {canManage && (
                            <td className="py-3">
                              <input
                                type="checkbox"
                                aria-label={`Select subscription ${subscription.id}`}
                                checked={selectedIds.includes(subscription.id)}
                                onChange={(event) =>
                                  setSelectedIds((current) =>
                                    event.target.checked
                                      ? [...current, subscription.id]
                                      : current.filter((id) => id !== subscription.id),
                                  )
                                }
                              />
                            </td>
                          )}
                          <td className="py-3">#{subscription.id}</td>
                          <td>{subscription.tenant_name || `Tenant #${subscription.tenant_id}`}</td>
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
                          <td>
                            {subscription.current_period_end
                              ? Math.max(
                                  0,
                                  Math.ceil(
                                    (new Date(subscription.current_period_end).getTime() - Date.now()) /
                                      (1000 * 60 * 60 * 24),
                                  ),
                                )
                              : "—"}
                          </td>
                          <td className="space-x-3 text-right">
                            <button
                              disabled={busy}
                              onClick={() => void openDetails(subscription.id)}
                              className="font-semibold text-slate-200 disabled:opacity-50"
                            >
                              Details
                            </button>
                            {isSuperAdmin &&
                              subscription.status === "pending" &&
                              subscription.admin_access_reason && (
                                <button
                                  disabled={busy}
                                  onClick={() =>
                                    void runAction(
                                      () => approveAdminManualSubscription(subscription.id),
                                      `Manual subscription #${subscription.id} approved.`,
                                    )
                                  }
                                  className="font-semibold text-emerald-300 disabled:opacity-50"
                                >
                                  Approve manual
                                </button>
                              )}
                            {canManage && subscription.status === "pending" && hasVerifiedPayment && (
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
                            {canManage && ["active", "expired"].includes(subscription.status) && (
                              <button
                                disabled={busy}
                                onClick={() => void extendSubscription(subscription)}
                                className="font-semibold text-cyan-300 disabled:opacity-50"
                              >
                                Extend
                              </button>
                            )}
                            {canManage && ["pending", "active", "suspended"].includes(subscription.status) && (
                              <button
                                disabled={busy}
                                onClick={() => void cancelSubscription(subscription)}
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
                      <tr><td colSpan={canManage ? 9 : 8} className="py-5 text-slate-400">No subscriptions found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
              <h2 className="text-lg font-semibold">Payment requests</h2>
              <p className="mt-1 text-sm text-slate-400">
                Confirming a payment activates its linked pending subscription and grants product access.
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
                          {canManage && ["pending", "processing"].includes(payment.status) && (
                            <>
                              <button
                                disabled={busy}
                                onClick={() =>
                                  void runAction(
                                    () => verifyAdminPayment(payment.id),
                                    `Payment #${payment.id} confirmed and its subscription activated.`,
                                  )
                                }
                                className="font-semibold text-emerald-300 disabled:opacity-50"
                              >
                                Confirm &amp; Activate
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
      {details && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setDetails(null);
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="subscription-details-title"
            className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-slate-700 bg-[#0d1726] p-6 text-white shadow-2xl"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="subscription-details-title" className="text-xl font-semibold">
                  Subscription #{details.id}
                </h2>
                <p className="mt-1 text-sm text-slate-400">
                  {details.tenant_name || `Tenant #${details.tenant_id}`} · {details.plan.name}
                </p>
              </div>
              <button
                onClick={() => setDetails(null)}
                aria-label="Close details"
                className="rounded-lg border border-slate-700 px-3 py-1 text-sm"
              >
                Close
              </button>
            </div>
            <dl className="mt-5 grid gap-4 sm:grid-cols-3">
              <div><dt className="text-xs text-slate-400">Start date</dt><dd className="mt-1">{new Date(details.start_date).toLocaleString()}</dd></div>
              <div><dt className="text-xs text-slate-400">End date</dt><dd className="mt-1">{details.current_period_end ? new Date(details.current_period_end).toLocaleString() : "No end date"}</dd></div>
              <div><dt className="text-xs text-slate-400">Remaining days</dt><dd className="mt-1">{details.remaining_days ?? "—"}</dd></div>
              {details.admin_access_reason && (
                <div className="sm:col-span-3">
                  <dt className="text-xs text-slate-400">Manual access reason</dt>
                  <dd className="mt-1">{details.admin_access_reason}</dd>
                </div>
              )}
            </dl>
            <h3 className="mt-7 font-semibold">Payment history</h3>
            <div className="mt-2 overflow-x-auto">
              <table className="w-full min-w-[500px] text-left text-sm">
                <thead className="text-xs text-slate-400"><tr><th className="py-2">Date</th><th>Amount</th><th>Method</th><th>Status</th></tr></thead>
                <tbody className="divide-y divide-slate-800">
                  {details.payment_history.map((payment) => (
                    <tr key={payment.id}>
                      <td className="py-2">{new Date(payment.paid_at || payment.created_at).toLocaleString()}</td>
                      <td>{payment.amount} {payment.currency}</td>
                      <td>{payment.payment_method}</td>
                      <td>{payment.status}</td>
                    </tr>
                  ))}
                  {!details.payment_history.length && <tr><td colSpan={4} className="py-3 text-slate-400">No payments recorded.</td></tr>}
                </tbody>
              </table>
            </div>
            <h3 className="mt-7 font-semibold">Activity log</h3>
            <ol className="mt-2 space-y-3">
              {details.activity_log.map((entry) => (
                <li key={entry.id} className="rounded-lg border border-slate-800 p-3 text-sm">
                  <div className="flex flex-wrap justify-between gap-2">
                    <span>{entry.actor_name} · {entry.action}</span>
                    <time className="text-xs text-slate-400">{new Date(entry.created_at).toLocaleString()}</time>
                  </div>
                  {entry.reason && (
                    <pre className="mt-2 whitespace-pre-wrap break-words font-sans text-xs text-slate-300">
                      {entry.reason}
                    </pre>
                  )}
                </li>
              ))}
              {!details.activity_log.length && <li className="text-sm text-slate-400">No activity recorded.</li>}
            </ol>
          </section>
        </div>
      )}
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
