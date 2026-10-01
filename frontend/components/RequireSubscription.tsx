"use client";

import { useEffect, useState } from "react";

import Link from "next/link";

import {

  ArrowRight,

  CheckCircle2,

  CreditCard,

  Loader2,

  ShieldCheck,

} from "lucide-react";

import { getProductAccess } from "@/lib/subscriptions";

type RequireSubscriptionProps = {

  productKey: string;

  children: React.ReactNode;

};

const productNames: Record<string, string> = {

  trademark: "Trademark Intelligence",

  network: "Network Design & Quotation",

  workforce: "Autonomous Workforce",

  trademark_workforce: "Trademark + Workforce",

  telecom: "Telecom Network",

};

export default function RequireSubscription({

  productKey,

  children,

}: RequireSubscriptionProps) {

  const [loading, setLoading] = useState(true);

  const [hasAccess, setHasAccess] = useState(false);

  const [error, setError] = useState("");

  const productName =

    productNames[productKey] ?? "This Product";

  useEffect(() => {

    let mounted = true;

    async function checkAccess() {

      try {

        setLoading(true);

        setError("");

        const result =

          await getProductAccess(productKey);

        if (!mounted) {

          return;

        }

        setHasAccess(

          result.has_access === true &&

          (

            result.status === "active" ||

            result.status === "trialing"

          ),

        );

      } catch (err) {

        if (!mounted) {

          return;

        }

        setError(

          err instanceof Error

            ? err.message

            : "Unable to verify subscription.",

        );

        setHasAccess(false);

      } finally {

        if (mounted) {

          setLoading(false);

        }

      }

    }

    checkAccess();

    return () => {

      mounted = false;

    };

  }, [productKey]);

  if (loading) {

    return (

      <main className="min-h-screen bg-slate-50">

        <div className="flex min-h-[70vh] items-center justify-center px-6">

          <div className="text-center">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">

              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />

            </div>

            <p className="mt-5 text-sm font-medium text-slate-600">

              Verifying product access...

            </p>

            <p className="mt-1 text-xs text-slate-400">

              {productName}

            </p>

          </div>

        </div>

      </main>

    );

  }

  if (error) {

    return (

      <main className="min-h-screen bg-slate-50 px-6 py-16">

        <div className="mx-auto flex min-h-[65vh] max-w-xl items-center justify-center">

          <div className="w-full rounded-3xl border border-red-200 bg-white p-8 text-center shadow-sm">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50">

              <ShieldCheck className="h-7 w-7 text-red-600" />

            </div>

            <p className="mt-6 text-xs font-semibold uppercase tracking-[0.18em] text-red-500">

              Access Check

            </p>

            <h1 className="mt-2 text-2xl font-bold text-slate-950">

              Access Verification Failed

            </h1>

            <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-500">

              We could not verify your subscription for{" "}

              <span className="font-semibold text-slate-700">

                {productName}

              </span>

              .

            </p>

            <div className="mt-5 rounded-2xl bg-red-50 p-4 text-left text-xs leading-5 text-red-700">

              {error}

            </div>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:justify-center">

              <Link

                href={`/pricing?product=${encodeURIComponent(productKey)}`}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"

              >

                View Plans

                <ArrowRight className="h-4 w-4" />

              </Link>

              <Link

                href="/subscriptions"

                className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"

              >

                My Subscriptions

              </Link>

            </div>

          </div>

        </div>

      </main>

    );

  }

  if (!hasAccess) {

    return (

      <main className="min-h-screen bg-slate-50 px-6 py-16">

        <div className="mx-auto flex min-h-[65vh] max-w-2xl items-center justify-center">

          <div className="w-full rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-10">

            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50">

              <CreditCard className="h-8 w-8 text-blue-600" />

            </div>

            <p className="mt-7 text-xs font-semibold uppercase tracking-[0.2em] text-blue-600">

              Apexive Community

            </p>

            <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950">

              Subscription Required

            </h1>

            <p className="mx-auto mt-4 max-w-lg text-sm leading-7 text-slate-500">

              An active subscription is required to access{" "}

              <span className="font-semibold text-slate-800">

                {productName}

              </span>

              .

            </p>

            <div className="mx-auto mt-7 max-w-md rounded-2xl border border-slate-200 bg-slate-50 p-5 text-left">

              <div className="flex items-start gap-3">

                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-blue-600" />

                <div>

                  <p className="text-sm font-semibold text-slate-900">

                    Choose a subscription plan

                  </p>

                  <p className="mt-1 text-xs leading-5 text-slate-500">

                    Select the plan that includes{" "}

                    {productName} and complete checkout.

                  </p>

                </div>

              </div>

            </div>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">

              <Link

                href={`/pricing?product=${encodeURIComponent(productKey)}`}

                className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800"

              >

                View Plans

                <ArrowRight className="h-4 w-4" />

              </Link>

              <Link

                href="/subscriptions"

                className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"

              >

                My Subscriptions

              </Link>

            </div>

            <p className="mt-6 text-xs text-slate-400">

              Your account will receive access after verified payment

              and subscription activation.

            </p>

          </div>

        </div>

      </main>

    );

  }

  return <>{children}</>;

}