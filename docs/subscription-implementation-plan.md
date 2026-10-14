# Subscription and Product Entitlement Implementation Plan

## Current architecture and constraints

- The central application is a FastAPI service using SQLAlchemy 2, PostgreSQL in deployment, Alembic migrations, and a Next.js frontend. The backend has an existing `users.tenant_id` tenant model, JWT bearer authentication, payment/subscription tables, and an audit-log table.
- The central API already contains uncommitted work for Super Admin grants, launch-code handoff, subscription access checks, and frontend administration. These changes are in the worktree and are being preserved and completed, not replaced.
- The central Alembic history has one current head (`c7d8e9f0a1b2`) descending from the existing merged subscription/project history. No second migration history is needed.
- A sibling `apexiveai-trademark-conflict-detector` repository is present and has independent uncommitted changes. Its FastAPI service stores jobs and files in local SQLite/filesystem storage, supports asynchronous processing, and already contains uncommitted integration with the central entitlement API. Both worktrees must be preserved.
- The existing payment adapters do not contain verified merchant-specific checkout or webhook signature implementations. No provider contract or production credential is assumed; paid access must remain limited to centrally verified/admin-reviewed payments until integration is approved.
- Existing product visibility publishes only Trademark and Workforce plans. MAX-MYANMAR and MNA remain catalog products but are not made purchasable or grantable by this work without explicit publication/pricing approval.

## Implementation sequence

1. Preserve and harden the in-progress role, grant, subscription, and launch-code migration. Remove automatic Super Admin promotion; Super Admin bootstrap must be an explicit, verified operator action.
2. Centralize product entitlement evaluation using trusted tenant identity, active subscription/payment state, grant start/expiry/revocation, and product publication rules.
3. Enforce tenant and product authorization on the central Detector API before parsing/processing uploads; retain the existing file signature/size validation, job ownership checks, and result scoping in the sibling Detector service.
4. Make launch-code exchange one-time under concurrent requests using a conditional database update, keep codes hash-only, configure the short handoff lifetime, and audit successful lifecycle changes without recording plaintext secrets.
5. Apply Super Admin guards to platform-wide plan/product/grant controls, retain tenant scoping for customer data, and record privileged subscription/payment/entitlement changes.
6. Keep frontend screens informational and action-oriented; all privileged and entitlement decisions continue to be enforced by the backend.
7. Add focused service/API tests, run the available backend and frontend checks, and inspect both worktrees' final diffs.
8. Replace credential-shaped values in tracked environment examples with placeholders, document exact setup/migration/deployment commands, and identify provider and cross-service configuration requirements.

## Risks and verification boundaries

- Do not run schema migrations against a configured database until its target is confirmed as a disposable/local or explicitly approved deployment database. Validate migrations offline and on an isolated test database instead.
- The Detector service depends on a live central API round-trip for each protected request. Deployment needs a reachable HTTPS central API URL and network/TLS configuration; authorization failures and upstream outages must fail closed.
- Detector jobs can outlive the authorization check that admitted an upload. Rechecking before deferred execution requires a safely retained user credential or a separately provisioned service credential; credentials must not be persisted in job state or logs. If that cannot be proven safe with the available configuration, queued work must fail closed and the production dependency must be documented.
- Payment provider integration remains blocked on official merchant API/signature specifications, credentials, sandbox access, and approval. A success redirect or client request is never payment evidence.
- No Redis/distributed rate-limit service is currently configured. In-process limits are not a production-wide brute-force control; launch-code entropy, atomic one-use consumption, short expiry, and upstream edge-rate limits must be configured and verified before production.
- An external production database, provider account, deployment platform, and production permissions are not available for this task. Production migrations, credentials, DNS, HTTPS, and live payment transactions require operator approval and verification.

## Validation approach

- Use the existing Python `unittest` tests and add focused backend tests for tenant-aware access decisions, unauthenticated/unauthorized detector requests, code replay/races, and payment/grant denial cases.
- Run Alembic revision graph and offline SQL checks without changing a production database.
- Run the sibling Detector security tests and the central backend tests with isolated test data.
- Run frontend lint, TypeScript/build validation where available.
- Report passed, failed, skipped, and externally blocked checks separately; do not equate a local mock or static test with production integration verification.
