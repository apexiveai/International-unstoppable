"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import RequireAuth from "@/components/RequireAuth";
import { getClientProducts, type ClientProduct } from "@/lib/client";
import { getMyPayments, type CreatePaymentResponse } from "@/lib/payments";
import {
  getMySubscriptions,
  getProductAccess,
  type Subscription,
  type SubscriptionAccess,
} from "@/lib/subscriptions";

type ProductAccess = ClientProduct & SubscriptionAccess;

function ClientDashboard() {
  const [products, setProducts] = useState<ProductAccess[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [payments, setPayments] = useState<CreatePaymentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const [catalog, subscriptionList, paymentList] = await Promise.all([
          getClientProducts(),
          getMySubscriptions(),
          getMyPayments(),
        ]);
        const accessList = await Promise.all(
          catalog.map((product) => getProductAccess(product.product_key)),
        );
        if (!mounted) return;
        setProducts(
          catalog.map((product, index) => ({
            ...product,
            ...accessList[index],
          })),
        );
        setSubscriptions(subscriptionList);
        setPayments(paymentList.items);
      } catch (reason) {
        if (mounted) {
          setError(reason instanceof Error ? reason.message : "Unable to load your workspace.");
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const activeCount = products.filter((product) => product.has_access).length;
  const waitingPayments = payments.filter((payment) => payment.status === "pending").length;

  return (
    <main className="min-h-screen bg-slate-50">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4 px-6 py-10">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-600">Client workspace</p>
            <h1 className="mt-2 text-3xl font-bold text-slate-950">Your Apexive dashboard</h1>
            <p className="mt-2 text-sm text-slate-500">View product access, billing status, and subscription history.</p>
          </div>
          <Link href="/pricing" className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
            Browse plans
          </Link>
        </div>
      </section>
      <div className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        {error && (
          <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}
        {loading ? (
          <p className="py-16 text-center text-sm text-slate-500">Loading your workspace…</p>
        ) : !error ? (
          <>
            <section className="grid gap-4 sm:grid-cols-3">
              {[
                ["Products with access", activeCount],
                ["Subscriptions", subscriptions.length],
                ["Payments awaiting review", waitingPayments],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
                  <p className="mt-2 text-3xl font-bold text-slate-950">{value}</p>
                </div>
              ))}
            </section>

            <section>
              <div className="mb-4 flex items-end justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-slate-950">Product access</h2>
                  <p className="mt-1 text-sm text-slate-500">Product access is granted only after verified payment and activation.</p>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {products.map((product) => (
                  <article key={product.product_key} className="rounded-2xl border border-slate-200 bg-white p-6">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-bold text-slate-950">{product.product_name}</h3>
                        <p className="mt-1 text-xs text-slate-500">{product.product_key}</p>
                      </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-bold ${product.has_access ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>
                        {product.has_access ? "Access active" : product.status ?? "No subscription"}
                      </span>
                    </div>
                    <div className="mt-5">
                      {product.has_access ? (
                        <a href={product.url} target="_blank" rel="noreferrer" className="font-semibold text-blue-700 hover:underline">
                          Open product
                        </a>
                      ) : (
                        <Link href={`/pricing?product=${encodeURIComponent(product.product_key)}`} className="font-semibold text-blue-700 hover:underline">
                          View available plans
                        </Link>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-bold text-slate-950">Subscriptions</h2>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[600px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500">
                    <tr><th className="py-2">Product</th><th>Status</th><th>Billing</th><th>Period ends</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {subscriptions.map((subscription) => (
                      <tr key={subscription.id}>
                        <td className="py-3 font-medium text-slate-900">{subscription.plan.name}</td>
                        <td className="capitalize">{subscription.status}</td>
                        <td>{subscription.price} {subscription.currency} / {subscription.billing_cycle}</td>
                        <td>{subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : "—"}</td>
                      </tr>
                    ))}
                    {!subscriptions.length && <tr><td colSpan={4} className="py-4 text-slate-500">No subscriptions yet.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-bold text-slate-950">Payments</h2>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[600px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500">
                    <tr><th className="py-2">Payment</th><th>Amount</th><th>Method</th><th>Status</th><th>Created</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {payments.map((payment) => (
                      <tr key={payment.id}>
                        <td className="py-3">#{payment.id}</td>
                        <td>{payment.amount} {payment.currency}</td>
                        <td>{payment.payment_method}</td>
                        <td className="capitalize">{payment.status}</td>
                        <td>{new Date(payment.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                    {!payments.length && <tr><td colSpan={5} className="py-4 text-slate-500">No payment records yet.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        ) : null}
      </div>
    </main>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth nextPath="/dashboard">
      <ClientDashboard />
    </RequireAuth>
  );
}
