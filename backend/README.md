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
until their prices are confirmed and added to `app/seed_subscription_plans.py`."
