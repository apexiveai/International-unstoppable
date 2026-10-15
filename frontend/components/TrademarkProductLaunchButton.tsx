"use client";

import { useState } from "react";
import { ArrowRight, Loader2 } from "lucide-react";

import { createProductLaunch } from "@/lib/subscriptions";

export default function TrademarkProductLaunchButton() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function openDetector() {
    setLoading(true);
    setError("");
    try {
      const launch = await createProductLaunch("trademark");
      window.location.assign(launch.url);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to open Trademark Conflict Detector.",
      );
      setLoading(false);
    }
  }

  return (
    <div className="shrink-0">
      <button
        type="button"
        onClick={() => void openDetector()}
        disabled={loading}
        className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-6 py-4 text-sm font-semibold text-slate-950 transition hover:bg-slate-100 disabled:cursor-wait disabled:opacity-60"
      >
        {loading ? "Opening Detector…" : "Open Workspace"}
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <ArrowRight className="h-4 w-4" />
        )}
      </button>
      {error && (
        <p role="alert" className="mt-3 max-w-sm text-sm text-rose-300">
          {error}
        </p>
      )}
    </div>
  );
}
