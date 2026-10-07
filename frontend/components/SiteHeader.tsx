"use client";

import Link from "next/link";

import Image from "next/image";

import { usePathname, useRouter } from "next/navigation";

import { useEffect, useState } from "react";

import { siteNavigationGroups } from "@/lib/site-navigation";

type StoredUser = {

  display_name?: string;

  username?: string;

  is_admin?: boolean;

};

const navItems = [
  { label: "Forums", href: "/forums" },
  { label: "Articles", href: "/articles" },
  { label: "Projects", href: "/projects" },
  { label: "Resources", href: "/resources" },
];

export default function SiteHeader() {

  const pathname = usePathname();

  const router = useRouter();

  const [user, setUser] = useState<StoredUser | null>(null);

  useEffect(() => {

    const readUser = () => {

      const storedUser = localStorage.getItem("apexive_user");

      if (!storedUser) {

        setUser(null);

        return;

      }

      try {

        setUser(JSON.parse(storedUser) as StoredUser);

      } catch {

        localStorage.removeItem("apexive_user");

        setUser(null);

      }

    };

    readUser();

    window.addEventListener("storage", readUser);

    return () => {

      window.removeEventListener("storage", readUser);

    };

  }, [pathname]);

  function logout() {

    localStorage.removeItem("apexive_token");

    localStorage.removeItem("apexive_user");

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
        

        {/* Brand */}

        <Link

          href="/"

          className="flex items-center gap-3"

        >

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

        {/* Desktop Navigation */}

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
                    {group.links.map((link) => (
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

        {/* Actions */}

        <div className="flex items-center gap-2">

          {user ? (

            <>
              <span className="hidden max-w-40 truncate rounded-lg bg-slate-800 px-3 py-2 text-sm font-semibold text-slate-200 md:inline-flex">

                {user.display_name || user.username}

              </span>

              <button

                type="button"

                onClick={logout}
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm font-medium text-slate-300 transition hover:border-red-400/40 hover:bg-red-500/10 hover:text-red-300"

              >

                Logout

              </button>

            </>

          ) : (

            <>

              <Link

                href="/login"

                className="hidden rounded-lg px-3 py-2 text-sm font-medium text-slate-400 transition hover:bg-slate-800 hover:text-slate-100 sm:inline-flex"

              >

                Login

              </Link>

              <Link

                href="/register"

                className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"

              >

                Join

              </Link>

            </>

          )}

        </div>

      </div>

      {/* Mobile Navigation */}
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
                    {group.links.map((link) => (
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