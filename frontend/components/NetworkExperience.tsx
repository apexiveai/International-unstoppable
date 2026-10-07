import Link from "next/link";

import { siteNavigationGroups } from "@/lib/site-navigation";

const pageCount = 100;

const networkLayers = [
  {
    number: "01",
    eyebrow: "CONNECTED SYSTEMS",
    title: "One view across your entire operation.",
    description:
      "Bring your tools, teams, and information together in a network that works as one.",
    color: "cyan",
  },
  {
    number: "02",
    eyebrow: "INTELLIGENT DATA",
    title: "Turn scattered data into clear signals.",
    description:
      "Trace the path from raw information to the decisions that move your business forward.",
    color: "blue",
  },
  {
    number: "03",
    eyebrow: "SEAMLESS AUTOMATION",
    title: "Keep every workflow in motion.",
    description:
      "Connect the right processes and let dependable automation handle the handoffs.",
    color: "amber",
  },
];

function getVisiblePages(currentPage: number) {
  const start = Math.max(2, currentPage - 1);
  const end = Math.min(pageCount - 1, currentPage + 1);
  const pages: Array<number | "ellipsis"> = [1];

  if (start > 2) {
    pages.push("ellipsis");
  }

  for (let page = start; page <= end; page += 1) {
    pages.push(page);
  }

  if (end < pageCount - 1) {
    pages.push("ellipsis");
  }

  pages.push(pageCount);
  return pages;
}

function PagePagination({ currentPage }: { currentPage: number }) {
  const visiblePages = getVisiblePages(currentPage);
  const previousPage = currentPage - 1;
  const nextPage = currentPage + 1;

  return (
    <nav className="pagination-wrap" aria-label="Network pages">
      <span className="pagination-caption">
        PAGE <strong>{currentPage}</strong> OF {pageCount}
      </span>
      <ul className="pagination-list">
        <li>
          {previousPage < 1 ? (
            <span className="pagination-control disabled" aria-disabled="true">
              Previous
            </span>
          ) : (
            <Link
              className="pagination-control"
              href={`/page/${previousPage}`}
              rel="prev"
            >
              Previous
            </Link>
          )}
        </li>
        {visiblePages.map((page, index) => (
          <li key={`${page}-${index}`}>
            {page === "ellipsis" ? (
              <span className="pagination-ellipsis" aria-hidden="true">
                …
              </span>
            ) : (
              <Link
                aria-label={`Page ${page}`}
                aria-current={page === currentPage ? "page" : undefined}
                className={`pagination-page${page === currentPage ? " active" : ""}`}
                href={`/page/${page}`}
              >
                {page}
              </Link>
            )}
          </li>
        ))}
        <li>
          {nextPage > pageCount ? (
            <span className="pagination-control disabled" aria-disabled="true">
              Next
            </span>
          ) : (
            <Link
              className="pagination-control"
              href={`/page/${nextPage}`}
              rel="next"
            >
              Next
            </Link>
          )}
        </li>
      </ul>
    </nav>
  );
}

export default function NetworkExperience({
  currentPage,
}: {
  currentPage: number;
}) {
  return (
    <main className="network-experience">
      <header className="network-header">
        <Link className="brand" href="/" aria-label="Apexive home">
          <span className="brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span className="brand-name">APEXIVE</span>
          <span className="brand-divider" />
          <span className="brand-subtitle">INTELLIGENCE NETWORK</span>
        </Link>
        <nav className="top-nav" aria-label="Main navigation">
          <a href="#network">Network</a>
          <a href="#layers">Capabilities</a>
          <details className="network-more-menu">
            <summary>
              More <span aria-hidden="true">⌄</span>
            </summary>
            <div className="network-more-panel">
              {siteNavigationGroups.map((group) => (
                <section key={group.label}>
                  <h2>{group.label}</h2>
                  {group.links.map((link) => (
                    <Link href={link.href} key={link.href}>
                      {link.label}
                    </Link>
                  ))}
                </section>
              ))}
            </div>
          </details>
          <a className="nav-cta" href="#pages">
            Explore pages <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </header>

      <section className="network-hero" id="network">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="status-dot" />
            CONNECTED INTELLIGENCE / PAGE {currentPage} OF {pageCount}
          </p>
          <h1>
            Everything connected.
            <br />
            <span>Nothing standing still.</span>
          </h1>
          <p className="hero-description">
            A clearer picture of your digital world. Connect data, systems, and
            decisions through one intelligent network built to move your
            business forward.
          </p>
          <div className="hero-actions">
            <a className="button-primary" href="#layers">
              Explore the network <span aria-hidden="true">↗</span>
            </a>
            <a className="button-text" href="#pages">
              Browse all 100 pages <span aria-hidden="true">↓</span>
            </a>
          </div>
          <div className="hero-metrics" aria-label="Network overview">
            <div>
              <strong>100</strong>
              <span>NETWORK PAGES</span>
            </div>
            <div>
              <strong>01</strong>
              <span>CONNECTED VIEW</span>
            </div>
            <div>
              <strong>∞</strong>
              <span>POSSIBILITIES</span>
            </div>
          </div>
        </div>

        <div
          className="network-visual"
          role="img"
          aria-label="An abstract network of connected data systems"
        >
          <div className="visual-label visual-label-top">
            <span className="status-dot" />
            LIVE SYSTEM MAP
          </div>
          <div className="visual-label visual-label-bottom">
            <span>DATA FLOW</span>
            <span className="flow-line" />
            <span>ACTIVE</span>
          </div>
          <span className="visual-coordinate">40° 43&apos; 55.3&quot; N</span>
        </div>
      </section>

      <section className="layers-section" id="layers">
        <div className="section-heading">
          <div>
            <p className="eyebrow">A NETWORK THAT WORKS FOR YOU</p>
            <h2>Built to bring everything together.</h2>
          </div>
          <p className="section-intro">
            From the first connection to the final decision, every part of your
            operation has a place in the bigger picture.
          </p>
        </div>

        <div className="layers-grid">
          {networkLayers.map((layer) => (
            <article
              className={`layer-card layer-${layer.color}`}
              key={layer.number}
            >
              <div className="layer-card-top">
                <span className="layer-number">{layer.number}</span>
                <span className="layer-orbit" aria-hidden="true">
                  <span />
                </span>
              </div>
              <p className="layer-eyebrow">{layer.eyebrow}</p>
              <h3>{layer.title}</h3>
              <p className="layer-description">{layer.description}</p>
              <span className="layer-link" aria-hidden="true">
                ↗
              </span>
            </article>
          ))}
        </div>
      </section>

      <section className="pagination-section" id="pages">
        <div className="pagination-heading">
          <div>
            <p className="eyebrow">NETWORK INDEX</p>
            <h2>Explore the full network.</h2>
          </div>
          <span className="index-total">001 — 100</span>
        </div>
        <PagePagination currentPage={currentPage} />
      </section>

      <footer className="network-footer">
        <div className="footer-directory">
          <div className="footer-directory-brand">
            <Link className="footer-brand" href="/">
              APEXIVE <span>INTELLIGENCE NETWORK</span>
            </Link>
            <span>CONNECTED BY DESIGN. BUILT FOR WHAT&apos;S NEXT.</span>
          </div>
          {siteNavigationGroups.map((group) => (
            <section className="footer-link-group" key={group.label}>
              <h2>{group.label}</h2>
              {group.links.map((link) => (
                <Link href={link.href} key={link.href}>
                  {link.label}
                </Link>
              ))}
            </section>
          ))}
        </div>
      </footer>
    </main>
  );
}
