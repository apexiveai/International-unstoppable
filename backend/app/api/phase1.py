from fastapi import APIRouter

router = APIRouter(prefix="/api/phase-1", tags=["Phase 1"])

PHASE_ONE_CAPABILITIES = [
    {"id": 1, "name": "Legal Knowledge Agent", "description": "Search and summarize approved legal knowledge sources."},
    {"id": 2, "name": "RFP Analysis & Costing", "description": "Extract requirements and prepare a costing workspace."},
    {"id": 3, "name": "Similar Transaction Search", "description": "Find comparable transactions from indexed matter data."},
    {"id": 4, "name": "RFI Generator", "description": "Generate a structured request for information from a matter brief."},
    {"id": 5, "name": "RFI Approval & Sending", "description": "Route RFIs through approval before delivery."},
    {"id": 6, "name": "Contract Drafting Agent", "description": "Draft contracts from approved templates and instructions."},
    {"id": 7, "name": "Precedent Retrieval", "description": "Retrieve relevant clauses and previously approved precedents."},
    {"id": 8, "name": "Country / Jurisdiction Detection", "description": "Detect governing countries and jurisdictions from documents."},
    {"id": 9, "name": "Party Extraction", "description": "Extract parties, roles, and entity details from documents."},
    {"id": 10, "name": "Agreement Classification", "description": "Classify agreements by type and workflow."},
    {"id": 11, "name": "Template Selection", "description": "Recommend templates based on matter context."},
    {"id": 12, "name": "Document Comparison", "description": "Compare document versions and highlight changes."},
    {"id": 13, "name": "SharePoint Integration", "description": "Connect approved document sources in SharePoint."},
    {"id": 14, "name": "Microsoft Teams Integration", "description": "Surface matter workflows and notifications in Teams."},
    {"id": 15, "name": "Human Approval Workflow", "description": "Require accountable human review for governed actions."},
    {"id": 16, "name": "Audit Log", "description": "Record requests, decisions, tool calls, and document events."},
    {"id": 17, "name": "Access Control", "description": "Enforce role-based access to workspaces and actions."},
    {"id": 18, "name": "Document Permissions", "description": "Apply document-level permissions and sharing controls."},
]


@router.get("")
def list_phase_one_capabilities():
    return {
        "phase": "Phase 1",
        "count": len(PHASE_ONE_CAPABILITIES),
        "capabilities": PHASE_ONE_CAPABILITIES,
    }
