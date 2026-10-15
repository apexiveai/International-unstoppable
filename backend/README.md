YOUR_OPENAI_API_KEY_HERE

psql -U naing -h localhost -p 5432 -d apexive_community

\dt

SELECT id, username, email, is_active, is_admin
FROM users;

"# Backend

## Client billing and product access

Platform-wide administration requires an authenticated user with both
`users.is_admin` and `users.is_super_admin` set. A normal administrator is not
implicitly promoted. Any administrator can review and approve pending customer
accounts across tenants; approval records the acting administrator and tenant
in the audit trail. Customer identity and tenant scope come from the
authenticated server-side user record, not request-supplied tenant or role IDs.

The normal billing flow is:

1. An authenticated client creates a pending payment with
   `POST /api/payments/create` (`plan_id` and `payment_method`). Bank and mobile
   wallet payments can be reviewed manually, including payments made outside
   the application.
2. An administrator verifies or rejects it under
   `/api/admin/payments/{payment_id}`.
3. Only a verified payment can be used to activate its linked subscription
   through `/api/admin/subscriptions/{subscription_id}/activate`.
4. An Admin can submit a manual subscription request with
   `POST /api/admin/subscriptions`; it remains pending until a Super Admin
   approves it through
   `POST /api/admin/subscriptions/{subscription_id}/approve-manual`. Requests
   require a reason and do not bypass verified payment for Trademark Conflict.
   Admins can extend eligible subscriptions and cancel them with a recorded
   reason. Support accounts have read-only subscription access. Customers can
   submit payment requests and view subscriptions but cannot administer them.
5. The client checks access with
   `GET /api/subscriptions/access/{product_key}`. Paid access requires a
   matching active subscription, valid dates, and a verified payment scoped to
   that subscription and tenant. A manual Admin subscription is instead
   authorized by its recorded Admin approval reason.
6. A Super Admin can issue time-bounded trial or complimentary grants through
   `POST /api/admin/product-grants`, list them through
   `GET /api/admin/product-grants`, and revoke them through
   `POST /api/admin/product-grants/{grant_id}/revoke`. Grants are tenant- and
   product-scoped and recorded in the system audit trail.
7. An entitled client requests a one-time product handoff at
   `POST /api/subscriptions/products/{product_key}/launch`. The plaintext code
   is returned only for that issuance; exchange it at
   `POST /api/subscriptions/launch/exchange`. Codes are hashed at rest,
   conditionally consumed once, and expire after
   `PRODUCT_LAUNCH_CODE_TTL_SECONDS` (default 180 seconds; allowed range
   30–900). Super Admins can list code metadata or revoke unused codes through
   `/api/admin/product-launch-codes`.
8. Tenant-scoped subscription/payment changes are available in
   `tenant_audit_logs` at `GET /api/admin/audit-logs`. Privileged operations,
   grant lifecycle changes, code lifecycle changes, and bootstrap actions are
   recorded in `system_audit_events`, exposed at
   `GET /api/admin/system-audit-logs`.

The subscription administration page provides tenant/plan/status filters,
active, revenue, pending-request, and expiring-soon summary cards, a six-month
verified-payment revenue dashboard by currency, an expiring-subscription list,
details and audit history, bounded bulk extension/cancellation, and CSV/XLSX
exports. Configure `EMAIL_ENABLED=true` and valid `SMTP_*` settings to enable
subscription expiry emails. Administrators can send due 7-day and 3-day
reminders from the subscription dashboard; the action skips reminders already
sent. For automatic delivery, schedule `python send_subscription_reminders.py`
to run daily from the `backend` directory. The job records in-app notifications
before attempting email delivery. Delivery failures are logged and included in
the command summary.

The Detector API checks entitlement before parsing uploads. The separate
Detector service verifies the bearer token and tenant against this API, scopes
jobs/results to the authenticated tenant, and rechecks authorization for queued
processing. Deploy it with a reachable HTTPS central API URL and configure
request-body limits at the reverse proxy as well as the application; requests
without a trustworthy `Content-Length` still require an ingress-level cap.

Trademark Conflict also offers a domain availability lookup backed by the
Spaceship API. Set `SPACESHIP_API_KEY` and `SPACESHIP_API_SECRET` in the backend
environment (and optionally `SPACESHIP_API_BASE_URL`, defaulting to
`https://spaceship.dev/api/v1`). Only authenticated tenants with active
Trademark Conflict access can use `POST /api/clone-detector/domains/availability`.
This lookup reports availability only; it does not register or purchase domains
and is not a trademark clearance or legal determination.

Run the Alembic migration before deploying the API:

```powershell
cd backend
alembic upgrade head
python app/seed_subscription_plans.py
```

Create an initial ordinary administrator only when explicitly approved by
setting `BOOTSTRAP_ADMIN_USERNAME`, `BOOTSTRAP_ADMIN_EMAIL`,
`BOOTSTRAP_ADMIN_DISPLAY_NAME`, and `BOOTSTRAP_ADMIN_PASSWORD` in a secure
secret mechanism, then run `python seed_admin.py`. The password must be at
least 16 characters. This command never creates or promotes a Super Admin.
For local setup, put these values in `backend/.env` (not `.env.example`); the
seed command loads that file automatically. After applying migrations, run
`.\.venv\Scripts\python.exe seed_admin.py` from `backend`. Bootstrap values
should be removed from the deployment environment or local `.env` after use.
For safety, the bootstrap command only writes to the known application
databases `apexive_community`, `apexive_community_app`, or
`apexive_admin_eisn`. It creates an ordinary administrator, never a Super
Admin, and updates an existing ordinary bootstrap account in place rather
than deleting an account that may have related records. On Render, run the
command from a one-off job or service shell connected to the production
database after setting the four bootstrap variables in the Render environment.
Remove all four bootstrap variables after the command succeeds. Sign in with
the configured email (case-insensitive) or username.
For the first Super Admin, have an authorized database operator promote an
existing, active administrator in a reviewed transaction and record the
approval reference in `system_audit_events`; do not promote a named account by
automatic migration or seed behavior. Only run the following after reviewing
the target account, backup, and approval reference. Replace the two quoted
placeholders before execution. A missing/non-admin/inactive target promotes no
account and inserts no audit event. The audit actor is left null to avoid
misrepresenting the database operator as an application user.

```sql
BEGIN;
WITH candidate AS (
    SELECT id
    FROM users
    WHERE username = 'REPLACE_WITH_APPROVED_USERNAME'
      AND is_admin IS TRUE
      AND is_active IS TRUE
    FOR UPDATE
),
promoted AS (
    UPDATE users AS target
    SET is_super_admin = TRUE
    FROM candidate
    WHERE target.id = candidate.id
      AND target.is_super_admin IS FALSE
    RETURNING target.id
),
audit AS (
    INSERT INTO system_audit_events
        (actor_user_id, action, target_type, target_id, outcome, details)
    SELECT
        NULL,
        'super_admin.bootstrap',
        'user',
        promoted.id::text,
        'success',
        jsonb_build_object(
            'operator', 'REPLACE_WITH_OPERATOR_IDENTITY',
            'approval_reference', 'REPLACE_WITH_APPROVAL_REFERENCE'
        )::text
    FROM promoted
    RETURNING id
)
SELECT id AS promoted_user_id FROM promoted;
COMMIT;
```

The current seed script publishes the already-priced Trademark and Workforce
plans. MAX-MYANMAR and MNA are recognized product keys but remain unpublished
until their prices are confirmed and added to `app/seed_subscription_plans.py`.

## Fresh PostgreSQL database

Keep any legacy database in place. For a fresh local community database, create
`apexive_community_app` using an authorized PostgreSQL role, then point the
backend `DATABASE_URL` in `backend/.env` at that database. For example, an
authorized operator can run:

```powershell
createdb apexive_community_app
psql -d apexive_community_app -v ON_ERROR_STOP=1 -f .\database.sql
```

`database.sql` bootstraps the schema at its recorded Alembic revision, seeds
the forum category tree and currently priced subscription plans, and does not
create an administrator account or credentials. After running it against an
empty database, run `alembic upgrade head` to apply any later migrations before
starting the application.
If the application database role cannot create databases, have an authorized
PostgreSQL operator create the empty database and grant ownership to the
application role before running `psql`. Run the SQL file once against an empty
database. For an existing application database, continue to use
`alembic upgrade head` and the seed scripts above; do not initialize a legacy
database by running this file against it.

## Billing and deployment limits

Merchant-specific checkout and signed webhook verification are not implemented
or verified for CB Pay, KBZPay, or AYA Pay. Until the official provider
contracts, sandbox credentials, callback-signature rules, and production
approval are available, payment verification is an explicit administrative
operation; a browser redirect or client assertion is never proof of payment.
Do not enable live paid billing based on this implementation alone.

Run migrations only against the intended database after taking a recoverable
backup. The repository's deployment startup may apply `alembic upgrade head`;
confirm the deployment database and migration window with the operator first.
Local unit tests and offline Alembic SQL generation do not substitute for a
staging migration or production verification.
