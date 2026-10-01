import Link from "next/link";

import SiteHeader from "@/components/SiteHeader";
import ProjectEngagement from "@/components/ProjectEngagement";

import { getProject } from "@/lib/api";

type Props = {

  params: Promise<{

    slug: string;

  }>;

};

export default async function ProjectDetailPage({

  params,

}: Props) {

  const { slug } = await params;

  let project;

  try {

    project = await getProject(slug);

  } catch {

    return (

      <div className="min-h-screen bg-white">

        <SiteHeader />

        <main className="mx-auto max-w-4xl px-6 py-24 text-center">

          <h1 className="text-3xl font-black text-[#172033]">

            Project not found

          </h1>

          <Link

            href="/projects"

            className="mt-6 inline-block font-bold text-blue-600"

          >

            ← Back to projects

          </Link>

        </main>

      </div>

    );

  }

  return (

    <div className="min-h-screen bg-white">

      <SiteHeader />

      <main className="mx-auto max-w-6xl px-6 py-12">

        <Link

          href="/projects"

          className="text-sm font-bold text-blue-600"

        >

          ← Back to projects

        </Link>

        <div className="mt-10 grid gap-10 lg:grid-cols-[1fr_320px]">

          <section>

            <div className="flex flex-wrap items-center gap-3">

              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">

                {project.status}

              </span>

              <span className="text-sm text-slate-400">

                ★ {project.stars}

              </span>

            </div>

            <h1 className="mt-5 text-4xl font-black tracking-tight text-[#172033] sm:text-5xl">

              {project.name}

            </h1>

            <p className="mt-5 text-lg leading-8 text-slate-500">

              {project.description}

            </p>

            <ProjectEngagement projectId={project.id} />

            <div className="my-10 h-px bg-slate-200" />

            <h2 className="text-2xl font-black text-[#172033]">

              About this project

            </h2>

            <div className="mt-5 whitespace-pre-wrap text-[17px] leading-8 text-slate-700">

              {project.content || project.description}

            </div>

            <div className="mt-10 flex flex-wrap gap-3">

              {project.repository_url && (

                <a

                  href={project.repository_url}

                  target="_blank"

                  rel="noreferrer"

                  className="rounded-xl bg-[#172033] px-5 py-3 text-sm font-bold text-white hover:bg-blue-600"

                >

                  Repository

                </a>

              )}

              {project.website_url && (

                <a

                  href={project.website_url}

                  target="_blank"

                  rel="noreferrer"

                  className="rounded-xl border border-slate-300 px-5 py-3 text-sm font-bold text-[#172033]"

                >

                  Website

                </a>

              )}

            </div>

            <div className="mt-10 grid gap-3 sm:grid-cols-3">
              <Link
                href={`/projects/${slug}/updates`}
                className="rounded-xl border border-slate-200 p-4 text-sm font-bold text-[#172033] hover:border-blue-300 hover:text-blue-600"
              >
                Project Updates →
              </Link>
              <Link
                href={`/projects/${slug}/team`}
                className="rounded-xl border border-slate-200 p-4 text-sm font-bold text-[#172033] hover:border-blue-300 hover:text-blue-600"
              >
                Contributors →
              </Link>
              <Link
                href={`/projects/${slug}/edit`}
                className="rounded-xl border border-slate-200 p-4 text-sm font-bold text-[#172033] hover:border-blue-300 hover:text-blue-600"
              >
                Edit Project →
              </Link>
            </div>

          </section>

          <aside className="h-fit rounded-2xl border border-slate-200 p-6">

            <h3 className="font-black text-[#172033]">

              Project Information

            </h3>

            <div className="mt-6 space-y-5 text-sm">

              <div>

                <div className="text-xs text-slate-400">

                  Category

                </div>

                <div className="mt-1 font-bold text-slate-700">

                  {project.category}

                </div>

              </div>

              <div>

                <div className="text-xs text-slate-400">

                  Stars

                </div>

                <div className="mt-1 font-bold text-slate-700">

                  {project.stars}

                </div>

              </div>

              <div>

                <div className="text-xs text-slate-400">

                  Views

                </div>

                <div className="mt-1 font-bold text-slate-700">

                  {project.views}
</div>

              </div>

              <div>

                <div className="text-xs text-slate-400">

                  Created

                </div>

                <div className="mt-1 font-bold text-slate-700">

                  {new Date(

                    project.created_at,

                  ).toLocaleDateString()}

                </div>

              </div>

            </div>

          </aside>

        </div>

      </main>

    </div>

  );

}