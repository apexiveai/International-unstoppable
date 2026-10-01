import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";

type Props = { params: Promise<{ slug: string }> };

export default async function ProjectTeamPage({ params }: Props) {
  const { slug } = await params;
  return (
    <div className="min-h-screen bg-white">
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-6 py-12 lg:px-8">
        <Link href={`/projects/${slug}`} className="text-sm font-bold text-blue-600">
          ← Back to project
        </Link>
        <p className="mt-10 text-xs font-black uppercase tracking-[0.18em] text-blue-600">
          Collaboration
        </p>
        <h1 className="mt-3 text-4xl font-black text-[#172033]">Project Contributors</h1>
        <p className="mt-4 text-slate-500">
          Meet the people building and maintaining this project.
        </p>
        <div className="mt-10 rounded-2xl border border-dashed border-slate-300 p-12 text-center">
          <h2 className="text-xl font-black text-[#172033]">Contributors coming soon</h2>
          <p className="mt-2 text-sm text-slate-500">
            Contributor invitations and roles will appear in this workspace.
          </p>
        </div>
      </main>
    </div>
  );
}
