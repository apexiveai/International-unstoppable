import Link from "next/link";

import SiteHeader from "@/components/SiteHeader";

import { getResource } from "@/lib/api";

type Props = {

  params: Promise<{

    slug: string;

  }>;

};

export default async function ResourceDetailPage({

  params,

}: Props) {

  const { slug } = await params;

  let resource;

  try {

    resource = await getResource(slug);

  } catch {

    return (

      <div className="min-h-screen bg-white">

        <SiteHeader />

        <main className="mx-auto max-w-4xl px-6 py-24 text-center">

          <h1 className="text-3xl font-black text-[#172033]">

            Resource not found

          </h1>

          <Link

            href="/resources"

            className="mt-6 inline-block font-bold text-blue-600"

          >

            ← Back to resources

          </Link>

        </main>

      </div>

    );

  }

  return (

    <div className="min-h-screen bg-white">

      <SiteHeader />

      <main className="mx-auto max-w-5xl px-6 py-12">

        <Link

          href="/resources"

          className="text-sm font-bold text-blue-600"

        >

          ← Back to resources

        </Link>

        <article className="mt-10">

          <div className="flex flex-wrap items-center gap-3">

            <span className="rounded-lg bg-blue-50 px-3 py-1 text-xs font-bold text-blue-600">

              {resource.resource_type}

            </span>

            <span className="text-sm text-slate-400">

              {resource.category}

            </span>

          </div>

          <h1 className="mt-5 text-4xl font-black tracking-tight text-[#172033] sm:text-5xl">

            {resource.title}

          </h1>

          <p className="mt-5 text-lg leading-8 text-slate-500">

            {resource.description}

          </p>

          <div className="mt-6 flex flex-wrap gap-5 text-sm text-slate-400">

            <span>

              {resource.downloads} downloads

            </span>

            {resource.file_size && (

              <span>{resource.file_size}</span>

            )}

            <span>

              {new Date(

                resource.created_at,

              ).toLocaleDateString()}

            </span>

          </div>

          <div className="my-10 h-px bg-slate-200" />

          <h2 className="text-2xl font-black text-[#172033]">

            About this resource

          </h2>

          <div className="mt-5 whitespace-pre-wrap text-[17px] leading-8 text-slate-700">

            {resource.content || resource.description}

          </div>

          {resource.file_url && (

            <a

              href={resource.file_url}

              target="_blank"

              rel="noreferrer"

              className="mt-10 inline-flex rounded-xl bg-[#172033] px-6 py-3 text-sm font-bold text-white hover:bg-blue-600"

            >

              Download resource

            </a>

          )}

        </article>

      </main>

    </div>

  );

}