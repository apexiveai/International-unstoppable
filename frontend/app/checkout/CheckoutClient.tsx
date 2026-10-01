"use client";

import Link from "next/link";

import { useSearchParams } from "next/navigation";

import { useEffect, useMemo, useState } from "react";

import {

  ArrowLeft,

  Building2,

  CheckCircle2,

  CreditCard,

  Loader2,

  ShieldCheck,

  Wallet,

} from "lucide-react";

import {

  getSubscriptionPlans,

  type SubscriptionPlan,

} from "@/lib/subscriptions";

import {

  createPayment,

  type CreatePaymentResponse,

  type PaymentMethod,

} from "@/lib/payments";

const paymentMethods: {

  id: PaymentMethod;

  name: string;

  description: string;

  icon: typeof CreditCard;

}[] = [

    {

      id: "card",

      name: "Credit / Debit Card",

      description: "Visa, Mastercard and supported cards",

      icon: CreditCard,

    },

    {

      id: "kbzpay",

      name: "KBZPay",

      description: "Pay securely with KBZPay",

      icon: Wallet,

    },

    {

      id: "cbpay",

      name: "CB Pay",

      description: "Pay securely with CB Pay",

      icon: Wallet,

    },

    {

      id: "ayapay",

      name: "AYA Pay",

      description: "Pay securely with AYA Pay",

      icon: Wallet,

    },

    {

      id: "mpu",

      name: "MPU",

      description: "Myanmar Payment Union",

      icon: Building2,

    },

  ];

const productNames: Record<string, string> = {

  trademark: "Trademark Conflict",

  network: "Network Design & Quotation",

  workforce: "Autonomous Workforce",

  trademark_workforce: "Trademark + Workforce",

  telecom: "Telecom Network",

};

export default function CheckoutClient() {

  const searchParams = useSearchParams();

  const productKey = searchParams.get("product");

  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);

  const [plansLoading, setPlansLoading] = useState(true);

  const [plansError, setPlansError] = useState("");

  const [selectedMethod, setSelectedMethod] =

    useState<PaymentMethod>("card");

  const [payment, setPayment] =

    useState<CreatePaymentResponse | null>(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {

    let mounted = true;

    async function loadPlans() {

      try {

        setPlansLoading(true);

        setPlansError("");

        const result = await getSubscriptionPlans();

        if (!mounted) {

          return;

        }

        setPlans(result);

      } catch (err) {

        if (!mounted) {

          return;

        }

        setPlansError(

          err instanceof Error

            ? err.message

            : "Unable to load subscription plans.",

        );

      } finally {

        if (mounted) {

          setPlansLoading(false);

        }

      }

    }

    loadPlans();

    return () => {

      mounted = false;

    };

  }, []);

  const selectedPlan = useMemo(() => {

    if (!productKey) {

      return null;

    }

    return (

      plans.find(

        (plan) => plan.product_key === productKey,

      ) ?? null

    );

  }, [plans, productKey]);

  const productName =

    productKey && productNames[productKey]

      ? productNames[productKey]

      : selectedPlan?.name ?? "Apexive AI Product";

  async function handleContinue() {

    if (!selectedPlan) {

      setError(

        "The selected subscription plan could not be found.",

      );

      return;

    }

    setLoading(true);

    setError("");

    try {

      const result = await createPayment(

        selectedPlan.id,

        selectedMethod,

      );

      setPayment(result);

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Unable to create payment.",

      );

    } finally {

      setLoading(false);

    }

  }

  if (plansLoading) {

    return (

      <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">

        <div className="flex min-h-[70vh] items-center justify-center">

          <div className="text-center">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white/5">

              <Loader2 className="h-7 w-7 animate-spin text-cyan-400" />
            </div>

            <h1 className="mt-5 text-xl font-semibold">

              Loading Checkout

            </h1>

            <p className="mt-2 text-sm text-slate-400">

              Loading the latest subscription plan and pricing...

            </p>

          </div>

        </div>

      </main>

    );

  }

  if (plansError) {

    return (

      <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">

        <div className="mx-auto flex min-h-[70vh] max-w-xl items-center justify-center">

          <div className="w-full rounded-3xl border border-red-400/20 bg-white/[0.04] p-8 text-center">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-400/10">

              <ShieldCheck className="h-7 w-7 text-red-400" />

            </div>

            <h1 className="mt-5 text-2xl font-semibold">

              Checkout Unavailable

            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-400">

              We could not load the latest subscription

              information.

            </p>

            <div className="mt-5 rounded-2xl border border-red-400/10 bg-red-400/5 p-4 text-left text-sm text-red-300">

              {plansError}

            </div>

            <Link

              href="/pricing"

              className="mt-6 inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-950"

            >

              <ArrowLeft className="h-4 w-4" />

              Back to Pricing

            </Link>

          </div>

        </div>

      </main>

    );

  }

  if (!productKey || !selectedPlan) {

    return (

      <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">

        <div className="mx-auto flex min-h-[70vh] max-w-xl items-center justify-center">

          <div className="w-full rounded-3xl border border-white/10 bg-white/[0.04] p-8 text-center">

            <h1 className="text-2xl font-semibold">

              Subscription Plan Not Found

            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-400">

              The selected product is unavailable or no longer

              active.

            </p>

            <Link

              href="/pricing"

              className="mt-6 inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-950"

            >

              <ArrowLeft className="h-4 w-4" />

              Back to Pricing

            </Link>

          </div>

        </div>

      </main>

    );

  }

  if (payment) {

    return (

      <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">

        <div className="mx-auto max-w-2xl">

          <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8 shadow-2xl">

            <div className="flex flex-col items-center text-center">

              <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10">

                <CheckCircle2 className="h-9 w-9 text-emerald-400" />

              </div>

              <h1 className="text-2xl font-semibold">

                Payment Created

              </h1>

              <p className="mt-2 text-sm text-slate-400">

                Your payment session has been created.

              </p>

            </div>

            <div className="mt-8 space-y-4 rounded-2xl border border-white/10 bg-black/20 p-5">

              <div className="flex justify-between gap-4">

                <span className="text-slate-400">

                  Product

                </span>

                <span className="text-right font-medium">

                  {productName}

                </span>

              </div>

              <div className="flex justify-between gap-4">

                <span className="text-slate-400">

                  Amount

                </span>

                <span className="font-semibold">

                  {payment.currency} {payment.amount}
                </span>

              </div>

              <div className="flex justify-between gap-4">

                <span className="text-slate-400">

                  Payment Method

                </span>

                <span className="capitalize">

                  {payment.payment_method}

                </span>

              </div>

              <div className="border-t border-white/10 pt-4">

                <p className="text-xs text-slate-500">

                  Checkout Reference

                </p>

                <p className="mt-1 break-all font-mono text-sm text-cyan-300">

                  {payment.checkout_reference}

                </p>

              </div>

              <div className="flex justify-between gap-4">

                <span className="text-slate-400">

                  Status

                </span>

                <span className="rounded-full bg-amber-400/10 px-3 py-1 text-xs font-medium uppercase tracking-wide text-amber-300">

                  {payment.status}

                </span>

              </div>

            </div>

            <div className="mt-6 rounded-2xl border border-amber-400/10 bg-amber-400/5 p-4 text-sm leading-6 text-amber-200">

              Payment is currently pending verification.

              Subscription access will only be activated after

              verified payment confirmation.

            </div>

            <Link

              href="/pricing"

              className="mt-6 flex items-center justify-center gap-2 rounded-xl border border-white/10 px-4 py-3 text-sm font-medium transition hover:bg-white/5"

            >

              <ArrowLeft className="h-4 w-4" />

              Back to Pricing

            </Link>

          </div>

        </div>

      </main>

    );

  }

  const displayPrice = Number(

    selectedPlan.monthly_price,

  ).toFixed(2);

  return (

    <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">

      <div className="mx-auto max-w-5xl">

        <Link

          href="/pricing"

          className="mb-8 inline-flex items-center gap-2 text-sm text-slate-400 transition hover:text-white"

        >

          <ArrowLeft className="h-4 w-4" />

          Back to Pricing

        </Link>

        <div className="mb-10">

          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">

            Apexive AI

          </p>

          <h1 className="mt-3 text-3xl font-semibold tracking-tight">

            Secure Checkout

          </h1>

          <p className="mt-2 text-slate-400">

            Complete your subscription for{" "}

            <span className="font-medium text-slate-200">

              {productName}

            </span>

            .

          </p>

        </div>

        <div className="grid gap-8 lg:grid-cols-[1fr_360px]">

          <section>

            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">

              <h2 className="text-lg font-semibold">

                Payment Method

              </h2>

              <p className="mt-1 text-sm text-slate-400">

                Choose how you want to pay.

              </p>

              <div className="mt-6 space-y-3">

                {paymentMethods.map((method) => {

                  const Icon = method.icon;

                  const active =

                    selectedMethod === method.id;

                  return (

                    <button

                      key={method.id}

                      type="button"

                      onClick={() =>

                        setSelectedMethod(method.id)

                      }

                      className={`flex w-full items-center gap-4 rounded-2xl border p-4 text-left transition ${active

                          ? "border-cyan-400/60 bg-cyan-400/10"

                          : "border-white/10 bg-black/10 hover:border-white/20 hover:bg-white/[0.04]"

                        }`}

                    >

                      <div
                        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${active

                            ? "bg-cyan-400/15 text-cyan-300"

                            : "bg-white/5 text-slate-400"

                          }`}

                      >

                        <Icon className="h-5 w-5" />

                      </div>

                      <div className="flex-1">

                        <div className="font-medium">

                          {method.name}

                        </div>

                        <div className="mt-1 text-xs text-slate-500">

                          {method.description}

                        </div>

                      </div>

                      <div

                        className={`h-5 w-5 rounded-full border ${active

                            ? "border-cyan-400 bg-cyan-400"

                            : "border-slate-600"

                          }`}

                      />

                    </button>

                  );

                })}

              </div>

            </div>

            {error && (

              <div className="mt-5 rounded-2xl border border-red-400/20 bg-red-400/5 p-4 text-sm leading-6 text-red-300">

                {error}

              </div>

            )}

          </section>

          <aside>

            <div className="sticky top-8 rounded-3xl border border-white/10 bg-white/[0.04] p-6">

              <h2 className="text-lg font-semibold">

                Order Summary

              </h2>

              <div className="mt-6">

                <p className="text-sm text-slate-400">

                  Subscription

                </p>

                <p className="mt-2 text-xl font-semibold">

                  {productName}

                </p>

                <p className="mt-2 text-xs text-slate-500">

                  {selectedPlan.description}

                </p>

              </div>

              <div className="my-6 border-t border-white/10" />

              <div className="flex items-end justify-between">

                <div>

                  <p className="text-sm text-slate-400">

                    Monthly

                  </p>

                  <p className="mt-1 text-3xl font-bold">

                    {selectedPlan.currency} {displayPrice}

                  </p>

                </div>

                <span className="pb-1 text-sm text-slate-500">

                  / {selectedPlan.billing_cycle}

                </span>

              </div>

              <button

                type="button"

                onClick={handleContinue}

                disabled={loading}

                className="mt-7 flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50"

              >

                {loading ? (

                  <>

                    <Loader2 className="h-4 w-4 animate-spin" />

                    Creating Payment...

                  </>

                ) : (

                  "Continue to Payment"

                )}

              </button>

              <div className="mt-5 flex items-start gap-3 text-xs leading-5 text-slate-500">

                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />

                <p>

                  Payment information is handled through the

                  configured payment provider. Apexive does not

                  store raw card security data.

                </p>

              </div>

            </div>

          </aside>

        </div>

      </div>

    </main>

  );

}