"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import SiteHeader from "@/components/SiteHeader";

export default function EditProjectPage() {
  const params = useParams<{ slug: string }>();

  return (
    <div className="min-h-screen bg-slate-50">
      <SiteHeader />
      <main className="mx-auto max-w-4xl px-6 py-12 lg:px-8">
        <Link href={`/projects/${params.slug}`} className="text-sm font-bold text-blue-600">
          ← Back to project
        </Link>
        <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-600">
            Project workspace
          </p>
          <h1 className="mt-3 text-3xl font-black text-[#172033]">Edit Project</h1>
          <p className="mt-3 text-slate-500">
            Update project details, links, status and showcase information.
          </p>
          <div className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            Editing is available to the project owner and administrators. Connect
            this form to the project update API before publishing changes.
          </div>
        </div>
      </main>
    </div>
  );
}
