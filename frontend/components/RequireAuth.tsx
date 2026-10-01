"use client";

import { useEffect, useSyncExternalStore } from "react";

import { useRouter } from "next/navigation";

type RequireAuthProps = {

  children: React.ReactNode;

  nextPath: string;

};

export default function RequireAuth({

  children,

  nextPath,

}: RequireAuthProps) {

  const router = useRouter();

  const authorized = useSyncExternalStore(
    (onStoreChange) => {
      window.addEventListener("storage", onStoreChange);
      return () => window.removeEventListener("storage", onStoreChange);
    },
    () => Boolean(localStorage.getItem("apexive_token")),
    () => false,
  );

  useEffect(() => {
    if (!authorized) {
      router.replace(
        `/login?next=${encodeURIComponent(nextPath)}`
      );
    }
  }, [authorized, router, nextPath]);

  if (!authorized) {

    return (

      <main className="min-h-screen bg-white flex items-center justify-center">

        <div className="text-center">

          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" />

          <p className="text-sm text-slate-500">

            Checking authentication...

          </p>

        </div>

      </main>

    );

  }

  return <>{children}</>;

}