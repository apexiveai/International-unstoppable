"use client";

import Link from "next/link";

import Image from "next/image";

import { usePathname, useRouter } from "next/navigation";

import { useEffect, useState } from "react";

type StoredUser = {

  display_name?: string;

  username?: string;

};

const navItems = [

  { label: "Forums", href: "/forums" },

  { label: "Articles", href: "/articles" },

  { label: "Projects", href: "/projects" },

  { label: "Resources", href: "/resources" },

  { label: "Trademark Intelligence", href: "/trademark-intelligence" },

  { label: "Workforce", href: "/workforce" },

  { label: "Pricing", href: "/pricing" },

  { label: "History", href: "/history" },

  { label: "Search", href: "/search" },

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

  }, []);

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

        <nav className="hidden items-center gap-1 lg:flex">

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

      <div className="border-t border-slate-800 lg:hidden">

        <div className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 py-2">

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

        </div>

      </div>

    </header>

  );

}