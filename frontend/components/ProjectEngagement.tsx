"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import API_URL from "@/lib/api";

type Engagement = {
  likes: number;
  bookmarks: number;
  followers: number;
  liked: boolean;
  bookmarked: boolean;
  followed: boolean;
};

export default function ProjectEngagement({ projectId }: { projectId: number }) {
  const router = useRouter();
  const [engagement, setEngagement] = useState<Engagement | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/projects/${projectId}/engagement`)
      .then((response) => (response.ok ? response.json() : null))
      .then(setEngagement)
      .catch(() => setEngagement(null));
  }, [projectId]);

  async function toggle(action: "like" | "bookmark" | "follow") {
    const token = localStorage.getItem("apexive_token");
    if (!token) {
      router.push(`/login?next=${encodeURIComponent(window.location.pathname)}`);
      return;
    }
    const response = await fetch(`${API_URL}/api/projects/${projectId}/${action}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.ok) {
      setEngagement(await response.json());
    }
  }

  if (!engagement) {
    return null;
  }

  return (
    <div className="mt-8 flex flex-wrap gap-3">
      <button type="button" onClick={() => toggle("like")} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold hover:border-blue-300">
        {engagement.liked ? "♥ Liked" : "♡ Like"} · {engagement.likes}
      </button>
      <button type="button" onClick={() => toggle("bookmark")} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold hover:border-blue-300">
        {engagement.bookmarked ? "★ Saved" : "☆ Save"} · {engagement.bookmarks}
      </button>
      <button type="button" onClick={() => toggle("follow")} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold hover:border-blue-300">
        {engagement.followed ? "Following" : "Follow"} · {engagement.followers}
      </button>
    </div>
  );
}
