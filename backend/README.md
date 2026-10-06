psql -U naing -h localhost -p 5432 -d apexive_community

\dt

SELECT id, username, email, is_active, is_admin
FROM users;

"# Backend

## Client billing and product access

Admin endpoints use the existing JWT bearer token and the `users.is_admin` flag.
Client management is available under `/api/admin/clients`; payment review,
subscription transitions, and the audit feed are available under `/api/admin`.

The normal billing flow is:

1. An authenticated client creates a pending payment with
   `POST /api/payments/create` (`plan_id` and `payment_method`).
2. An administrator verifies or rejects it under
   `/api/admin/payments/{payment_id}`.
3. Only a verified payment can be used to activate its linked subscription
   through `/api/admin/subscriptions/{subscription_id}/activate`.
4. The client checks access with
   `GET /api/subscriptions/access/{product_key}`. Access requires an active,
   unexpired subscription and a verified payment.
5. Payment and subscription changes are recorded in
   `tenant_audit_logs`; administrators can view them at
   `GET /api/admin/audit-logs`.

Run the Alembic migration before deploying the API:

```powershell
cd backend
alembic upgrade head
python app/seed_subscription_plans.py
```

The current seed script publishes the already-priced Trademark and Workforce
plans. MAX-MYANMAR and MNA are recognized product keys but remain unpublished
until their prices are confirmed and added to `app/seed_subscription_plans.py`.

## Fresh PostgreSQL database

For a new, empty PostgreSQL database, the complete schema can be bootstrapped
from the SQL file instead of applying the migrations:

```powershell
createdb apexive_community
psql -d apexive_community -v ON_ERROR_STOP=1 -f .\database.sql
```

`database.sql` creates all current ORM tables and indexes, seeds the forum
category tree and currently priced subscription plans, and records the current
Alembic head. It does not create an administrator account or credentials.
If the database has already been created by your hosting provider, skip
`createdb` and run only the `psql` command. Run the SQL file once against an
empty database. For an existing database, continue to use
`alembic upgrade head` and the seed scripts above.
