import Link from "next/link";

import SiteHeader from "@/components/SiteHeader";

import { getArticle } from "@/lib/api";

type Props = {

  params: Promise<{

    slug: string;

  }>;

};

export default async function ArticleDetailPage({

  params,

}: Props) {

  const { slug } = await params;

  let article;

  try {

    article = await getArticle(slug);

  } catch {

    return (

      <div className="min-h-screen bg-white">

        <SiteHeader />

        <main className="mx-auto max-w-4xl px-6 py-24 text-center">

          <h1 className="text-3xl font-black text-[#172033]">

            Article not found

          </h1>

          <Link

            href="/articles"

            className="mt-6 inline-block font-bold text-blue-600"

          >

            ← Back to articles

          </Link>

        </main>

      </div>

    );

  }

  return (

    <div className="min-h-screen bg-white text-slate-900">

      <SiteHeader />

      <main className="mx-auto max-w-4xl px-6 py-12">

        <Link

          href="/articles"

          className="text-sm font-bold text-blue-600"

        >

          ← Back to articles

        </Link>

        <article className="mt-10">

          <div className="text-xs font-black uppercase tracking-[0.16em] text-blue-600">

            {article.category}

          </div>

          <h1 className="mt-4 text-4xl font-black tracking-tight text-[#172033] sm:text-5xl">

            {article.title}

          </h1>

          <p className="mt-5 text-lg leading-8 text-slate-500">

            {article.excerpt}

          </p>

          <div className="mt-6 flex flex-wrap gap-4 text-sm text-slate-400">

            <span>

              {article.read_time_minutes} min read

            </span>

            <span>{article.views} views</span>

            <span>

              {new Date(

                article.created_at,

              ).toLocaleDateString()}

            </span>

          </div>

          <div className="my-10 h-px bg-slate-200" />

          <div className="whitespace-pre-wrap text-[17px] leading-8 text-slate-700">

            {article.content}

          </div>

        </article>

      </main>

    </div>

  );

}