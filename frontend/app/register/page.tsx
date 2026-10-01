"use client";

import Link from "next/link";

import {
  FormEvent,
  startTransition,
  useEffect,
  useRef,
  useState,
} from "react";

import { useRouter } from "next/navigation";
import AuthLayout from "@/components/AuthLayout";
import API_URL from "@/lib/api";

const PENDING_FACE_REGISTRATION_KEY = "apexive_pending_face_registration";

type PendingFaceRegistration = {
  username: string;
  display_name: string;
  email: string;
};

export default function RegisterPage() {

  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);

  const [username, setUsername] = useState("");

  const [displayName, setDisplayName] = useState("");

  const [email, setEmail] = useState("");

  const [password, setPassword] = useState("");

  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);
  const [faceLoading, setFaceLoading] = useState(false);
  const [faceSessionId, setFaceSessionId] = useState("");

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get("session_id");
    if (!sessionId) {
      return;
    }

    try {
      const pendingRegistration = sessionStorage.getItem(
        PENDING_FACE_REGISTRATION_KEY,
      );
      if (!pendingRegistration) {
        throw new Error("Registration details were not found. Please try again.");
      }

      const registration = JSON.parse(
        pendingRegistration,
      ) as PendingFaceRegistration;
      startTransition(() => {
        setUsername(registration.username);
        setDisplayName(registration.display_name);
        setEmail(registration.email);
        setFaceSessionId(sessionId);
        setError("");
      });
    } catch (restoreError) {
      startTransition(() => {
        setError(
          restoreError instanceof Error
            ? restoreError.message
            : "Unable to restore registration details.",
        );
      });
      router.replace("/register");
    }
  }, [router]);

  async function startFaceRegistration() {
    if (!formRef.current?.reportValidity()) {
      return;
    }

    setError("");
    setFaceLoading(true);

    try {
      const returnTo = `${window.location.origin}/register`;
      const response = await fetch(`${API_URL}/api/auth/face/session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim(),
          return_to: returnTo,
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to start face verification");
      }
      if (!data.verification_url) {
        throw new Error("Didit verification URL was not returned by the server.");
      }

      sessionStorage.setItem(
        PENDING_FACE_REGISTRATION_KEY,
        JSON.stringify({
          username,
          display_name: displayName,
          email: email.trim(),
        } satisfies PendingFaceRegistration),
      );
      window.location.href = data.verification_url;
    } catch (startError) {
      setError(
        startError instanceof Error
          ? startError.message
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
      const endpoint = faceSessionId
        ? `${API_URL}/api/auth/face/register/complete`
        : `${API_URL}/api/auth/register`;
      const response = await fetch(

        endpoint,

        {

          method: "POST",

          headers: {

            "Content-Type": "application/json",

          },

          body: JSON.stringify({

            username,

            display_name: displayName,

            email,

            password,

            ...(faceSessionId ? { session_id: faceSessionId } : {}),

          }),

        },

      );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(

          data.detail || "Registration failed",

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

      if (faceSessionId) {
        sessionStorage.removeItem(PENDING_FACE_REGISTRATION_KEY);
      }

      router.push("/");

    } catch (error) {

      setError(

        error instanceof Error

          ? error.message

          : "Registration failed",

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
            Join the community
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Create your developer community account.
          </p>
        </div>
        <form
          ref={formRef}
          onSubmit={handleSubmit}
          className="w-full"

        >

          {error && (

            <div className="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">

              {error}

            </div>

          )}

          {faceSessionId && (
            <div className="mb-5 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              Face verification is complete. Re-enter your password to finish creating your account.
            </div>
          )}

          <label className="block text-sm font-medium text-slate-700">

            Display name

          </label>

          <input

            value={displayName}

            onChange={(event) =>

              setDisplayName(event.target.value)

            }

            placeholder="Bhone Htet Naing"

            required

            className="mt-2 w-full rounded-lg border border-transparent bg-[#e8f0ff] px-4 py-3 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-100"

          />

          <label className="mt-5 block text-sm font-medium text-slate-700">

            Username

          </label>

          <input

            value={username}

            onChange={(event) =>

              setUsername(event.target.value)

            }

            placeholder="bhone"

            required

            minLength={3}

            className="mt-2 w-full rounded-lg border border-transparent bg-[#e8f0ff] px-4 py-3 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-100"

          />

          <label className="mt-5 block text-sm font-medium text-slate-700">

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

            className="mt-2 w-full rounded-lg border border-transparent bg-[#e8f0ff] px-4 py-3 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
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

            placeholder="Minimum 8 characters"

            autoComplete="new-password"

            minLength={8}

            required

            className="mt-2 w-full rounded-lg border border-transparent bg-[#e8f0ff] px-4 py-3 text-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-100"

          />

          <button

            type="submit"

            disabled={loading || faceLoading}

            className="mt-6 w-full rounded-lg bg-black py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"

          >

            {loading
              ? faceSessionId
                ? "Verifying and creating account..."
                : "Creating account..."
              : faceSessionId
                ? "Complete registration"
                : "Create account"}

          </button>

          {!faceSessionId && (
            <>
              <div className="my-6 flex items-center gap-3 text-xs text-slate-400">
                <span className="h-px flex-1 bg-slate-200" />
                <span>or verify your identity</span>
                <span className="h-px flex-1 bg-slate-200" />
              </div>

              <button
                type="button"
                onClick={startFaceRegistration}
                disabled={loading || faceLoading}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 py-3.5 text-sm font-semibold text-slate-900 transition hover:border-slate-500 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <span aria-hidden="true" className="text-lg">
                  ◉
                </span>
                {faceLoading
                  ? "Opening secure face verification..."
                  : "Register with face authentication"}
              </button>

              <p className="mt-3 text-center text-xs leading-5 text-slate-400">
                Secure identity verification powered by Didit.
              </p>
            </>
          )}

          <p className="mt-6 text-center text-sm text-slate-500">

            Already have an account?{" "}

            <Link

              href="/login"

              className="font-semibold text-slate-950 hover:underline"

            >

              Sign in

            </Link>

          </p>

        </form>

      </>
    </AuthLayout>

  );

}