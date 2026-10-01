"use client";

import Link from "next/link";

import { FormEvent, useEffect, useState } from "react";

import { useRouter } from "next/navigation";
import AuthLayout from "@/components/AuthLayout";
import API_URL from "@/lib/api";

export default function LoginPage() {

  const router = useRouter();

  const [email, setEmail] = useState("");

  const [password, setPassword] = useState("");

  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);

  const [faceLoading, setFaceLoading] = useState(false);

  /*

   * After Didit verification:

   * /login?session_id=xxxxxxxx

   *

   * The backend checks the Didit decision and returns

   * the normal Apexive JWT.

   */

  useEffect(() => {

    const params = new URLSearchParams(window.location.search);

    const sessionId = params.get("session_id");

    if (!sessionId) {

      return;

    }

    let cancelled = false;

    async function completeFaceAuthentication() {

      setFaceLoading(true);

      setError("");

      try {

        const response = await fetch(

          `${API_URL}/api/auth/face/complete`,

          {

            method: "POST",

            headers: {

              "Content-Type": "application/json",

            },

            body: JSON.stringify({

              session_id: sessionId,

            }),

          },

        );

        const data = await response.json();

        if (!response.ok) {

          throw new Error(

            data.detail || "Face verification was not approved",

          );

        }

        if (cancelled) {

          return;

        }

        localStorage.setItem(

          "apexive_token",

          data.access_token,

        );

        localStorage.setItem(

          "apexive_user",

          JSON.stringify(data.user),

        );

        const next = params.get("next") || "/";

        router.replace(next);

      } catch (verificationError: unknown) {

        if (!cancelled) {

          setError(

            verificationError instanceof Error

              ? verificationError.message

              : "Face verification failed",

          );

          setFaceLoading(false);

        }

      }

    }

    completeFaceAuthentication();

    return () => {

      cancelled = true;

    };

  }, [router]);

  async function startFaceAuthentication() {

    if (!email.trim()) {

      setError(

        "Enter your account email before starting face authentication.",

      );

      return;

    }

    setFaceLoading(true);

    setError("");

    try {

      const params = new URLSearchParams(window.location.search);

      const next = params.get("next") || "/";

      const returnTo =

        `${window.location.origin}/login?next=${encodeURIComponent(next)}`;

      const response = await fetch(

        `${API_URL}/api/auth/face/session`,

        {

          method: "POST",

          headers: {

            "Content-Type": "application/json",

          },

          body: JSON.stringify({

            email: email.trim(),

            return_to: returnTo,

          }),

        },

      );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(

          data.detail || "Unable to start face verification",

        );

      }

      if (!data.verification_url) {

        throw new Error(

          "Didit verification URL was not returned by the server.",

        );

      }

      /*

       * Open the secure Didit verification page.

       */

      window.location.href = data.verification_url;

    } catch (error: unknown) {

      setError(

        error instanceof Error

          ? error.message

          : "Unable to start face verification",

      );

      setFaceLoading(false);

    }

  }

  async function handleSubmit(

    event: FormEvent<HTMLFormElement>,

  ) {

    event.preventDefault();

    setError("");

    setLoading(true);

    try {

      const response = await fetch(

        `${API_URL}/api/auth/login`,

        {

          method: "POST",

          headers: {
            "Content-Type": "application/json",

          },

          body: JSON.stringify({

            email: email.trim(),

            password,

          }),

        },

      );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(

          data.detail || "Login failed",

        );

      }

      localStorage.setItem(

        "apexive_token",

        data.access_token,

      );

      localStorage.setItem(

        "apexive_user",

        JSON.stringify(data.user),

      );

      const params = new URLSearchParams(

        window.location.search,

      );

      const next = params.get("next") || "/";

      router.replace(next);

    } catch (error: unknown) {

      setError(

        error instanceof Error

          ? error.message

          : "Login failed",

      );

    } finally {

      setLoading(false);

    }

  }

  return (

    <AuthLayout>
      <>
        <div className="mb-7">
          <p className="text-xs font-medium tracking-wide text-slate-500">
            APEXIVE AI
          </p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
            Welcome back
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Sign in to your enterprise workspace.
          </p>
        </div>
        <form
          onSubmit={handleSubmit}
          className="w-full"
        >

          {error && (

            <div className="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">

              {error}

            </div>

          )}

          <label className="block text-sm font-medium text-slate-700">

            Email

          </label>

          <input

            type="email"

            value={email}

            onChange={(event) =>

              setEmail(event.target.value)

            }

            placeholder="you@example.com"

            required

            className="mt-2 w-full rounded-lg border border-transparent bg-[#e8f0ff] px-4 py-3 text-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"

          />

          <label className="mt-5 block text-sm font-medium text-slate-700">

            Password

          </label>

          <input

            type="password"

            value={password}

            onChange={(event) =>

              setPassword(event.target.value)

            }

            placeholder="••••••••"

            required

            className="mt-2 w-full rounded-lg border border-transparent bg-[#e8f0ff] px-4 py-3 text-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"

          />

          <button

            type="submit"

            disabled={loading || faceLoading}

            className="mt-3 w-full rounded-lg bg-black py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"

          >

            {loading ? "Signing in..." : "Sign in"}

          </button>

          <div className="my-6 flex items-center gap-3 text-xs text-slate-400">

            <span className="h-px flex-1 bg-slate-200" />

            <span>or</span>

            <span className="h-px flex-1 bg-slate-200" />

          </div>

          <button

            type="button"

            onClick={startFaceAuthentication}

            disabled={loading || faceLoading}

            className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 py-3.5 text-sm font-semibold text-slate-900 transition hover:border-slate-500 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"

          >

            <span

              aria-hidden="true"

              className="text-lg"

            >

              ◉

            </span>

            {faceLoading? "Opening secure face verification..."

              : "Continue with face authentication"}

          </button>

          <p className="mt-3 text-center text-xs leading-5 text-slate-400">

            Secure identity verification powered by Didit.

          </p>

          <p className="mt-6 text-center text-sm text-slate-500">

            Don&apos;t have an account?{" "}

            <Link

              href="/register"

              className="font-semibold text-slate-950 hover:underline"

            >

              Create one

            </Link>

          </p>

        </form>

      </>
    </AuthLayout>

  );

}