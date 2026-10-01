from app.auth import hash_password
from app.database import SessionLocal

from app.models import Article, Project, Resource, User

def seed_content():

    db = SessionLocal()

    try:

        admin = db.query(User).filter(

            User.username == "apexive"

        ).first()

        if not admin:

            admin = User(
                username="apexive",
                email="admin@apexive.ai",
                password_hash=hash_password("ChangeThisPassword123!"),
                display_name="Apexive",
                bio="Apexive Community administrator.",
                is_active=True,
                is_admin=True,
            )
            db.add(admin)
            db.flush()

        # -------------------------------------------------

        # ARTICLES

        # -------------------------------------------------

        articles = [

            {

                "title": "Building Production AI Agents",

                "slug": "building-production-ai-agents",

                "excerpt": (

                    "A practical architecture for building reliable "

                    "AI agents that can execute real enterprise workflows."

                ),

                "content": """Production AI agents are more than chat interfaces.

A reliable agent system needs an execution layer, tool management,

state management, policies, retries, observability and auditability.

A practical architecture can be divided into several layers:

1. User and application layer

2. Agent orchestration layer

3. Tool execution layer

4. Policy and governance layer

5. Memory and state layer

6. Database and persistence layer

7. Observability and audit layer

The important architectural principle is to treat an AI agent as

an execution system rather than a simple prompt wrapper.

The agent should be able to reason about a task, select tools,

execute actions, recover from failures and maintain an auditable

record of what happened.

For enterprise systems, deterministic controls should remain

around the model. Permissions, financial actions, sensitive data

access and external side effects should pass through explicit

policies.

This architecture provides a foundation for autonomous enterprise

workforce systems that can safely operate across real workflows.""",

                "category": "Artificial Intelligence",

                "read_time_minutes": 8,

                "is_published": True,

                "is_featured": True,

            },

            {

                "title": "How to Design an Enterprise Agent Architecture",

                "slug": "enterprise-agent-architecture",

                "excerpt": (

                    "Understand supervisors, workers, tools, policies, "

                    "memory and execution layers."

                ),

                "content": """Enterprise agent architecture should separate

reasoning from execution.

A supervisor can coordinate multiple specialized workers.

Workers can focus on tasks such as document analysis,

financial reconciliation, research or reporting.

Tools should be isolated behind controlled interfaces.

The execution engine should record:

- tool calls

- inputs

- outputs

- errors

- retries

- approvals

- execution state

A policy engine should determine which actions an agent is

allowed to perform.

This separation makes the system easier to observe, secure,

debug and scale.

The goal is not simply to create an intelligent chatbot.

The goal is to create an execution platform where AI can

participate in structured business workflows.""",

                "category": "AI Architecture",

                "read_time_minutes": 10,

                "is_published": True,

                "is_featured": True,

            },

            {

                "title": "PostgreSQL for Scalable SaaS",

                "slug": "postgresql-for-scalable-saas",

                "excerpt": (

                    "Database architecture patterns for SaaS applications "

                    "that need to scale reliably."

                ),

                "content": """PostgreSQL is a strong foundation for modern SaaS

applications because it combines relational consistency,

powerful indexing, transactions and mature operational tooling.

A scalable application should establish clear ownership
between application services and database models.

Important practices include:

- indexed lookup columns

- foreign key constraints

- transaction boundaries

- migration management

- connection pooling

- pagination

- query monitoring

- backup and recovery procedures

As the application grows, database design becomes part of

the overall architecture rather than an implementation detail.

Good schemas make future features easier to build and maintain.""",

                "category": "Database",

                "read_time_minutes": 7,

                "is_published": True,

                "is_featured": False,

            },

            {

                "title": "Understanding MCP for Modern AI Systems",

                "slug": "understanding-mcp-modern-ai-systems",

                "excerpt": (

                    "How standardized tool interfaces can connect AI "

                    "systems with external capabilities."

                ),

                "content": """Modern AI systems often need access to external

tools, databases, APIs and enterprise systems.

A standardized tool interface can simplify this integration.

The important design principle is to keep tools separate from

the model itself.

The model decides what capability it needs.

The execution layer validates the request and performs the

operation according to application policy.

This separation improves security, observability and

maintainability.

For enterprise agent systems, standardized tool interfaces

can become an important part of the execution architecture.""",

                "category": "Artificial Intelligence",

                "read_time_minutes": 6,

                "is_published": True,

                "is_featured": False,

            },

            {

                "title": "FastAPI Production Architecture",

                "slug": "fastapi-production-architecture",

                "excerpt": (

                    "A clean backend structure for production FastAPI "

                    "applications."

                ),

                "content": """A production FastAPI application benefits from

clear separation between API routes, schemas, models,

authentication, services and persistence.

A practical structure can include:

app/

  api/

  models/

  schemas/

  services/

  auth.py

  config.py

  database.py

  main.py

Routes should remain focused on HTTP concerns.

Business logic should move into services as complexity grows.

Database access should be predictable and transaction-safe.

This architecture makes a backend easier to extend as more

features and teams are added.""",

                "category": "Development",

                "read_time_minutes": 7,

                "is_published": True,

                "is_featured": False,

            },

        ]

        for data in articles:

            existing = db.query(Article).filter(

                Article.slug == data["slug"]

            ).first()

            if not existing:

                db.add(

                    Article(

                        **data,

                        author_id=admin.id,

                    )

                )

        # -------------------------------------------------

        # PROJECTS

        # -------------------------------------------------

        projects = [

            {

                "name": "Apexive AI",

                "slug": "apexive-ai",

                "description": (

                    "Autonomous enterprise AI architecture for "

                    "real business workflows."

                ),

                "content": """Apexive AI is focused on building autonomous

enterprise systems that combine AI agents, structured workflows,

data intelligence, governance and execution.

The long-term goal is to move beyond conversational AI and

build systems that can participate in real enterprise operations.""",

                "category": "Artificial Intelligence",

                "status": "Active",

                "stars": 128,
"is_featured": True,

            },

            {

                "name": "Autonomous Enterprise Workforce",

                "slug": "autonomous-enterprise-workforce",

                "description": (

                    "An execution engine for AI agents that coordinate "

                    "tools, workflows and enterprise operations."

                ),

                "content": """An enterprise agent execution platform designed

around supervisors, workers, tools, policies, memory,

approvals, retries and audit logs.

The system is intended for structured business workflows

rather than simple chatbot interactions.""",

                "category": "AI Infrastructure",

                "status": "Building",

                "stars": 94,

                "is_featured": True,

            },

            {

                "name": "Private Legal AI",

                "slug": "private-legal-ai",

                "description": (

                    "A secure AI workspace designed around private "

                    "enterprise legal knowledge."

                ),

                "content": """Private Legal AI focuses on secure legal

knowledge workflows, document analysis, contract assistance,

precedent discovery and enterprise knowledge retrieval.

The architecture emphasizes private data boundaries,

access control and enterprise governance.""",

                "category": "Legal Technology",

                "status": "Beta",

                "stars": 76,

                "is_featured": True,

            },

            {

                "name": "Construction AI",

                "slug": "construction-ai",

                "description": (

                    "AI-powered workflows for construction companies "

                    "and project teams."

                ),

                "content": """Construction AI explores AI-assisted workflows

for RFIs, project documentation, communication and

construction knowledge management.""",

                "category": "Construction Technology",

                "status": "Building",

                "stars": 61,

                "is_featured": False,

            },

            {

                "name": "Legal Trademark AI",

                "slug": "legal-trademark-ai",

                "description": (

                    "AI-assisted trademark research and document analysis."

                ),

                "content": """Legal Trademark AI is designed to assist with

trademark document analysis, search workflows and structured

legal information processing.""",

                "category": "Legal Technology",

                "status": "Building",

                "stars": 48,

                "is_featured": False,

            },
            *[
                {
                    "name": name,
                    "slug": slug,
                    "description": description,
                    "content": content,
                    "category": "Telecom & Networking",
                    "status": "Building",
                    "stars": 0,
                    "is_featured": False,
                }
                for name, slug, description, content in [
                    ("5G Network Monitoring Dashboard", "5g-network-monitoring-dashboard", "Real-time 5G service, alarm, and KPI visibility for network teams.", "Monitor 5G core and RAN health, alarms, availability, latency, and capacity from one operational dashboard."),
                    ("IMS Monitoring System", "ims-monitoring-system", "Monitor IMS registration, call flows, SIP signaling, and service quality.", "Track IMS nodes, SIP response codes, registration success, call setup, and VoLTE service health."),
                    ("Microwave Link Monitor", "microwave-link-monitor", "Monitor microwave link availability, capacity, RSSI, and alignment indicators.", "Collect link telemetry and raise actionable alarms for fading, interference, and capacity degradation."),
                    ("NOC Automation", "noc-automation", "Automate NOC triage, alarm correlation, escalation, and runbook execution.", "Connect alarms to diagnostic playbooks and approval-controlled remediation workflows."),
                    ("SNMP Network Monitor", "snmp-network-monitor", "SNMP-based monitoring for telecom and IP network infrastructure.", "Discover devices, poll metrics, normalize traps, and expose device health and interface status."),
                    ("Network Topology Visualizer", "network-topology-visualizer", "Interactive topology maps for core, transport, and access networks.", "Visualize device relationships, paths, dependencies, and service impact during incidents."),
                    ("LTE KPI Analyzer", "lte-kpi-analyzer", "Analyze LTE accessibility, retainability, mobility, and utilization KPIs.", "Compare cells and regions, detect KPI degradation, and identify likely radio performance causes."),
                    ("Telecom Power Monitoring", "telecom-power-monitoring", "Monitor rectifiers, batteries, generators, solar systems, and site power.", "Track voltage, current, battery health, fuel, solar contribution, and site power alarms."),
                ]
            ],
        ]

        for data in projects:

            existing = db.query(Project).filter(

                Project.slug == data["slug"]

            ).first()

            if not existing:

                db.add(

                    Project(

                        **data,

                        creator_id=admin.id,

                    )

                )

        # -------------------------------------------------

        # RESOURCES

        # -------------------------------------------------

        resources = [

            {

                "title": "AI Agent Architecture Guide",

                "slug": "ai-agent-architecture-guide",

                "description": (

                    "Architecture patterns for building production-ready "

                    "AI agent systems."

                ),

                "content": """This guide covers the fundamental components

of production AI agent architecture.

Topics include:

- agent orchestration

- tool execution

- policies

- memory

- retries

- approvals

- audit logs

- observability

Use it as a starting point when designing an enterprise

agent execution platform.""",

                "resource_type": "Guide",

                "category": "AI Tools",

                "file_size": "2.4 MB",
"is_featured": True,

                "is_published": True,

            },

            {

                "title": "Production PostgreSQL Checklist",

                "slug": "production-postgresql-checklist",

                "description": (

                    "A practical checklist for deploying and operating "

                    "PostgreSQL applications."

                ),

                "content": """Production PostgreSQL checklist:

Database migrations

Indexes

Foreign keys

Connection management

Backups

Recovery

Monitoring

Query performance

Security

Access control""",

                "resource_type": "Cheat Sheet",

                "category": "Documentation",

                "file_size": "840 KB",

                "is_featured": True,

                "is_published": True,

            },

            {

                "title": "Software Architecture Document",

                "slug": "software-architecture-document",

                "description": (

                    "A reusable architecture document structure "

                    "for software projects."

                ),

                "content": """Software architecture template sections:

1. System Overview

2. Requirements

3. Architecture

4. Components

5. Database

6. APIs

7. Security

8. Deployment

9. Monitoring

10. Future Scaling""",

                "resource_type": "Template",

                "category": "Documentation",

                "file_size": "620 KB",

                "is_featured": True,

                "is_published": True,

            },

            {

                "title": "FastAPI Production Deployment Guide",

                "slug": "fastapi-production-deployment-guide",

                "description": (

                    "Deployment considerations for production FastAPI "

                    "applications."

                ),

                "content": """Production FastAPI deployment should cover

application configuration, process management, reverse proxy,

database connectivity, logging, security and monitoring.""",

                "resource_type": "Guide",

                "category": "Developer Tools",

                "file_size": "1.8 MB",

                "is_featured": False,

                "is_published": True,

            },

            {

                "title": "Enterprise AI Security Checklist",

                "slug": "enterprise-ai-security-checklist",

                "description": (

                    "A security checklist for enterprise AI systems."

                ),

                "content": """Enterprise AI security areas:

Authentication

Authorization

Data isolation

Secrets management

Tool permissions

Audit logging

Prompt injection defense

Sensitive data handling

Model access control

Incident response""",

                "resource_type": "Cheat Sheet",

                "category": "Security Tools",

                "file_size": "910 KB",

                "is_featured": False,

                "is_published": True,

            },

        ]

        for data in resources:

            existing = db.query(Resource).filter(

                Resource.slug == data["slug"]

            ).first()

            if not existing:

                db.add(

                    Resource(

                        **data,

                        author_id=admin.id,

                    )

                )

        db.commit()

        print("Apexive Community content seed completed.")

    finally:

        db.close()

if __name__ == "__main__":

    seed_content()