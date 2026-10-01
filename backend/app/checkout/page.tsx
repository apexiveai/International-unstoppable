"use client";

import Link from "next/link";

import { useSearchParams } from "next/navigation";

import { useState } from "react";

import {

  CreditCard,

  Wallet,

  Building2,

  ShieldCheck,

  ArrowLeft,

  CheckCircle2,

  Loader2,

} from "lucide-react";

import {

  createPayment,

  type PaymentMethod,

  type CreatePaymentResponse,

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

const productPrices: Record<string, number> = {

  trademark: 249,

  network: 199,

  workforce: 299,

  trademark_workforce: 499,

  telecom: 399,

};

export default function CheckoutPage() {

  const searchParams = useSearchParams();

  const productKey = searchParams.get("product") || "trademark";

  const productName =

    productNames[productKey] || "Trademark Conflict";

  const price =

    productPrices[productKey] ?? 249;

  const planIdMap: Record<string, number> = {

    trademark: 1,

    network: 2,

    workforce: 3,

    trademark_workforce: 4,

    telecom: 5,

  };

  const planId =

    planIdMap[productKey] || 1;

  const [selectedMethod, setSelectedMethod] =

    useState<PaymentMethod>("card");

  const [loading, setLoading] =

    useState(false);

  const [payment, setPayment] =

    useState<CreatePaymentResponse | null>(null);

  const [error, setError] =

    useState("");

  async function handleContinue() {

    setLoading(true);

    setError("");

    try {

      const result = await createPayment(

        planId,

        selectedMethod,

      );

      setPayment(result);

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Unable to create payment",

      );

    } finally {

      setLoading(false);

    }

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

                <span className="font-medium">

                  {productName}

                </span>

              </div>

              <div className="flex justify-between gap-4">

                <span className="text-slate-400">

                  Amount

                </span>

                <span className="font-semibold">

                  ${payment.amount} {payment.currency}

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

            <div className="mt-6 rounded-2xl border border-amber-400/10 bg-amber-400/5 p-4 text-sm text-amber-200">

              Real payment gateway integration will process this

              checkout reference. Subscription access will only be

              activated after verified payment confirmation.

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

            Select your preferred payment method.

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

                      className={`flex w-full items-center gap-4 rounded-2xl border p-4 text-left transition ${

                        active

                          ? "border-cyan-400/60 bg-cyan-400/10"

                          : "border-white/10 bg-black/10 hover:border-white/20 hover:bg-white/[0.04]"

                      }`}

                    >

                      <div

                        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${

                          active
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

                        className={`h-5 w-5 rounded-full border ${

                          active

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

              <div className="mt-5 rounded-2xl border border-red-400/20 bg-red-400/5 p-4 text-sm text-red-300">

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

              </div>

              <div className="my-6 border-t border-white/10" />

              <div className="flex items-end justify-between">

                <div>

                  <p className="text-sm text-slate-400">

                    Monthly

                  </p>

                  <p className="mt-1 text-3xl font-bold">

                    ${price}

                  </p>

                </div>

                <span className="pb-1 text-sm text-slate-500">

                  USD / month

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

                  <>

                    Continue to Payment

                  </>

                )}

              </button>

              <div className="mt-5 flex items-start gap-3 text-xs text-slate-500">

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