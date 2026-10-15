type PaginationProps = {
  page: number;
  pages: number;
  total: number;
  onPageChange: (page: number) => void;
};

function visiblePages(currentPage: number, pages: number) {
  const start = Math.max(1, Math.min(currentPage - 2, pages - 4));
  const end = Math.min(pages, start + 4);
  return Array.from({ length: end - start + 1 }, (_, index) => start + index);
}

export default function Pagination({
  page,
  pages,
  total,
  onPageChange,
}: PaginationProps) {
  if (total === 0 || pages <= 1) return null;
  const pageNumbers = visiblePages(page, pages);
  const controlClass =
    "inline-flex min-w-10 items-center justify-center border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-400 disabled:hover:bg-white";

  return (
    <nav
      aria-label="Pagination"
      className="mt-8 flex flex-col items-center justify-between gap-4 sm:flex-row"
    >
      <p className="text-sm text-slate-500">
        Page {page} of {pages} · {total} results
      </p>
      <ul className="flex items-center">
        <li>
          <button
            type="button"
            className={`${controlClass} rounded-l-md`}
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
          >
            Previous
          </button>
        </li>
        {pageNumbers[0] > 1 && (
          <>
            <li>
              <button
                type="button"
                className={controlClass}
                onClick={() => onPageChange(1)}
              >
                1
              </button>
            </li>
            {pageNumbers[0] > 2 && (
              <li aria-hidden="true" className={`${controlClass} cursor-default`}>
                …
              </li>
            )}
          </>
        )}
        {pageNumbers.map((number) => (
          <li key={number}>
            <button
              type="button"
              aria-current={page === number ? "page" : undefined}
              className={`${controlClass} ${
                page === number ? "border-blue-600 bg-blue-600 text-white hover:bg-blue-700" : ""
              }`}
              onClick={() => onPageChange(number)}
            >
              {number}
            </button>
          </li>
        ))}
        {pageNumbers[pageNumbers.length - 1] < pages && (
          <>
            {pageNumbers[pageNumbers.length - 1] < pages - 1 && (
              <li aria-hidden="true" className={`${controlClass} cursor-default`}>
                …
              </li>
            )}
            <li>
              <button
                type="button"
                className={controlClass}
                onClick={() => onPageChange(pages)}
              >
                {pages}
              </button>
            </li>
          </>
        )}
        <li>
          <button
            type="button"
            className={`${controlClass} rounded-r-md`}
            onClick={() => onPageChange(page + 1)}
            disabled={page === pages}
          >
            Next
          </button>
        </li>
      </ul>
    </nav>
  );
}
