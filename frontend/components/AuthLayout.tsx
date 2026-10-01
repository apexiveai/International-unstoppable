import type { ReactNode } from "react";
import Link from "next/link";

type AuthLayoutProps = {
  children: ReactNode;
};

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <main className="flex min-h-screen flex-col bg-white md:flex-row">
      <section className="relative flex min-h-36 flex-col justify-between bg-black px-6 py-6 text-white md:min-h-screen md:w-1/2 md:px-8 md:py-8 lg:px-12 lg:py-10">
        <div>
          <Link
            href="/"
            className="text-lg font-bold tracking-tight text-white"
          >
            APEXIVE AI
          </Link>
          <p className="mt-1 text-xs text-slate-400">
            Autonomous Enterprise Intelligence &amp; Execution Infrastructure
          </p>
        </div>

        <div className="my-8 hidden max-w-xl md:my-0 md:block">
          <div className="mb-5 h-px w-14 bg-slate-500" />
          <h2 className="text-3xl font-bold leading-tight tracking-tight text-white lg:text-4xl">
            From enterprise goals
            <br />
            to governed execution.
          </h2>
          <p className="mt-5 max-w-md text-sm leading-6 text-slate-400">
            Plan, execute, verify, recover and audit enterprise work with
            governed AI agents.
          </p>
        </div>

        <p className="hidden text-xs text-slate-500 md:block">
          © Apexive AI
        </p>
      </section>

      <section className="flex flex-1 items-center justify-center px-6 py-12 md:px-10 md:py-16">
        <div className="w-full max-w-sm">{children}</div>
      </section>
    </main>
  );
}
