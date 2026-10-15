"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import {

  getSubscriptionPlans,

  getMySubscriptions,

  type SubscriptionPlan,

  type Subscription,

} from "@/lib/subscriptions";

export default function PricingPage() {

  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);

  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [currentTime, setCurrentTime] = useState<number | null>(null);

  const router = useRouter();

  useEffect(() => {

    async function load() {

      try {

        const [planData, subscriptionData] = await Promise.all([
          getSubscriptionPlans(),
          localStorage.getItem("apexive_token")
            ? getMySubscriptions()
            : Promise.resolve<Subscription[]>([]),
        ]);

        const productFilter = new URLSearchParams(window.location.search).get("product");
        setPlans(
          productFilter
            ? planData.filter((plan) => plan.product_key === productFilter)
            : planData,
        );

        setSubscriptions(subscriptionData);

      } catch (err) {

        setError(

          err instanceof Error

            ? err.message

            : "Unable to load subscription plans.",

        );

      } finally {

        setCurrentTime(Date.now());

        setLoading(false);

      }

    }

    load();

  }, []);

function handleSubscribe(plan: {

  id: number;

  product_key: string;

}) {

  router.push(

    `/checkout?product=${encodeURIComponent(plan.product_key)}`

  );

}

  function hasActiveSubscription(productKey: string) {
    if (currentTime === null) return false;

    return subscriptions.some(

      (subscription) =>
        subscription.plan.product_key === productKey
        && ["active", "trialing"].includes(subscription.status)
        && (!subscription.current_period_end
          || new Date(subscription.current_period_end).getTime() > currentTime)
        && (!subscription.contract_end
          || new Date(subscription.contract_end).getTime() > currentTime)

    );

  }

  if (loading) {

    return (

      <main className="min-h-screen bg-slate-50">

        <div className="mx-auto flex min-h-[70vh] max-w-7xl items-center justify-center px-6">

          <div className="text-center">

            <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" />

            <p className="text-sm text-slate-500">

              Loading subscription plans...

            </p>

          </div>

        </div>

      </main>

    );

  }

  return (

    <main className="min-h-screen bg-slate-50">

      <section className="border-b border-slate-200 bg-white">

        <div className="mx-auto max-w-7xl px-6 py-16 text-center">

          <div className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">

            APEXIVE AI

          </div>

          <h1 className="text-4xl font-bold tracking-tight text-[#172033] md:text-5xl">

            Choose your AI workspace

          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-slate-500">

            Subscribe to the Apexive AI products your organization needs.

            Manage all subscriptions from one central workspace.

          </p>

          <div className="mt-6">

            <Link

              href="/subscriptions"

              className="text-sm font-semibold text-blue-600 hover:text-blue-700"

            >

              View My Subscriptions →

            </Link>

          </div>

        </div>

      </section>

      {error && (

        <div className="mx-auto mt-6 max-w-7xl px-6">

          <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">

            {error}

          </div>

        </div>

      )}

      <section className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">

          {plans.map((plan) => {

            const active = hasActiveSubscription(plan.product_key);
            const monthlyPrice = Number(plan.monthly_price);
            const formattedMonthlyPrice = new Intl.NumberFormat("en-US", {
              maximumFractionDigits: 2,
            }).format(monthlyPrice);
            const contractCommitment =
              plan.minimum_contract_months === null
                ? null
                : new Intl.NumberFormat("en-US", {
                    maximumFractionDigits: 2,
                  }).format(monthlyPrice * plan.minimum_contract_months);

            return (

              <article

                key={plan.id}
                className={`relative flex flex-col rounded-2xl border bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg ${plan.product_key === "trademark_workforce"

                    ? "border-blue-300 ring-2 ring-blue-50"

                    : "border-slate-200"

                  }`}

              >

                {plan.product_key === "trademark_workforce" && (

                  <div className="absolute -top-3 left-6 rounded-full bg-blue-600 px-3 py-1 text-xs font-bold text-white">

                    COMBINED

                  </div>

                )}

                <div>

                  <h2 className="text-xl font-bold text-[#172033]">

                    {plan.name}

                  </h2>

                  <p className="mt-3 min-h-14 text-sm leading-6 text-slate-500">

                    {plan.description}

                  </p>

                </div>

                <div className="mt-7">

                  <span className="text-4xl font-bold tracking-tight text-[#172033]">

                    {plan.currency} {formattedMonthlyPrice}

                  </span>

                  <span className="ml-2 text-sm text-slate-500">

                    / month

                  </span>

                </div>

                {plan.minimum_contract_months !== null && (
                  <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
                    Minimum {plan.minimum_contract_months}-month contract,
                    billed monthly. Total contract commitment: {plan.currency}{" "}
                    {contractCommitment}.
                  </div>
                )}

                <div className="mt-5 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">

                  Billing cycle:{" "}

                  <span className="font-semibold">

                    {plan.billing_cycle}

                  </span>

                </div>

                <div className="mt-auto pt-7">

                  {active ? (

                    <Link

                      href="/subscriptions"

                      className="flex w-full items-center justify-center rounded-xl bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700 transition hover:bg-emerald-100"

                    >

                      ✓ Active — Manage Subscription

                    </Link>

                  ) : (

                    <button

                      type="button"

                      onClick={() => handleSubscribe(plan)}

                      className="flex w-full items-center justify-center rounded-xl bg-[#172033] px-4 py-3 text-sm font-bold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"

                    >

                      {`Subscribe for ${plan.currency} ${formattedMonthlyPrice}/month`}

                    </button>

                  )}

                </div>

              </article>

            );

          })}
        </div>
        {plans.length === 0 && !error && (
          <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-8 text-center">
            <h2 className="text-lg font-semibold text-slate-900">Plans are being prepared</h2>
            <p className="mt-2 text-sm text-slate-500">
              New product plans will appear here once pricing is confirmed.
            </p>
          </div>
        )}
      </section>

    </main>

  );

}