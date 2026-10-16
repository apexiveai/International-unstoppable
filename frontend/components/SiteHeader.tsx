"use client";

import Link from "next/link";

import Image from "next/image";

import { usePathname, useRouter } from "next/navigation";

import { useEffect, useState } from "react";
import { UserRound } from "lucide-react";

import { getCurrentUser, type AuthenticatedUser } from "@/lib/auth";
import { siteNavigationGroups } from "@/lib/site-navigation";

const navItems = [
  { label: "Forums", href: "/forums" },
  { label: "Articles", href: "/articles" },
  { label: "Projects", href: "/projects" },
  { label: "Resources", href: "/resources" },
];

export default function SiteHeader() {

  const pathname = usePathname();

  const router = useRouter();

  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    let active = true;
    const verifyUser = async () => {
      const token = localStorage.getItem("apexive_token");
      if (!token) {
        if (active) {
          setUser(null);
          setAuthError("");
          setAuthReady(true);
        }
        return;
      }
      if (active) {
        setAuthReady(false);
        setAuthError("");
      }
      try {
        const verifiedUser = await getCurrentUser(token);
        if (!active) return;
        if (!verifiedUser) {
          localStorage.removeItem("apexive_token");
          localStorage.removeItem("apexive_user");
          setUser(null);
          return;
        }
        localStorage.setItem("apexive_user", JSON.stringify(verifiedUser));
        setUser(verifiedUser);
      } catch (reason) {
        if (active) {
          setUser(null);
          setAuthError(
            reason instanceof Error
              ? reason.message
              : "Unable to verify your account.",
          );
        }
      } finally {
        if (active) setAuthReady(true);
      }
    };
    const handleAuthChange = () => void verifyUser();
    void verifyUser();
    window.addEventListener("storage", handleAuthChange);
    window.addEventListener("apexive-auth-changed", handleAuthChange);
    return () => {
      active = false;
      window.removeEventListener("storage", handleAuthChange);
      window.removeEventListener("apexive-auth-changed", handleAuthChange);
    };
  }, [pathname]);

  function logout() {
    localStorage.removeItem("apexive_token");
    localStorage.removeItem("apexive_user");
    window.dispatchEvent(new Event("apexive-auth-changed"));
    setUser(null);
    router.replace("/");
  }

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-[#080e18]/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3">
          <Image
            src="/apexive-community-logo.png"
            alt="Apexive Community"
            width={40}
            height={40}
            className="h-10 w-10 rounded-xl object-cover"
          />
          <div className="hidden sm:block">
            <div className="text-sm font-bold tracking-tight text-slate-100">
              APEXIVE
            </div>
            <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-slate-400">
              Community
            </div>
          </div>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Main navigation">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                  active
                    ? "bg-cyan-400/10 text-cyan-300"
                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
          <details className="group relative">
            <summary className="flex cursor-pointer list-none items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-400 transition hover:bg-slate-800 hover:text-slate-100 [&::-webkit-details-marker]:hidden">
              More <span aria-hidden="true" className="text-xs">⌄</span>
            </summary>
            <div className="absolute right-0 top-full z-50 mt-2 grid w-[min(38rem,90vw)] grid-cols-3 gap-5 rounded-xl border border-slate-700 bg-[#0b1420] p-5 shadow-2xl">
              {siteNavigationGroups.map((group) => (
                <section key={group.label}>
                  <h2 className="mb-2 text-[11px] font-bold uppercase tracking-[0.14em] text-cyan-300">
                    {group.label}
                  </h2>
                  <ul className="space-y-1">
                    {group.links
                      .filter((link) =>
                        !user || !["Login", "Register"].includes(link.label),
                      )
                      .map((link) => (
                        <li key={link.href}>
                          <Link
                            href={link.href}
                            className={`block rounded-md px-2 py-1.5 text-sm transition ${
                              isActive(link.href)
                                ? "bg-cyan-400/10 text-cyan-300"
                                : "text-slate-300 hover:bg-slate-800 hover:text-white"
                            }`}
                          >
                            {link.label}
                          </Link>
                        </li>
                      ))}
                  </ul>
                </section>
              ))}
            </div>
          </details>
        </nav>

        <div className="flex items-center gap-2">
          {authReady && user ? (
            <details className="group relative">
              <summary className="flex cursor-pointer list-none items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-left transition hover:border-cyan-400/50 hover:bg-slate-800 [&::-webkit-details-marker]:hidden">
                <UserRound aria-hidden="true" className="h-5 w-5 shrink-0 text-cyan-300" />
                <span className="max-w-24 truncate text-sm font-semibold text-slate-100 sm:max-w-40">
                  {user.display_name || user.username}
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-300 sm:text-xs">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Signed in
                </span>
              </summary>
              <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-xl border border-slate-700 bg-[#0b1420] p-2 shadow-2xl">
                <Link href="/account" className="block rounded-lg px-3 py-2 text-sm text-slate-200 hover:bg-slate-800">
                  My Account
                </Link>
                <Link href="/dashboard" className="block rounded-lg px-3 py-2 text-sm text-slate-200 hover:bg-slate-800">
                  Dashboard
                </Link>
                <Link href="/subscriptions" className="block rounded-lg px-3 py-2 text-sm text-slate-200 hover:bg-slate-800">
                  My Subscriptions
                </Link>
                <button
                  type="button"
                  onClick={logout}
                  className="mt-1 w-full rounded-lg border-t border-slate-800 px-3 py-2 text-left text-sm text-red-300 hover:bg-red-500/10"
                >
                  Logout
                </button>
              </div>
            </details>
          ) : authReady && !authError ? (
            <>
              <Link
                href="/login"
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-400 transition hover:bg-slate-800 hover:text-slate-100"
              >
                Login
              </Link>
              <Link
                href="/register"
                className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
              >
                Register
              </Link>
            </>
          ) : authReady ? (
            <div className="flex items-center gap-2">
              <span className="hidden text-xs text-amber-300 sm:inline" title={authError}>
                Session not verified
              </span>
              <button
                type="button"
                onClick={() => window.dispatchEvent(new Event("apexive-auth-changed"))}
                className="rounded-lg px-2 py-2 text-xs text-amber-200 hover:bg-slate-800"
                aria-label={`Retry account verification: ${authError}`}
              >
                Retry
              </button>
            </div>
          ) : (
            <span className="px-3 py-2 text-xs text-slate-500">
              Checking session…
            </span>
          )}
        </div>
      </div>

      <nav className="border-t border-slate-800 lg:hidden" aria-label="Main navigation">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-1 px-4 py-2">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`shrink-0 rounded-lg px-3 py-2 text-xs font-medium transition ${
                  active
                    ? "bg-cyan-400/10 text-cyan-300"
                    : "text-slate-400 hover:bg-slate-800"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
          <details className="group relative shrink-0">
            <summary className="flex cursor-pointer list-none items-center gap-1 rounded-lg px-3 py-2 text-xs font-medium text-slate-400 [&::-webkit-details-marker]:hidden">
              More <span aria-hidden="true">⌄</span>
            </summary>
            <div className="absolute right-0 top-full z-50 mt-2 grid w-[min(38rem,90vw)] grid-cols-2 gap-4 rounded-xl border border-slate-700 bg-[#0b1420] p-4 shadow-2xl">
              {siteNavigationGroups.map((group) => (
                <section key={group.label}>
                  <h2 className="mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-cyan-300">
                    {group.label}
                  </h2>
                  <ul className="space-y-1">
                    {group.links
                      .filter((link) =>
                        !user || !["Login", "Register"].includes(link.label),
                      )
                      .map((link) => (
                        <li key={link.href}>
                          <Link
                            href={link.href}
                            className="block rounded-md px-2 py-1.5 text-xs text-slate-300 hover:bg-slate-800 hover:text-white"
                          >
                            {link.label}
                          </Link>
                        </li>
                      ))}
                  </ul>
                </section>
              ))}
            </div>
          </details>
        </div>
      </nav>
    </header>
  );
}