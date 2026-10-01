"use client";

import Link from "next/link";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import API_URL from "@/lib/api";


type Thread = {

  id: number;

  title: string;

  slug: string;

  content: string;

  category_id: number;

  author_id: number;

  views: number;

  created_at: string;
  problem?: string | null;
  network_environment?: string | null;
  symptoms?: string | null;
  logs_alarms?: string | null;
  what_i_tried?: string | null;

};

type Reply = {

  id: number;

  content: string;

  thread_id: number;

  author_id: number;

  created_at: string;

};

export default function ThreadPage({

  params,

}: {

  params: Promise<{
    categorySlug: string;
    threadSlug: string;
  }>;
}) {
  const { categorySlug, threadSlug } = use(params);
  const router = useRouter();

  const [thread, setThread] =

    useState<Thread | null>(null);

  const [replies, setReplies] =

    useState<Reply[]>([]);

  const [replyText, setReplyText] =

    useState("");

  const [loading, setLoading] =

    useState(true);

  const [posting, setPosting] =

    useState(false);

  const [error, setError] =

    useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const threadResponse = await fetch(
          `${API_URL}/api/threads/by-slug/${encodeURIComponent(categorySlug)}/${encodeURIComponent(threadSlug)}`,
        );
        if (!threadResponse.ok) {
          throw new Error("Thread not found.");
        }

        const threadData: Thread = await threadResponse.json();
        if (cancelled) return;
        setThread(threadData);

        const replyResponse = await fetch(
          `${API_URL}/api/replies/thread/${threadData.id}`,
        );
        if (replyResponse.ok) {
          const replyData: Reply[] = await replyResponse.json();
          if (!cancelled) setReplies(replyData);
        }
      } catch (error) {
        if (!cancelled) {
          setError(
            error instanceof Error
              ? error.message
              : "Unable to load discussion.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [categorySlug, threadSlug]);

  async function submitReply() {

    if (!replyText.trim()) {

      return;

    }

    const token =

      localStorage.getItem("apexive_token");

    if (!token) {

      router.push(
        `/login?next=${encodeURIComponent(`/forums/${categorySlug}/${threadSlug}`)}`,
      );

      return;

    }

    if (!thread) {

      return;

    }

    setPosting(true);

    setError("");

    try {

      const response =

        await fetch(

          `${API_URL}/api/replies`,

          {

            method: "POST",

            headers: {

              "Content-Type": "application/json",

              Authorization: `Bearer ${token}`,

            },

            body: JSON.stringify({
              content: replyText.trim(),
              thread_id: thread.id,
            }),

          }

        );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(

          data.detail ||

            "Failed to post reply."

        );

      }

      setReplies((current) => [

        ...current,

        data,

      ]);

      setReplyText("");

    } catch (error) {

      setError(

        error instanceof Error

          ? error.message

          : "Unable to post reply."

      );

    } finally {

      setPosting(false);

    }

  }

  if (loading) {

    return (

      <main className="min-h-screen bg-slate-950 p-10 text-slate-400">

        Loading discussion...

      </main>

    );

  }

  if (!thread) {

    return (

      <main className="min-h-screen bg-slate-950 p-10 text-white">

        {error || "Discussion not found."}

      </main>

    );

  }

  return (

    <main className="min-h-screen bg-slate-950 text-white">

      <div className="mx-auto max-w-5xl px-6 py-10">

        <Link

          href={`/forums/${categorySlug}`}

          className="text-sm text-slate-500 hover:text-emerald-400"

        >

          ← Back to forum

        </Link>

        <article className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-7">

          <div className="flex flex-wrap gap-2">

            <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400">
              Discussion

            </span>


          </div>

          <h1 className="mt-5 text-3xl font-bold">

            {thread.title}

          </h1>

          <div className="mt-4 flex gap-4 text-sm text-slate-500">

            <span>

              {thread.views} views

            </span>

            <span>

              {new Date(

                thread.created_at

              ).toLocaleDateString()}

            </span>

          </div>

          <div className="mt-8 whitespace-pre-wrap leading-8 text-slate-300">

            {thread.content}

          </div>

        </article>

        {(thread.problem || thread.network_environment || thread.symptoms || thread.logs_alarms || thread.what_i_tried) && (
          <section className="mt-8 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-7">
            <h2 className="text-2xl font-bold">Network Troubleshooting</h2>
            <div className="mt-6 space-y-5">
              {([
                ["Problem", thread.problem],
                ["Network Environment", thread.network_environment],
                ["Symptoms", thread.symptoms],
                ["Logs / Alarms", thread.logs_alarms],
                ["What I Tried", thread.what_i_tried],
              ] as const).filter(([, value]) => value).map(([label, value]) => (
                <div key={label} className="border-l-2 border-emerald-500/60 pl-4">
                  <h3 className="font-semibold text-emerald-400">{label}</h3>
                  <p className="mt-2 whitespace-pre-wrap leading-7 text-slate-300">{value}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="mt-8">

          <div className="mb-4 flex items-center justify-between">

            <h2 className="text-2xl font-bold">

              Replies

            </h2>

            <span className="text-sm text-slate-500">

              {replies.length}

            </span>

          </div>

          <div className="space-y-4">

            {replies.map((reply) => (

              <article

                key={reply.id}

                className="rounded-2xl border border-slate-800 bg-slate-900 p-6"
              >
                <div className="whitespace-pre-wrap leading-7 text-slate-300">

                  {reply.content}

                </div>

                <div className="mt-5 text-xs text-slate-500">

                  Member #{reply.author_id}

                  {" · "}

                  {new Date(

                    reply.created_at

                  ).toLocaleDateString()}

                </div>

              </article>

            ))}

          </div>

          <div className="mt-8 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
            <h2 className="text-xl font-semibold text-emerald-400">Accepted Solution</h2>
            <p className="mt-2 text-sm text-slate-400">
              Community answers appear above. A verified fix can be promoted here as the accepted solution.
            </p>
          </div>

        </section>

          <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">

            <h2 className="text-xl font-semibold">

              Join the discussion

            </h2>

            <textarea

              value={replyText}

              onChange={(e) =>

                setReplyText(e.target.value)

              }

              rows={7}

              maxLength={30000}

              placeholder="Share your answer, experience, or solution..."

              className="mt-4 w-full resize-y rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 outline-none focus:border-emerald-500"

            />

            {error && (

              <div className="mt-4 rounded-xl bg-red-500/10 p-4 text-sm text-red-300">

                {error}

              </div>

            )}

            <button

              onClick={submitReply}

              disabled={

                posting ||

                !replyText.trim()

              }

              className="mt-4 rounded-xl bg-emerald-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"

            >

              {posting

                ? "Posting..."

                : "Post Reply"}

            </button>

          </section>

      </div>

    </main>

  );

}