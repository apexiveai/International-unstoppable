"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import RequireAuth from "@/components/RequireAuth";
import { getClientProducts, type ClientProduct } from "@/lib/client";
import {
  createAdminAccount,
  createAdminClient,
  getAdminAccounts,
  getAdminDashboard,
  getAdminPlanSettings,
  refundAdminPayment,
  rejectAdminPayment,
  resetAdminClientPassword,
  setAdminAccountStatus,
  setAdminClientStatus,
  updateAdminPlanSettings,
  updateAdminSubscription,
  updateAdminSubscriptionPrice,
  verifyAdminPayment,
  type AdminAccount,
  type AdminAuditLog,
  type AdminClient,
  type AdminPayment,
  type AdminPlan,
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

const paymentStatuses = ["pending", "verified", "rejected", "refunded"] as const;
const subscriptionStatuses = [
  "active",
  "pending",
  "suspended",
  "expired",
  "cancelled",
] as const;

function scrollToSection(sectionId: string) {
  document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth" });
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "active" || status === "verified"
      ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
      : status === "pending" || status === "processing"
        ? "border-amber-400/30 bg-amber-400/10 text-amber-300"
        : status === "refunded" || status === "cancelled" || status === "rejected"
          ? "border-rose-400/30 bg-rose-400/10 text-rose-300"
          : "border-slate-400/30 bg-slate-400/10 text-slate-300";
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold capitalize ${color}`}>
      {status}
    </span>
  );
}

function AdminDashboard() {
  const router = useRouter();
  const [data, setData] = useState(emptyDashboard);
  const [accounts, setAccounts] = useState<AdminAccount[]>([]);
  const [products, setProducts] = useState<ClientProduct[]>([]);
  const [plans, setPlans] = useState<AdminPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const [selectedClient, setSelectedClient] = useState<AdminClient | null>(null);
  const [selectedAdmin, setSelectedAdmin] = useState<AdminAccount | null>(null);
  const [paymentFilter, setPaymentFilter] = useState<string>("pending");
  const [subscriptionFilter, setSubscriptionFilter] = useState<string>("active");
  const [editingSubscriptionId, setEditingSubscriptionId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setError("");
    try {
      const [dashboard, adminAccounts, catalog, planSettings] = await Promise.all([
        getAdminDashboard(),
        getAdminAccounts(),
        getClientProducts(),
        getAdminPlanSettings(),
      ]);
      setData(dashboard);
      setAccounts(adminAccounts);
      setProducts(catalog);
      setPlans(planSettings);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load admin data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    let isAdmin = false;
    try {
      const rawUser = localStorage.getItem("apexive_user");
      const user = rawUser ? (JSON.parse(rawUser) as { is_admin?: boolean }) : null;
      isAdmin = Boolean(user?.is_admin);
    } catch {
      isAdmin = false;
    }

    if (!isAdmin) {
      router.replace("/");
      return () => {
        mounted = false;
      };
    }

    void Promise.all([
      getAdminDashboard(),
      getAdminAccounts(),
      getClientProducts(),
      getAdminPlanSettings(),
    ])
      .then(([dashboard, adminAccounts, catalog, planSettings]) => {
        if (!mounted) return;
        setData(dashboard);
        setAccounts(adminAccounts);
        setProducts(catalog);
        setPlans(planSettings);
      })
      .catch((reason: unknown) => {
        if (mounted) {
          setError(reason instanceof Error ? reason.message : "Unable to load admin data.");
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [router]);

  async function runAction(action: () => Promise<unknown>, successMessage: string) {
    setBusy(true);
    setError("");
    setNotice("");
    setTemporaryPassword("");
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

  async function submitClient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setBusy(true);
    setError("");
    setNotice("");
    setTemporaryPassword("");
    try {
      const result = await createAdminClient({
        username: String(form.get("username") ?? ""),
        email: String(form.get("email") ?? ""),
        display_name: String(form.get("display_name") ?? ""),
        company_name: String(form.get("company_name") ?? ""),
      });
      setTemporaryPassword(result.temporary_password);
      setNotice(`Created client account for ${result.client.email}. Save the temporary password now.`);
      formElement.reset();
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create client.");
    } finally {
      setBusy(false);
    }
  }

  async function submitAdmin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setBusy(true);
    setError("");
    setNotice("");
    setTemporaryPassword("");
    try {
      const result = await createAdminAccount({
        username: String(form.get("username") ?? ""),
        email: String(form.get("email") ?? ""),
        display_name: String(form.get("display_name") ?? ""),
      });
      setTemporaryPassword(result.temporary_password);
      setNotice(`Created administrator account for ${result.admin.email}. Save the temporary password now.`);
      formElement.reset();
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create administrator.");
    } finally {
      setBusy(false);
    }
  }

  async function rejectPayment(payment: AdminPayment) {
    const reason = window.prompt("Enter a reason for rejecting this payment:");
    if (!reason?.trim()) return;
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
      setTemporaryPassword(result.temporary_password);
      setNotice(`Temporary password for ${client.email}. Share it securely.`);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to reset client password.");
    } finally {
      setBusy(false);
    }
  }

  async function savePlan(event: FormEvent<HTMLFormElement>, plan: AdminPlan) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const price = Number(form.get("monthly_price"));
    if (!Number.isFinite(price) || price < 0) {
      setError("Enter a valid non-negative subscription price.");
      return;
    }
    await runAction(
      () =>
        updateAdminPlanSettings(plan.id, {
          name: String(form.get("name") ?? ""),
          description: String(form.get("description") ?? ""),
          monthly_price: String(price),
          currency: String(form.get("currency") ?? ""),
          billing_cycle: String(form.get("billing_cycle") ?? ""),
          is_active: form.get("is_active") === "on",
        }),
      `Saved settings for ${plan.name}.`,
    );
  }

  async function saveSubscriptionPrice(
    event: FormEvent<HTMLFormElement>,
    subscription: AdminSubscription,
  ) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const rawPrice = String(form.get("price") ?? "").trim();
    const price = Number(rawPrice);
    if (!rawPrice || !Number.isFinite(price) || price < 0) {
      setError("Enter a valid subscription amount greater than or equal to zero.");
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");
    try {
      await updateAdminSubscriptionPrice(subscription.id, rawPrice);
      setEditingSubscriptionId(null);
      setNotice(`Subscription #${subscription.id} amount updated to ${rawPrice} ${subscription.currency}.`);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to update subscription amount.");
    } finally {
      setBusy(false);
    }
  }

  const pendingPaymentCount = data.payments.filter((payment) =>
    ["pending", "processing"].includes(payment.status),
  ).length;
  const activeSubscriptionCount = data.subscriptions.filter(
    (subscription) => subscription.status === "active",
  ).length;
  const filteredPayments = data.payments.filter((payment) => {
    if (paymentFilter === "pending") return ["pending", "processing"].includes(payment.status);
    return payment.status === paymentFilter;
  });
  const filteredSubscriptions = data.subscriptions.filter(
    (subscription) => subscription.status === subscriptionFilter,
  );

  return (
    <main className="min-h-screen bg-[#080e18] text-slate-100">
      <div className="min-h-screen lg:flex">
        <aside className="border-b border-slate-800 bg-[#0b1422] px-5 py-6 lg:sticky lg:top-0 lg:h-screen lg:w-72 lg:shrink-0 lg:overflow-y-auto lg:border-b-0 lg:border-r">
          <Link href="/admin" className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-400/10 text-sm font-black text-cyan-300">A</span>
            <span>
              <span className="block text-sm font-bold tracking-wide">APEXIVE AI</span>
              <span className="block text-xs text-slate-500">ADMIN CONSOLE</span>
            </span>
          </Link>
          <nav aria-label="Admin navigation" className="mt-8 grid gap-1 text-sm">
            <a href="#dashboard" className="rounded-lg px-3 py-2.5 font-semibold text-slate-200 hover:bg-slate-800/70">Dashboard</a>
            <div className="pt-3">
              <a href="#clients" className="px-3 text-xs font-bold uppercase tracking-widest text-slate-500">Clients</a>
              <div className="mt-1 grid gap-1">
                <a href="#clients" className="rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-800/70">All Clients</a>
                <a href="#create-client" className="rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-800/70">Create Client</a>
                <button onClick={() => selectedClient ? scrollToSection("client-details") : scrollToSection("clients")} className="rounded-lg px-3 py-2 text-left text-slate-300 hover:bg-slate-800/70">Client Details</button>
              </div>
            </div>
            <div className="pt-3">
              <a href="#admins" className="px-3 text-xs font-bold uppercase tracking-widest text-slate-500">Admins</a>
              <div className="mt-1 grid gap-1">
                <a href="#admins" className="rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-800/70">Admin List</a>
                <a href="#create-admin" className="rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-800/70">Create Admin</a>
                <button onClick={() => selectedAdmin ? scrollToSection("admin-details") : scrollToSection("admins")} className="rounded-lg px-3 py-2 text-left text-slate-300 hover:bg-slate-800/70">Admin Details</button>
              </div>
            </div>
            <div className="pt-3">
              <a href="#subscriptions" className="px-3 text-xs font-bold uppercase tracking-widest text-slate-500">Subscriptions</a>
              <div className="mt-1 grid gap-1">
                {subscriptionStatuses.map((item) => (
                  <button key={item} onClick={() => { setSubscriptionFilter(item); scrollToSection("subscriptions"); }} className="rounded-lg px-3 py-2 text-left capitalize text-slate-300 hover:bg-slate-800/70">{item}</button>
                ))}
              </div>
            </div>
            <div className="pt-3">
              <a href="#payments" className="px-3 text-xs font-bold uppercase tracking-widest text-slate-500">Payments</a>
              <div className="mt-1 grid gap-1">
                {paymentStatuses.map((item) => (
                  <button key={item} onClick={() => { setPaymentFilter(item); scrollToSection("payments"); }} className="rounded-lg px-3 py-2 text-left capitalize text-slate-300 hover:bg-slate-800/70">{item}</button>
                ))}
              </div>
            </div>
            <div className="pt-3">
              <a href="#products" className="px-3 text-xs font-bold uppercase tracking-widest text-slate-500">Products</a>
              <div className="mt-1 grid gap-1">
                {products.map((product) => (
                  <a key={product.product_key} href={`#product-${product.product_key}`} className="rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-800/70">{product.product_name}</a>
                ))}
              </div>
            </div>
            <a href="#audit-logs" className="mt-3 rounded-lg px-3 py-2.5 text-slate-300 hover:bg-slate-800/70">Audit Logs</a>
            <a href="#settings" className="rounded-lg px-3 py-2.5 text-slate-300 hover:bg-slate-800/70">Settings</a>
          </nav>
          <Link href="/dashboard" className="mt-8 inline-block px-3 text-sm font-semibold text-cyan-300 hover:text-cyan-200">← Client dashboard</Link>
        </aside>

        <div className="min-w-0 flex-1">
          <header id="dashboard" className="border-b border-slate-800 bg-[#0b1422] px-6 py-8 lg:px-10">
            <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">Apexive administration</p>
                <h1 className="mt-2 text-3xl font-bold text-white">Dashboard</h1>
                <p className="mt-2 text-sm text-slate-400">Manage clients, administrators, subscriptions, payments, products, and platform settings.</p>
              </div>
              <button onClick={() => void load()} disabled={busy || loading} className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800 disabled:opacity-50">Refresh data</button>
            </div>
          </header>

          <div className="mx-auto max-w-7xl space-y-8 px-6 py-8 lg:px-10">
            {error && (
              <div role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div>
            )}
            {notice && (
              <div role="status" className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 p-4 text-sm text-emerald-200">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p>{notice}</p>
                    {temporaryPassword && <p className="mt-2 break-all font-mono font-bold">Temporary password: {temporaryPassword}</p>}
                  </div>
                  <button onClick={() => { setNotice(""); setTemporaryPassword(""); }} aria-label="Dismiss notification" className="text-lg leading-none text-emerald-100">×</button>
                </div>
              </div>
            )}

            {loading ? (
              <p className="py-20 text-center text-sm text-slate-400">Loading admin console…</p>
            ) : (
              <>
                <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  {[
                    ["Clients", data.clients.length],
                    ["Administrators", accounts.length],
                    ["Payments to review", pendingPaymentCount],
                    ["Active subscriptions", activeSubscriptionCount],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-2xl border border-slate-800 bg-[#0d1726] p-5">
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
                      <p className="mt-3 text-3xl font-bold text-white">{value}</p>
                    </div>
                  ))}
                </section>

                <section id="clients" className="scroll-mt-6 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="text-lg font-bold text-white">All Clients</h2>
                      <p className="mt-1 text-sm text-slate-400">Review client accounts, open their details, or manage access.</p>
                    </div>
                    <a href="#create-client" className="rounded-lg bg-cyan-300 px-4 py-2 text-sm font-bold text-slate-950">Create client</a>
                  </div>
                  <div className="mt-5 overflow-x-auto">
                    <table className="w-full min-w-[760px] text-left text-sm">
                      <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Client</th><th>Workspace</th><th>Status</th><th>Created</th><th className="text-right">Actions</th></tr></thead>
                      <tbody className="divide-y divide-slate-800">
                        {data.clients.map((client) => (
                          <tr key={client.id}>
                            <td className="py-3"><p className="font-semibold text-slate-100">{client.display_name}</p><p className="text-slate-400">{client.email}</p></td>
                            <td className="text-slate-300">{client.company_name ?? "—"}</td>
                            <td><StatusBadge status={client.is_active ? "active" : "disabled"} /></td>
                            <td className="text-slate-400">{new Date(client.created_at).toLocaleDateString()}</td>
                            <td className="space-x-3 text-right">
                              <button onClick={() => { setSelectedClient(client); scrollToSection("client-details"); }} className="font-semibold text-cyan-300 hover:text-cyan-100">Details</button>
                              <button disabled={busy} onClick={() => void resetClientPassword(client)} className="font-semibold text-amber-300 disabled:opacity-50">Reset password</button>
                              <button disabled={busy} onClick={() => void runAction(() => setAdminClientStatus(client.id, !client.is_active), client.is_active ? "Client disabled." : "Client enabled.")} className="font-semibold text-slate-300 disabled:opacity-50">{client.is_active ? "Disable" : "Enable"}</button>
                            </td>
                          </tr>
                        ))}
                        {!data.clients.length && <tr><td colSpan={5} className="py-5 text-slate-400">No clients created yet.</td></tr>}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section id="create-client" className="scroll-mt-6 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                  <h2 className="text-lg font-bold text-white">Create Client</h2>
                  <form onSubmit={submitClient} className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    <input aria-label="Username" name="username" required minLength={3} maxLength={50} placeholder="Username" className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
                    <input aria-label="Email" name="email" type="email" required placeholder="Email" className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
                    <input aria-label="Contact name" name="display_name" required minLength={2} maxLength={100} placeholder="Contact name" className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
                    <input aria-label="Company or workspace" name="company_name" maxLength={200} placeholder="Company / workspace" className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
                    <button disabled={busy} className="rounded-lg bg-cyan-300 px-4 py-2.5 text-sm font-bold text-slate-950 disabled:opacity-50 sm:col-span-2 xl:col-span-4">Create account and show temporary password</button>
                  </form>
                </section>

                {selectedClient && (
                  <section id="client-details" className="scroll-mt-6 rounded-2xl border border-cyan-400/30 bg-[#0d1726] p-6">
                    <div className="flex items-center justify-between gap-3">
                      <h2 className="text-lg font-bold text-white">Client Details</h2>
                      <button onClick={() => setSelectedClient(null)} className="text-sm font-semibold text-slate-400 hover:text-white">Close</button>
                    </div>
                    <dl className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                      {[["Name", selectedClient.display_name], ["Username", selectedClient.username], ["Email", selectedClient.email], ["Workspace", selectedClient.company_name ?? "—"], ["Tenant ID", selectedClient.tenant_id ?? "—"], ["Created", new Date(selectedClient.created_at).toLocaleString()]].map(([label, value]) => (
                        <div key={label}><dt className="text-xs uppercase tracking-wider text-slate-500">{label}</dt><dd className="mt-1 text-sm text-slate-100">{value}</dd></div>
                      ))}
                    </dl>
                  </section>
                )}

                <section id="admins" className="scroll-mt-6 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div><h2 className="text-lg font-bold text-white">Admin List</h2><p className="mt-1 text-sm text-slate-400">Review administrator accounts and enable or disable access.</p></div>
                    <a href="#create-admin" className="rounded-lg bg-cyan-300 px-4 py-2 text-sm font-bold text-slate-950">Create admin</a>
                  </div>
                  <div className="mt-5 overflow-x-auto">
                    <table className="w-full min-w-[680px] text-left text-sm">
                      <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Administrator</th><th>Username</th><th>Status</th><th>Created</th><th className="text-right">Actions</th></tr></thead>
                      <tbody className="divide-y divide-slate-800">
                        {accounts.map((account) => (
                          <tr key={account.id}>
                            <td className="py-3"><p className="font-semibold text-slate-100">{account.display_name}</p><p className="text-slate-400">{account.email}</p></td>
                            <td className="text-slate-300">{account.username}</td>
                            <td><StatusBadge status={account.is_active ? "active" : "disabled"} /></td>
                            <td className="text-slate-400">{new Date(account.created_at).toLocaleDateString()}</td>
                            <td className="space-x-3 text-right">
                              <button onClick={() => { setSelectedAdmin(account); scrollToSection("admin-details"); }} className="font-semibold text-cyan-300">Details</button>
                              <button disabled={busy} onClick={() => void runAction(() => setAdminAccountStatus(account.id, !account.is_active), account.is_active ? "Administrator disabled." : "Administrator enabled.")} className="font-semibold text-slate-300 disabled:opacity-50">{account.is_active ? "Disable" : "Enable"}</button>
                            </td>
                          </tr>
                        ))}
                        {!accounts.length && <tr><td colSpan={5} className="py-5 text-slate-400">No administrator accounts found.</td></tr>}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section id="create-admin" className="scroll-mt-6 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                  <h2 className="text-lg font-bold text-white">Create Admin</h2>
                  <p className="mt-1 text-sm text-slate-400">The new administrator receives a one-time temporary password.</p>
                  <form onSubmit={submitAdmin} className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    <input aria-label="Admin username" name="username" required minLength={3} maxLength={50} placeholder="Username" className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
                    <input aria-label="Admin email" name="email" type="email" required placeholder="Email" className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
                    <input aria-label="Admin display name" name="display_name" required minLength={2} maxLength={100} placeholder="Display name" className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
                    <button disabled={busy} className="rounded-lg bg-cyan-300 px-4 py-2.5 text-sm font-bold text-slate-950 disabled:opacity-50">Create administrator</button>
                  </form>
                </section>

                {selectedAdmin && (
                  <section id="admin-details" className="scroll-mt-6 rounded-2xl border border-cyan-400/30 bg-[#0d1726] p-6">
                    <div className="flex items-center justify-between gap-3">
                      <h2 className="text-lg font-bold text-white">Admin Details</h2>
                      <button onClick={() => setSelectedAdmin(null)} className="text-sm font-semibold text-slate-400 hover:text-white">Close</button>
                    </div>
                    <dl className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                      {[["Name", selectedAdmin.display_name], ["Username", selectedAdmin.username], ["Email", selectedAdmin.email], ["Status", selectedAdmin.is_active ? "Active" : "Disabled"], ["Account type", "Administrator"], ["Created", new Date(selectedAdmin.created_at).toLocaleString()]].map(([label, value]) => (
                        <div key={label}><dt className="text-xs uppercase tracking-wider text-slate-500">{label}</dt><dd className="mt-1 text-sm text-slate-100">{value}</dd></div>
                      ))}
                    </dl>
                  </section>
                )}

                <section id="subscriptions" className="scroll-mt-6 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div><h2 className="text-lg font-bold text-white">Subscriptions</h2><p className="mt-1 text-sm text-slate-400">Review status and set the amount for each subscription. Changing a subscription amount does not rewrite historical payments.</p></div>
                    <label className="flex items-center gap-2 text-sm text-slate-400">Status<select value={subscriptionFilter} onChange={(event) => setSubscriptionFilter(event.target.value)} className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 text-slate-100">{subscriptionStatuses.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
                  </div>
                  <div className="mt-5 overflow-x-auto">
                    <table className="w-full min-w-[980px] text-left text-sm">
                      <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Subscription</th><th>Tenant</th><th>Product</th><th>Amount</th><th>Status</th><th>Period ends</th><th className="text-right">Actions</th></tr></thead>
                      <tbody className="divide-y divide-slate-800">
                        {filteredSubscriptions.map((subscription) => (
                          <tr key={subscription.id}>
                            <td className="py-3 text-slate-100">#{subscription.id}</td><td className="text-slate-300">{subscription.tenant_id}</td><td className="text-slate-300">{subscription.plan.name}</td>
                            <td className="text-slate-100">{subscription.price} {subscription.currency}<p className="text-xs text-slate-500">{subscription.billing_cycle}</p></td>
                            <td><StatusBadge status={subscription.status} /></td><td className="text-slate-400">{subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : "—"}</td>
                            <td className="text-right">
                              <div className="flex flex-wrap items-center justify-end gap-3">
                              {editingSubscriptionId === subscription.id ? (
                                <form onSubmit={(event) => void saveSubscriptionPrice(event, subscription)} className="flex items-center gap-2">
                                  <input aria-label={`Amount for subscription ${subscription.id}`} name="price" type="number" min="0" max="9999999999.99" step="0.01" required defaultValue={subscription.price} className="w-28 rounded-lg border border-slate-700 bg-[#080e18] px-2 py-1.5 text-right text-sm text-white" />
                                  <button disabled={busy} className="font-semibold text-cyan-300 disabled:opacity-50">Save</button>
                                  <button type="button" disabled={busy} onClick={() => setEditingSubscriptionId(null)} className="font-semibold text-slate-400 disabled:opacity-50">Cancel</button>
                                </form>
                              ) : (
                                <button disabled={busy} onClick={() => setEditingSubscriptionId(subscription.id)} className="font-semibold text-cyan-300 disabled:opacity-50">Edit amount</button>
                              )}
                              {["pending", "suspended", "expired"].includes(subscription.status) && <button disabled={busy} onClick={() => void runAction(() => updateAdminSubscription(subscription.id, "activate"), `Subscription #${subscription.id} activated.`)} className="font-semibold text-emerald-300 disabled:opacity-50">Activate</button>}
                              {subscription.status === "active" && <button disabled={busy} onClick={() => void runAction(() => updateAdminSubscription(subscription.id, "suspend"), `Subscription #${subscription.id} suspended.`)} className="font-semibold text-amber-300 disabled:opacity-50">Suspend</button>}
                              {["pending", "active", "suspended"].includes(subscription.status) && <button disabled={busy} onClick={() => void runAction(() => updateAdminSubscription(subscription.id, "cancel"), `Subscription #${subscription.id} cancelled.`)} className="font-semibold text-rose-300 disabled:opacity-50">Cancel</button>}
                              </div>
                            </td>
                          </tr>
                        ))}
                        {!filteredSubscriptions.length && <tr><td colSpan={7} className="py-5 text-slate-400">No {subscriptionFilter} subscriptions found.</td></tr>}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section id="payments" className="scroll-mt-6 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div><h2 className="text-lg font-bold text-white">Payments</h2><p className="mt-1 text-sm text-slate-400">Verify, reject, or refund payments.</p></div>
                    <label className="flex items-center gap-2 text-sm text-slate-400">Status<select value={paymentFilter} onChange={(event) => setPaymentFilter(event.target.value)} className="rounded-lg border border-slate-700 bg-[#080e18] px-3 py-2 capitalize text-slate-100">{paymentStatuses.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
                  </div>
                  <div className="mt-5 overflow-x-auto">
                    <table className="w-full min-w-[850px] text-left text-sm">
                      <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Payment</th><th>Tenant</th><th>Amount</th><th>Method</th><th>Status</th><th className="text-right">Actions</th></tr></thead>
                      <tbody className="divide-y divide-slate-800">
                        {filteredPayments.map((payment) => (
                          <tr key={payment.id}>
                            <td className="py-3 text-slate-100">#{payment.id}<p className="text-xs text-slate-500">Plan #{payment.plan_id}</p></td><td className="text-slate-300">{payment.tenant_id}</td><td className="text-slate-300">{payment.amount} {payment.currency}</td><td className="text-slate-300">{payment.payment_method}</td><td><StatusBadge status={payment.status} /></td>
                            <td className="space-x-3 text-right">
                              {["pending", "processing"].includes(payment.status) && <><button disabled={busy} onClick={() => void runAction(() => verifyAdminPayment(payment.id), `Payment #${payment.id} verified.`)} className="font-semibold text-emerald-300 disabled:opacity-50">Verify</button><button disabled={busy} onClick={() => void rejectPayment(payment)} className="font-semibold text-rose-300 disabled:opacity-50">Reject</button></>}
                              {payment.status === "verified" && <button disabled={busy} onClick={() => void runAction(() => refundAdminPayment(payment.id), `Payment #${payment.id} refunded.`)} className="font-semibold text-amber-300 disabled:opacity-50">Refund</button>}
                            </td>
                          </tr>
                        ))}
                        {!filteredPayments.length && <tr><td colSpan={6} className="py-5 text-slate-400">No {paymentFilter} payments found.</td></tr>}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section id="products" className="scroll-mt-6 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                  <h2 className="text-lg font-bold text-white">Products</h2>
                  <p className="mt-1 text-sm text-slate-400">Published product catalog and destination URLs.</p>
                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    {products.map((product) => (
                      <article id={`product-${product.product_key}`} key={product.product_key} className="scroll-mt-6 rounded-xl border border-slate-800 bg-[#080e18] p-5">
                        <p className="text-xs font-semibold uppercase tracking-wider text-cyan-300">{product.product_key}</p>
                        <h3 className="mt-2 font-bold text-white">{product.product_name}</h3>
                        <a href={product.url} target="_blank" rel="noreferrer" className="mt-3 inline-block break-all text-sm text-cyan-300 hover:underline">{product.url}</a>
                      </article>
                    ))}
                    {!products.length && <p className="text-sm text-slate-400">No products are configured.</p>}
                  </div>
                </section>

                <section id="audit-logs" className="scroll-mt-6 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                  <h2 className="text-lg font-bold text-white">Audit Logs</h2>
                  <p className="mt-1 text-sm text-slate-400">Latest subscription and payment activity across tenants.</p>
                  <ul className="mt-4 divide-y divide-slate-800">
                    {data.auditLogs.map((entry) => (
                      <li key={entry.id} className="flex flex-wrap justify-between gap-2 py-3 text-sm">
                        <span className="font-medium text-slate-200">{entry.action} · {entry.target_type} #{entry.target_id}</span>
                        <span className="text-slate-400">Tenant {entry.tenant_id} · {new Date(entry.created_at).toLocaleString()}</span>
                      </li>
                    ))}
                    {!data.auditLogs.length && <li className="py-3 text-sm text-slate-400">No audit activity yet.</li>}
                  </ul>
                </section>

                <section id="settings" className="scroll-mt-6 rounded-2xl border border-slate-800 bg-[#0d1726] p-6">
                  <h2 className="text-lg font-bold text-white">Global Settings</h2>
                  <p className="mt-1 text-sm text-slate-400">Manage subscription plan names, billing prices, currencies, cycles, and status. Only published products can be purchased. Changes apply to future purchases; existing subscriptions keep their agreed terms.</p>
                  <div className="mt-5 grid gap-4">
                    {plans.map((plan) => (
                      <form key={plan.id} onSubmit={(event) => void savePlan(event, plan)} className="grid gap-3 rounded-xl border border-slate-800 bg-[#080e18] p-4 sm:grid-cols-2 xl:grid-cols-6">
                        <div className="sm:col-span-2 xl:col-span-6"><p className="font-semibold text-white">{plan.product_key}</p><p className="text-xs text-slate-500">Plan ID {plan.id}</p></div>
                        <label className="grid gap-1 text-xs text-slate-400">Plan name<input name="name" required minLength={2} maxLength={200} defaultValue={plan.name} className="rounded-lg border border-slate-700 bg-[#0d1726] px-3 py-2 text-sm text-white" /></label>
                        <label className="grid gap-1 text-xs text-slate-400">Price<input name="monthly_price" type="number" min="0" max="100000000" step="0.01" required defaultValue={plan.monthly_price} className="rounded-lg border border-slate-700 bg-[#0d1726] px-3 py-2 text-sm text-white" /></label>
                        <label className="grid gap-1 text-xs text-slate-400">Currency<input name="currency" required minLength={3} maxLength={10} defaultValue={plan.currency} className="rounded-lg border border-slate-700 bg-[#0d1726] px-3 py-2 text-sm uppercase text-white" /></label>
                        <label className="grid gap-1 text-xs text-slate-400">Billing cycle<input name="billing_cycle" required minLength={2} maxLength={30} defaultValue={plan.billing_cycle} className="rounded-lg border border-slate-700 bg-[#0d1726] px-3 py-2 text-sm text-white" /></label>
                        <label className="grid gap-1 text-xs text-slate-400 sm:col-span-2 xl:col-span-6">Description<textarea name="description" maxLength={5000} defaultValue={plan.description} rows={2} className="rounded-lg border border-slate-700 bg-[#0d1726] px-3 py-2 text-sm text-white" /></label>
                        <label className="flex items-center gap-2 text-sm text-slate-300"><input name="is_active" type="checkbox" defaultChecked={plan.is_active} className="accent-cyan-300" />Plan active</label>
                        <button disabled={busy} className="rounded-lg bg-cyan-300 px-4 py-2 text-sm font-bold text-slate-950 disabled:opacity-50 sm:justify-self-start">Save plan settings</button>
                      </form>
                    ))}
                    {!plans.length && <p className="text-sm text-slate-400">No subscription plans are configured.</p>}
                  </div>
                </section>
              </>
            )}
          </div>
        </div>
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
