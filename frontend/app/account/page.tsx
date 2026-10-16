"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import SiteHeader from "@/components/SiteHeader";
import { getCurrentUser, type AuthenticatedUser } from "@/lib/auth";

export default function AccountPage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function loadAccount() {
      const token = localStorage.getItem("apexive_token");
      if (!token) {
        router.replace("/login?next=%2Faccount");
        return;
      }
      try {
        const currentUser = await getCurrentUser(token);
        if (!active) return;
        if (!currentUser) {
          localStorage.removeItem("apexive_token");
          localStorage.removeItem("apexive_user");
          window.dispatchEvent(new Event("apexive-auth-changed"));
          router.replace("/login?next=%2Faccount");
          return;
        }
        setUser(currentUser);
      } catch (reason) {
        if (active) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Unable to load your account.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadAccount();
    return () => {
      active = false;
    };
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <SiteHeader />
      <main className="mx-auto max-w-4xl px-6 py-14">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">
          Account
        </p>
        <h1 className="mt-3 text-4xl font-bold">My Account</h1>
        {loading && <p className="mt-8 text-slate-400">Verifying your account…</p>}
        {error && (
          <p role="alert" className="mt-8 rounded-xl bg-red-500/10 p-4 text-red-300">
            {error}
          </p>
        )}
        {user && (
          <>
            <dl className="mt-8 grid gap-4 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:grid-cols-2">
              <div>
                <dt className="text-xs uppercase tracking-wider text-slate-500">Name</dt>
                <dd className="mt-1 text-slate-100">{user.display_name}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wider text-slate-500">Username</dt>
                <dd className="mt-1 text-slate-100">{user.username}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wider text-slate-500">Email</dt>
                <dd className="mt-1 text-slate-100">{user.email}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wider text-slate-500">Account status</dt>
                <dd className="mt-1 text-slate-100">{user.account_status}</dd>
              </div>
            </dl>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/dashboard"
                className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950"
              >
                Dashboard
              </Link>
              <Link
                href="/subscriptions"
                className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200"
              >
                My Subscriptions
              </Link>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
