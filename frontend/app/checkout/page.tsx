import { Suspense } from "react";

import CheckoutClient from "./CheckoutClient";

function CheckoutLoading() {

  return (

    <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">

      <div className="mx-auto max-w-5xl">

        <div className="animate-pulse">

          <div className="h-4 w-32 rounded bg-white/10" />

          <div className="mt-6 h-10 w-64 rounded bg-white/10" />

          <div className="mt-3 h-5 w-96 max-w-full rounded bg-white/10" />

          <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_360px]">

            <div className="h-[500px] rounded-3xl bg-white/[0.04]" />

            <div className="h-[380px] rounded-3xl bg-white/[0.04]" />

          </div>

        </div>

      </div>

    </main>

  );

}

export default function CheckoutPage() {

  return (

    <Suspense fallback={<CheckoutLoading />}>

      <CheckoutClient />

    </Suspense>

  );

}