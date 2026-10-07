import { notFound } from "next/navigation";

import NetworkExperience from "@/components/NetworkExperience";

const pageCount = 100;

export function generateStaticParams() {
  return Array.from({ length: pageCount }, (_, index) => ({
    page: String(index + 1),
  }));
}

export default async function DynamicPage({
  params,
}: {
  params: Promise<{ page: string }>;
}) {
  const { page } = await params;
  const currentPage = Number(page);

  if (
    !Number.isInteger(currentPage) ||
    currentPage < 1 ||
    currentPage > pageCount
  ) {
    notFound();
  }

  return <NetworkExperience currentPage={currentPage} />;
}
