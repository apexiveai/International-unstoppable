import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";

const capabilities = [

  ["01", "Legal Knowledge Agent", "Search and summarize approved legal knowledge sources."],

  ["02", "RFP Analysis & Costing", "Extract requirements and prepare a costing workspace."],

  ["03", "Similar Transaction Search", "Find comparable transactions from indexed matter data."],

  ["04", "RFI Generator", "Generate a structured request for information from a matter brief."],

  ["05", "RFI Approval & Sending", "Route RFIs through approval before delivery."],

  ["06", "Contract Drafting Agent", "Draft contracts from approved templates and instructions."],

  ["07", "Precedent Retrieval", "Retrieve relevant clauses and previously approved precedents."],

  ["08", "Country / Jurisdiction Detection", "Detect governing countries and jurisdictions from documents."],

  ["09", "Party Extraction", "Extract parties, roles, and entity details from documents."],

  ["10", "Agreement Classification", "Classify agreements by type and workflow."],

  ["11", "Template Selection", "Recommend templates based on matter context."],

  ["12", "Document Comparison", "Compare document versions and highlight changes."],

  ["13", "SharePoint Integration", "Connect approved document sources in SharePoint."],

  ["14", "Microsoft Teams Integration", "Surface matter workflows and notifications in Teams."],

  ["15", "Human Approval Workflow", "Require accountable human review for governed actions."],

  ["16", "Audit Log", "Record requests, decisions, tool calls, and document events."],

  ["17", "Access Control", "Enforce role-based access to workspaces and actions."],

  ["18", "Document Permissions", "Apply document-level permissions and sharing controls."],

] as const;

export default function PhaseOnePage() {

  return (

    <div className="min-h-screen bg-slate-50">

      <SiteHeader />

      <main className="mx-auto max-w-7xl px-6 py-16 lg:px-8">

        <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-600">

          Enterprise legal operations

        </p>

        <h1 className="mt-3 text-4xl font-black tracking-tight text-[#172033]">

          Phase 1 capabilities

        </h1>

        <p className="mt-4 max-w-3xl text-slate-600">

          A single capability map for the first delivery phase. Each item is

          ready to be connected to a governed workflow, data source, and

          approval policy.

        </p>

        {/* Telecom Power Monitoring */}

        <section className="mt-12">

          <div className="mb-5">

            <p className="text-xs font-black uppercase tracking-[0.18em] text-amber-600">

              Network Infrastructure

            </p>

            <h2 className="mt-2 text-2xl font-black text-[#172033]">

              Projects

            </h2>

          </div>
<Link

  href="https://www.apexiveai.com/telecom-power-monitoring"

  className="group block w-full rounded-2xl border border-slate-200 bg-white p-7 text-left shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-blue-300 hover:shadow-xl"

>

  <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">

    <div className="flex items-start gap-5">

      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-2xl">

        ⚡

      </div>

      <div>

        <div className="flex flex-wrap items-center gap-3">

          <h3 className="text-xl font-black text-[#172033]">

            Telecom Power Monitoring

          </h3>

          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">

            Active

          </span>

        </div>

        <p className="mt-2 text-sm font-semibold text-slate-500">

          Network Design & Quotation

        </p>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">

          Cisco network design, VLAN / SSID planning, IP planning,

          ACL policies, Cisco configuration generation, product

          catalog management and professional quotations.

        </p>

        <div className="mt-4 flex flex-wrap gap-2">

          {[

            "Cisco",

            "VLAN / SSID",

            "IP Planner",

            "ACL",

            "Quotation",

          ].map((item) => (

            <span

              key={item}

              className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-600"

            >

              {item}

            </span>

          ))}

        </div>

      </div>

    </div>

    <div className="flex shrink-0 items-center gap-2 text-sm font-black text-blue-600 transition-transform group-hover:translate-x-1">

      Open Project

      <span className="text-lg">→</span>

    </div>

  </div>

</Link>

        </section>

        {/* Existing Phase 1 capabilities */}

        <section className="mt-14">

          <div className="mb-6">

            <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-600">

              Enterprise legal operations

            </p>

            <h2 className="mt-2 text-2xl font-black text-[#172033]">

              Phase 1 capabilities

            </h2>

          </div>

          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">

            {capabilities.map(([number, name, description]) => (

              <article

                key={number}

                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"

              >

                <div className="flex items-center justify-between">

                  <span className="text-sm font-black text-blue-600">

                    {number}

                  </span>

                  <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-amber-700">

                    Foundation

                  </span>

                </div>

                <h2 className="mt-5 text-lg font-black text-[#172033]">

                  {name}

                </h2>

                <p className="mt-3 text-sm leading-6 text-slate-500">

                  {description}

                </p>

              </article>

            ))}

          </div>

        </section>

      </main>

    </div>

  );

}