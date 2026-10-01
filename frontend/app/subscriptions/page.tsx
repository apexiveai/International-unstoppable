"use client";

import { useEffect, useState } from "react";

import Link from "next/link";

import {

  ArrowRight,

  CalendarDays,

  CheckCircle2,

  CreditCard,

  Loader2,

  XCircle,

} from "lucide-react";

import {

  cancelSubscription,

  getMySubscriptions,

  type Subscription,

} from "@/lib/subscriptions";

const productNames: Record<string, string> = {

  trademark: "Trademark Intelligence",

  network: "Network Design & Quotation",

  workforce: "Autonomous Workforce",

  trademark_workforce: "Trademark + Workforce",

  telecom: "Telecom Network",

};

function formatDate(value: string | null) {

  if (!value) {

    return "—";

  }

  return new Date(value).toLocaleDateString("en-US", {

    year: "numeric",

    month: "short",

    day: "numeric",

  });

}

function getStatusClass(status: string) {

  switch (status) {

    case "active":

    case "trialing":

      return "bg-emerald-50 text-emerald-700 border-emerald-200";

    case "cancelled":

    case "canceled":

      return "bg-amber-50 text-amber-700 border-amber-200";

    case "expired":

      return "bg-red-50 text-red-700 border-red-200";

    default:

      return "bg-slate-50 text-slate-600 border-slate-200";

  }

}

export default function SubscriptionsPage() {

  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [cancellingId, setCancellingId] = useState<number | null>(null);

  function handleRetry() {
    setLoading(true);
    setError("");
    void getMySubscriptions()
      .then(setSubscriptions)
      .catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load your subscriptions.",
        );
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {

    let isMounted = true;

    getMySubscriptions()
      .then((result) => {
        if (isMounted) {
          setSubscriptions(result);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load your subscriptions.",
          );
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };

  }, []);

  async function handleCancel(subscriptionId: number) {

    const confirmed = window.confirm(

      "Are you sure you want to cancel this subscription?",

    );

    if (!confirmed) {

      return;

    }

    try {

      setCancellingId(subscriptionId);
      await cancelSubscription(subscriptionId);
      setSubscriptions(await getMySubscriptions());
      setError("");

    } catch (err) {

      window.alert(

        err instanceof Error

          ? err.message

          : "Unable to cancel subscription.",

      );

    } finally {

      setCancellingId(null);

    }

  }

  const activeSubscriptions = subscriptions.filter(

    (subscription) =>

      subscription.status === "active" ||

      subscription.status === "trialing",

  );

  return (

    <main className="min-h-screen bg-slate-50">

      <section className="border-b border-slate-200 bg-white">

        <div className="mx-auto max-w-6xl px-6 py-14">

          <div className="max-w-3xl">

            <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-600">

              Apexive Community

            </p>

            <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-950">

              My Subscriptions

            </h1>

            <p className="mt-4 text-sm leading-7 text-slate-500">

              Manage your active Apexive Community products,

              subscription periods, and billing status.

            </p>

          </div>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">

            <Link

              href="/pricing"

              className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"

            >

              View Plans

              <ArrowRight className="h-4 w-4" />

            </Link>

            <Link

              href="/"

              className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"

            >

              Back to Community
            </Link>

          </div>

        </div>

      </section>

      <section className="mx-auto max-w-6xl px-6 py-10">

        {loading && (

          <div className="flex min-h-[45vh] items-center justify-center">

            <div className="text-center">

              <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-600" />

              <p className="mt-4 text-sm text-slate-500">

                Loading your subscriptions...

              </p>

            </div>

          </div>

        )}

        {!loading && error && (

          <div className="rounded-3xl border border-red-200 bg-white p-8 text-center shadow-sm">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50">

              <XCircle className="h-7 w-7 text-red-600" />

            </div>

            <h2 className="mt-5 text-xl font-bold text-slate-950">

              Unable to load subscriptions

            </h2>

            <p className="mt-3 text-sm text-red-600">

              {error}

            </p>

            <button

              type="button"

              onClick={handleRetry}

              className="mt-6 rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white"

            >

              Try Again

            </button>

          </div>

        )}

        {!loading && !error && (

          <>

            <div className="grid gap-4 sm:grid-cols-3">

              <div className="rounded-2xl border border-slate-200 bg-white p-5">

                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">

                  Total

                </p>

                <p className="mt-2 text-3xl font-bold text-slate-950">

                  {subscriptions.length}

                </p>

              </div>

              <div className="rounded-2xl border border-emerald-200 bg-white p-5">

                <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">

                  Active

                </p>

                <p className="mt-2 text-3xl font-bold text-slate-950">

                  {activeSubscriptions.length}

                </p>

              </div>

              <div className="rounded-2xl border border-blue-200 bg-white p-5">

                <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">

                  Available Products

                </p>

                <p className="mt-2 text-3xl font-bold text-slate-950">

                  5

                </p>

              </div>

            </div>

            {subscriptions.length === 0 ? (

              <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">

                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50">

                  <CreditCard className="h-8 w-8 text-blue-600" />

                </div>

                <h2 className="mt-6 text-2xl font-bold text-slate-950">

                  No subscriptions yet

                </h2>

                <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-500">

                  Choose an Apexive Community product to start

                  using the platform.

                </p>

                <Link

                  href="/pricing"

                  className="mt-7 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-blue-700"

                >

                  Explore Plans

                  <ArrowRight className="h-4 w-4" />

                </Link>

              </div>

            ) : (

              <div className="mt-8 space-y-5">

                {subscriptions.map((subscription) => {

                  const productKey =

                    subscription.plan.product_key;

                  const productName =

                    productNames[productKey] ??

                    subscription.plan.name;

                  const active =
                    subscription.status === "active" ||

                    subscription.status === "trialing";

                  return (

                    <div

                      key={subscription.id}

                      className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"

                    >

                      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">

                        <div>

                          <div className="flex flex-wrap items-center gap-3">

                            <h2 className="text-xl font-bold text-slate-950">

                              {productName}

                            </h2>

                            <span

                              className={`rounded-full border px-3 py-1 text-xs font-bold uppercase ${getStatusClass(

                                subscription.status,

                              )}`}

                            >

                              {subscription.status}

                            </span>

                          </div>

                          <p className="mt-2 text-sm text-slate-500">

                            {subscription.plan.name}

                          </p>

                        </div>

                        <div className="flex items-center gap-2 rounded-2xl bg-slate-50 px-4 py-3">

                          {active ? (

                            <CheckCircle2 className="h-5 w-5 text-emerald-600" />

                          ) : (

                            <XCircle className="h-5 w-5 text-slate-400" />

                          )}

                          <span className="text-sm font-semibold text-slate-700">

                            {active

                              ? "Access Enabled"

                              : "Access Inactive"}

                          </span>

                        </div>

                      </div>

                      <div className="mt-7 grid gap-4 border-t border-slate-100 pt-6 sm:grid-cols-2 lg:grid-cols-4">

                        <div>

                          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">

                            Price

                          </p>

                          <p className="mt-2 text-sm font-bold text-slate-900">

                            {subscription.currency}{" "}

                            {Number(subscription.price).toFixed(2)}

                            <span className="ml-1 font-normal text-slate-400">

                              /{subscription.billing_cycle}

                            </span>

                          </p>

                        </div>

                        <div>

                          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">

                            Started

                          </p>

                          <p className="mt-2 flex items-center gap-2 text-sm font-semibold text-slate-700">

                            <CalendarDays className="h-4 w-4 text-slate-400" />

                            {formatDate(subscription.start_date)}

                          </p>

                        </div>

                        <div>

                          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">

                            Current Period End

                          </p>

                          <p className="mt-2 text-sm font-semibold text-slate-700">

                            {formatDate(

                              subscription.current_period_end,

                            )}

                          </p>

                        </div>

                        <div>

                          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">

                            Subscription ID

                          </p>

                          <p className="mt-2 text-sm font-semibold text-slate-700">
                            #{subscription.id}

                          </p>

                        </div>

                      </div>

                      {active && (

                        <div className="mt-6 flex justify-end">

                          <button

                            type="button"

                            disabled={

                              cancellingId === subscription.id

                            }

                            onClick={() =>

                              handleCancel(subscription.id)

                            }

                            className="rounded-xl border border-red-200 bg-white px-4 py-2.5 text-sm font-semibold text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"

                          >

                            {cancellingId === subscription.id

                              ? "Cancelling..."

                              : "Cancel Subscription"}

                          </button>

                        </div>

                      )}

                    </div>

                  );

                })}

              </div>

            )}

          </>

        )}

      </section>

    </main>

  );

}